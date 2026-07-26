"""
GestionCours — lanceur.

Par défaut : interface web moderne (Flask).
Pour l'ancienne interface Tkinter : python main.py --desktop

Sous Windows, double-cliquer GestionCours.exe lance le web et ouvre le navigateur.
"""
import argparse
import os
import sys
import threading
import traceback
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


def run_web(host="127.0.0.1", port=5000, debug=False, open_browser=True):
    from app import app

    url = f"http://127.0.0.1:{port}"

    if open_browser:
        def _open():
            webbrowser.open(url)

        threading.Timer(1.0, _open).start()

    print(f"GestionCours — {url}")
    print("Laissez cette fenêtre ouverte. Fermez-la pour quitter.")
    # use_reloader=False is required for PyInstaller / double-click launches
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def run_desktop():
    import tkinter as tk
    from interface import PlanningApp

    root = tk.Tk()
    PlanningApp(root)
    root.mainloop()


def main():
    # Double-clic .exe : pas d'arguments → web + navigateur
    if _is_frozen() and len(sys.argv) == 1:
        try:
            run_web(host="127.0.0.1", port=5000, debug=False, open_browser=True)
        except Exception:
            _show_error(traceback.format_exc())
            sys.exit(1)
        return

    parser = argparse.ArgumentParser(description="Gestion des cours universitaires")
    parser.add_argument("--desktop", action="store_true", help="Lancer l'interface Tkinter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--no-debug", action="store_true")
    parser.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir le navigateur")
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
            )
    except Exception:
        _show_error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
