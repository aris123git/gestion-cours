"""
GestionCours — lanceur.

Par défaut : interface web moderne (Flask).
Pour l'ancienne interface Tkinter : python main.py --desktop

Sous Windows, double-cliquer GestionCours.exe lance le serveur local,
attend qu'il soit prêt, ouvre le navigateur, puis réduit la fenêtre de statut.
"""
import argparse
import os
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser


def _is_frozen():
    return getattr(sys, "frozen", False)


def _show_error(message):
    """Affiche l'erreur même sans console (double-clic .exe)."""
    log_path = None
    try:
        from config import BASE_DIR
        log_path = os.path.join(BASE_DIR, "gestioncours-error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        pass

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        detail = message if len(message) < 1200 else message[:1200] + "\n..."
        if log_path:
            detail += f"\n\nLog : {log_path}"
        messagebox.showerror("GestionCours — erreur", detail)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def _wait_server(base_url, timeout=20):
    """Attend que Flask réponde avant d'ouvrir le navigateur."""
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base_url + "/api/meta", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception as exc:
            last_err = exc
            time.sleep(0.25)
    raise RuntimeError(f"Le serveur n'a pas démarré à temps ({base_url}). {last_err}")


def _find_free_port(host, preferred=5000, tries=15):
    import socket

    for port in range(preferred, preferred + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError("Aucun port libre pour démarrer GestionCours")


def _status_window(url):
    """Fenêtre de statut (coin bas-droit), sans rester au-dessus du navigateur."""
    import tkinter as tk

    root = tk.Tk()
    root.title("GestionCours")
    root.resizable(False, False)
    # Ne PAS forcer topmost : ça bloquait le navigateur
    try:
        root.attributes("-topmost", False)
    except Exception:
        pass

    frame = tk.Frame(root, padx=16, pady=12)
    frame.pack()
    status = tk.StringVar(value="Serveur démarré")
    tk.Label(
        frame,
        text="GestionCours",
        font=("Segoe UI", 11, "bold"),
    ).pack(anchor="w")
    tk.Label(frame, textvariable=status, font=("Segoe UI", 9), justify="left").pack(
        anchor="w", pady=(4, 8)
    )
    tk.Label(
        frame,
        text=url,
        font=("Segoe UI", 8),
        fg="#333",
    ).pack(anchor="w")

    btn_row = tk.Frame(frame)
    btn_row.pack(fill="x", pady=(10, 0))

    def open_ui():
        webbrowser.open(url)

    tk.Button(btn_row, text="Ouvrir l'interface", command=open_ui).pack(
        side="left", padx=(0, 8)
    )
    tk.Button(btn_row, text="Quitter", command=root.destroy).pack(side="left")

    root.update_idletasks()
    w, h = max(root.winfo_width(), 280), max(root.winfo_height(), 120)
    x = max(20, root.winfo_screenwidth() - w - 24)
    y = max(20, root.winfo_screenheight() - h - 60)
    root.geometry(f"{w}x{h}+{x}+{y}")

    # Après ouverture navigateur : réduire dans la barre des tâches
    def iconify_later():
        try:
            root.iconify()
            status.set("En cours (réduire / restaurer depuis la barre des tâches)")
        except Exception:
            pass

    root.after(1500, iconify_later)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
    os._exit(0)


def run_web(host="127.0.0.1", port=None, debug=False, open_browser=True, status_ui=None):
    from app import app

    if port is None:
        port = _find_free_port(host, 5000)
    url = f"http://127.0.0.1:{port}"
    if status_ui is None:
        status_ui = _is_frozen()

    ready = {"ok": False, "error": None}

    def serve():
        try:
            app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
        except Exception as exc:
            ready["error"] = exc

    if status_ui:
        threading.Thread(target=serve, daemon=True).start()
        try:
            _wait_server(url)
            ready["ok"] = True
        except Exception as exc:
            _show_error(str(exc))
            sys.exit(1)
        if open_browser:
            webbrowser.open(url)
        _status_window(url)
        return

    print(f"GestionCours — {url}")
    print("Laissez cette fenêtre ouverte. Fermez-la pour quitter.")
    if open_browser:
        def _open():
            try:
                _wait_server(url)
                webbrowser.open(url)
            except Exception:
                pass

        threading.Thread(target=_open, daemon=True).start()
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)


def run_desktop():
    import tkinter as tk
    from interface import PlanningApp

    root = tk.Tk()
    PlanningApp(root)
    root.mainloop()


def main():
    if _is_frozen() and len(sys.argv) == 1:
        try:
            run_web(host="127.0.0.1", debug=False, open_browser=True, status_ui=True)
        except Exception:
            _show_error(traceback.format_exc())
            sys.exit(1)
        return

    parser = argparse.ArgumentParser(description="Gestion des cours universitaires")
    parser.add_argument("--desktop", action="store_true", help="Lancer l'interface Tkinter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-debug", action="store_true")
    parser.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir le navigateur")
    parser.add_argument(
        "--status-ui",
        action="store_true",
        help="Afficher la petite fenêtre de statut (comme le .exe)",
    )
    args = parser.parse_args()

    try:
        if args.desktop:
            run_desktop()
        else:
            debug = (not args.no_debug) and (not _is_frozen())
            run_web(
                host=args.host,
                port=args.port,
                debug=debug,
                open_browser=not args.no_browser,
                status_ui=args.status_ui or _is_frozen(),
            )
    except Exception:
        _show_error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
