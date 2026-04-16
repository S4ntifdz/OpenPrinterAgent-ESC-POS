"""Main entry point for OpenPrinterAgent CLI."""

import argparse
import sys


def run_api() -> None:
    """Run the Flask API server."""
    from src.api.app import create_app
    from src.utils.config import load_config

    config = load_config()
    app = create_app(config)

    print(f"Starting OpenPrinterAgent API on {config.API_HOST}:{config.API_PORT}")
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.FLASK_DEBUG)


def run_gui() -> None:
    """Run the GUI application."""
    from src.gui.app import run_gui

    print("Starting OpenPrinterAgent GUI...")
    run_gui()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="OpenPrinterAgent - ESC/POS Thermal Printer Controller"
    )
    parser.add_argument(
        "mode",
        choices=["api", "gui"],
        help="Run mode: 'api' for REST server, 'gui' for desktop application",
    )

    args = parser.parse_args()

    if args.mode == "api":
        run_api()
    elif args.mode == "gui":
        run_gui()

    return 0


if __name__ == "__main__":
    sys.exit(main())
