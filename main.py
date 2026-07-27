"""
GestionCours — lanceur.

Par défaut : interface web moderne (Flask).
Pour l'ancienne interface Tkinter : python main.py --desktop

Sous Windows, double-cliquer GestionCours.exe lance le web et ouvre le navigateur
(sans fenêtre de terminal). Une petite fenêtre « En cours » permet de quitter.
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


def _status_window(url):
    """Petite fenêtre pour garder l'app vivante et permettre de quitter."""
    import tkinter as tk

    root = tk.Tk()
    root.title("GestionCours")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    frame = tk.Frame(root, padx=18, pady=14)
    frame.pack()
    tk.Label(
        frame,
        text="GestionCours est en cours",
        font=("Segoe UI", 11, "bold"),
    ).pack(anchor="w")
    tk.Label(
        frame,
        text=f"Interface : {url}\nFermez cette fenêtre pour quitter.",
        font=("Segoe UI", 9),
        justify="left",
    ).pack(anchor="w", pady=(6, 10))

    btn_row = tk.Frame(frame)
    btn_row.pack(fill="x")
    tk.Button(
        btn_row,
        text="Ouvrir le navigateur",
        command=lambda: webbrowser.open(url),
    ).pack(side="left", padx=(0, 8))
    tk.Button(btn_row, text="Quitter", command=root.destroy).pack(side="left")

    # Centrer légèrement
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 3
    root.geometry(f"+{x}+{y}")

    def on_close():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    # Fermer la fenêtre = arrêter le process (serveur inclus)
    os._exit(0)


def run_web(host="127.0.0.1", port=5000, debug=False, open_browser=True, status_ui=None):
    from app import app

    url = f"http://127.0.0.1:{port}"
    if status_ui is None:
        status_ui = _is_frozen()

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    if status_ui:
        threading.Thread(
            target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
            daemon=True,
        ).start()
        _status_window(url)
        return

    print(f"GestionCours — {url}")
    print("Laissez cette fenêtre ouverte. Fermez-la pour quitter.")
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def run_desktop():
    import tkinter as tk
    from interface import PlanningApp

    root = tk.Tk()
    PlanningApp(root)
    root.mainloop()


def main():
    # Double-clic .exe : pas d'arguments → web + navigateur + fenêtre statut
    if _is_frozen() and len(sys.argv) == 1:
        try:
            run_web(host="127.0.0.1", port=5000, debug=False, open_browser=True, status_ui=True)
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
