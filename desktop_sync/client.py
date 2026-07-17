"""
Desktop synchronization client for GestionCours.

Reads the local SQLite database, queues pending changes when offline,
and pushes them to the FastAPI backend via POST /sync.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import urllib.error
import urllib.request

logger = logging.getLogger("desktop_sync")

# Maps desktop créneau labels to start/end times
CRENEAU_TIMES = {
    "Matin": ("07:00:00", "12:00:00"),
    "Après-midi": ("13:00:00", "18:00:00"),
}


@dataclass
class SyncConfig:
    api_base_url: str = "http://127.0.0.1:8000"
    api_key: str = "desktop-admin-sync-key-change-me"
    sqlite_path: str = ""
    queue_path: str = ""
    timeout_seconds: int = 30
    poll_interval_seconds: int = 60


@dataclass
class SyncStatus:
    state: str = "idle"  # idle | syncing | offline | error | ok
    last_sync_at: Optional[str] = None
    last_message: str = ""
    pending_count: int = 0
    conflicts: list[dict] = field(default_factory=list)


class SyncClient:
    """
    Synchronization client used by the Tkinter desktop app.

    - `sync_now()` pushes the full local timetable (or queued deltas).
    - `queue_change()` stores a change when offline.
    - A background thread retries pending changes when connectivity returns.
    """

    def __init__(self, config: SyncConfig, on_status: Optional[Callable[[SyncStatus], None]] = None):
        self.config = config
        self.on_status = on_status
        self.status = SyncStatus()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        if not self.config.sqlite_path:
            raise ValueError("sqlite_path is required")
        if not self.config.queue_path:
            base = Path(self.config.sqlite_path).parent
            self.config.queue_path = str(base / "sync_queue.json")

        self._ensure_queue_file()

    # ------------------------------------------------------------------ public

    def start_background(self) -> None:
        """Start the offline-retry background worker."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._background_loop, daemon=True, name="SyncWorker")
        self._thread.start()

    def stop_background(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def sync_now(self, full: bool = True) -> SyncStatus:
        """Trigger an immediate sync (full dump of local SQLite by default)."""
        with self._lock:
            self._set_status("syncing", "Synchronisation en cours…")
            try:
                if full:
                    payload = self.build_full_payload()
                else:
                    payload = self._drain_queue_payload()
                    if not payload:
                        self._set_status("ok", "Rien à synchroniser")
                        return self.status

                result = self._post_json("/sync", payload)
                # Clear queue on success
                self._write_queue([])
                conflicts = result.get("conflicts") or []
                msg = result.get("message") or "Synchronisation réussie"
                self.status.conflicts = conflicts
                self.status.last_sync_at = datetime.now().isoformat(timespec="seconds")
                if conflicts:
                    self._set_status("ok", f"{msg} ({len(conflicts)} conflit(s))")
                else:
                    self._set_status("ok", msg)
            except urllib.error.URLError as exc:
                # Offline — keep/queue full snapshot for later
                self._enqueue_full_snapshot()
                self._set_status("offline", f"Hors ligne — changements mis en file ({exc.reason})")
            except Exception as exc:  # noqa: BLE001
                logger.exception("Sync failed")
                self._enqueue_full_snapshot()
                self._set_status("error", str(exc))
            return self.status

    def notify_local_change(self, kind: str = "schedule_changed") -> None:
        """
        Called by the desktop app after every local modification.
        Attempts an immediate sync; queues if offline.
        """
        self._append_queue({"kind": kind, "at": datetime.now().isoformat()})
        # Fire-and-forget in a short-lived thread to keep UI responsive
        threading.Thread(target=self.sync_now, kwargs={"full": True}, daemon=True).start()

    def get_status(self) -> SyncStatus:
        self.status.pending_count = len(self._read_queue())
        return self.status

    # -------------------------------------------------------------- payload

    def build_full_payload(self) -> dict[str, Any]:
        """Export filières, rooms and all courses from SQLite into the API sync shape."""
        conn = sqlite3.connect(self.config.sqlite_path)
        conn.row_factory = sqlite3.Row
        try:
            filieres = []
            for row in conn.execute("SELECT id, annee, nom FROM filieres"):
                filieres.append(
                    {"desktop_id": row["id"], "name": row["nom"], "level": row["annee"]}
                )

            rooms = []
            for row in conn.execute("SELECT id, nom, capacite FROM salles"):
                rooms.append(
                    {
                        "desktop_id": row["id"],
                        "name": row["nom"],
                        "capacity": row["capacite"] or 0,
                    }
                )

            salle_names = {
                r["id"]: r["nom"] for r in conn.execute("SELECT id, nom FROM salles")
            }

            schedules = []
            desktop_ids: list[int] = []
            for row in conn.execute(
                """
                SELECT id, filiere_id, date_lundi, jour, creneau, matiere, enseignant,
                       salle_id, groupe_tc
                FROM cours
                """
            ):
                start, end = CRENEAU_TIMES.get(row["creneau"], ("07:00:00", "12:00:00"))
                desktop_ids.append(row["id"])
                schedules.append(
                    {
                        "desktop_id": row["id"],
                        "filiere_desktop_id": row["filiere_id"],
                        "day": row["jour"],
                        "start_time": start,
                        "end_time": end,
                        "subject": row["matiere"],
                        "teacher": row["enseignant"],
                        "room": salle_names.get(row["salle_id"]) if row["salle_id"] else None,
                        "group_tc": row["groupe_tc"],
                        "week_date": row["date_lundi"],
                        "updated_at": datetime.now().isoformat(),
                    }
                )

            # Soft-delete: ask server to remove schedules whose desktop_id
            # is no longer present. We send an empty deleted list on full sync
            # and rely on a reconcile endpoint pattern — see reconcile_deletes.
            return {
                "filieres": filieres,
                "rooms": rooms,
                "schedules": schedules,
                "deleted_desktop_ids": [],
                "notify_students": True,
                "_local_desktop_ids": desktop_ids,  # stripped before POST
            }
        finally:
            conn.close()

    def reconcile_deletes(self, known_server_desktop_ids: list[int]) -> list[int]:
        """Return desktop_ids present on the server but missing locally."""
        payload = self.build_full_payload()
        local = set(payload.get("_local_desktop_ids") or [])
        return [i for i in known_server_desktop_ids if i not in local]

    # -------------------------------------------------------------- HTTP

    def _post_json(self, path: str, payload: dict) -> dict:
        clean = {k: v for k, v in payload.items() if not k.startswith("_")}
        # Attach deletes from queue if any
        queue = self._read_queue()
        deleted = []
        for item in queue:
            if item.get("kind") == "delete" and item.get("desktop_id"):
                deleted.append(item["desktop_id"])
        if deleted:
            clean["deleted_desktop_ids"] = list(set(clean.get("deleted_desktop_ids", []) + deleted))

        body = json.dumps(clean).encode("utf-8")
        url = self.config.api_base_url.rstrip("/") + path
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.config.api_key,
            },
        )
        with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def check_connectivity(self) -> bool:
        try:
            url = self.config.api_base_url.rstrip("/") + "/health"
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.status == 200
        except Exception:  # noqa: BLE001
            return False

    # -------------------------------------------------------------- queue

    def _ensure_queue_file(self) -> None:
        path = Path(self.config.queue_path)
        if not path.exists():
            path.write_text("[]", encoding="utf-8")

    def _read_queue(self) -> list[dict]:
        try:
            return json.loads(Path(self.config.queue_path).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return []

    def _write_queue(self, items: list[dict]) -> None:
        Path(self.config.queue_path).write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _append_queue(self, item: dict) -> None:
        items = self._read_queue()
        items.append(item)
        # Cap queue size
        self._write_queue(items[-500:])

    def _enqueue_full_snapshot(self) -> None:
        self._append_queue({"kind": "full_resync", "at": datetime.now().isoformat()})

    def _drain_queue_payload(self) -> Optional[dict]:
        items = self._read_queue()
        if not items:
            return None
        return self.build_full_payload()

    def queue_delete(self, desktop_id: int) -> None:
        self._append_queue({"kind": "delete", "desktop_id": desktop_id, "at": datetime.now().isoformat()})
        threading.Thread(target=self.sync_now, kwargs={"full": True}, daemon=True).start()

    # -------------------------------------------------------------- bg

    def _background_loop(self) -> None:
        while not self._stop.is_set():
            pending = self._read_queue()
            if pending and self.check_connectivity():
                logger.info("Connectivity restored — flushing %s pending item(s)", len(pending))
                self.sync_now(full=True)
            self._stop.wait(self.config.poll_interval_seconds)

    def _set_status(self, state: str, message: str) -> None:
        self.status.state = state
        self.status.last_message = message
        self.status.pending_count = len(self._read_queue())
        if self.on_status:
            try:
                self.on_status(self.status)
            except Exception:  # noqa: BLE001
                logger.exception("on_status callback failed")


def load_config_from_env(sqlite_path: str) -> SyncConfig:
    return SyncConfig(
        api_base_url=os.environ.get("GESTION_API_URL", "http://127.0.0.1:8000"),
        api_key=os.environ.get("GESTION_API_KEY", "desktop-admin-sync-key-change-me"),
        sqlite_path=sqlite_path,
        queue_path=os.environ.get("GESTION_SYNC_QUEUE", ""),
    )
