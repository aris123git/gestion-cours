"""
GestionCours — lanceur.

Par défaut : interface bureau native PySide6 (comme Gestion_app).
Options :
  python main.py              → PySide6
  python main.py --web        → interface Flask + navigateur
  python main.py --tk         → ancienne UI Tkinter
"""
import argparse
import os
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser


def _is_frozen():
    return getattr(sys, "frozen", False)


def _show_error(message):
    log_path = None
    try:
        from config import BASE_DIR
        log_path = os.path.join(BASE_DIR, "gestioncours-error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        pass

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        detail = message if len(message) < 1200 else message[:1200] + "\n..."
        if log_path:
            detail += f"\n\nLog : {log_path}"
        QMessageBox.critical(None, "GestionCours — erreur", detail)
    except Exception:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("GestionCours — erreur", message[:1200])
            root.destroy()
        except Exception:
            print(message, file=sys.stderr)


def run_desktop_qt():
    from desktop.main_window import run_desktop_qt as _run
    return _run()


def run_desktop_tk():
    import tkinter as tk
    from interface import PlanningApp
    root = tk.Tk()
    PlanningApp(root)
    root.mainloop()


def _wait_server(base_url, timeout=20):
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
    raise RuntimeError(f"Le serveur n'a pas démarré ({base_url}). {last_err}")


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
    raise RuntimeError("Aucun port libre")


def run_web(host="127.0.0.1", port=None, debug=False, open_browser=True):
    from app import app
    if port is None:
        port = _find_free_port(host, 5000)
    url = f"http://127.0.0.1:{port}"
    print(f"GestionCours (web) — {url}")
    if open_browser:
        def _open():
            try:
                _wait_server(url)
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=_open, daemon=True).start()
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)


def main():
    # .exe sans args → bureau PySide6
    if _is_frozen() and len(sys.argv) == 1:
        try:
            sys.exit(run_desktop_qt() or 0)
        except Exception:
            _show_error(traceback.format_exc())
            sys.exit(1)

    parser = argparse.ArgumentParser(description="Gestion des cours universitaires")
    parser.add_argument("--web", action="store_true", help="Interface Flask + navigateur")
    parser.add_argument("--tk", "--desktop", dest="tk", action="store_true",
                        help="Ancienne interface Tkinter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-debug", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    try:
        if args.web:
            debug = (not args.no_debug) and (not _is_frozen())
            run_web(
                host=args.host,
                port=args.port,
                debug=debug,
                open_browser=not args.no_browser,
            )
        elif args.tk:
            run_desktop_tk()
        else:
            sys.exit(run_desktop_qt() or 0)
    except Exception:
        _show_error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
