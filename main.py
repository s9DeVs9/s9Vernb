
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    os.makedirs("results", exist_ok=True)
    os.makedirs("combolists", exist_ok=True)

    try:
        if "--gui" in sys.argv:
            import customtkinter as ctk
            from ui.app import App
            root = ctk.CTk()
            app = App(root)
            try:
                root.mainloop()
            except KeyboardInterrupt:
                app._on_close()
        else:
            from cli import run_cli
            run_cli()
    except KeyboardInterrupt:
        print("\n  S9Checker terminated.")
        sys.exit(0)


if __name__ == "__main__":
    main()
