"""
GestionCours — lanceur.

Par défaut : interface web moderne (Flask).
Pour l'ancienne interface Tkinter : python main.py --desktop
"""
import argparse
import sys


def run_web(host="0.0.0.0", port=5000, debug=True):
    from app import app
    print(f"GestionCours — http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}")
    app.run(host=host, port=port, debug=debug)


def run_desktop():
    import tkinter as tk
    from interface import PlanningApp
    root = tk.Tk()
    PlanningApp(root)
    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gestion des cours universitaires")
    parser.add_argument("--desktop", action="store_true", help="Lancer l'interface Tkinter")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--no-debug", action="store_true")
    args = parser.parse_args()

    if args.desktop:
        run_desktop()
    else:
        run_web(host=args.host, port=args.port, debug=not args.no_debug)
