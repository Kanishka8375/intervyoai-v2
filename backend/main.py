"""
IntervyoAI - Main Entry Point
Real-time AI Interview Copilot - 100% Undetectable
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from rich.console import Console
from rich.panel import Panel

from backend.config import server_settings
from backend.server.api import IntervyoServer

logger.add("logs/intervyoai.log", rotation="10 MB", level="INFO")
console = Console()


class IntervyoAI:
    def __init__(self):
        self.server = None
        self._is_running = False

    def initialize(self):
        console.print(
            Panel.fit(
                "[bold cyan]IntervyoAI[/bold cyan] - Interview Copilot\n"
                "[dim]100% Local • 100% Undetectable • 100% Open Source[/dim]",
                border_style="cyan",
            )
        )

        with console.status("[bold green]Initializing components...") as status:
            status.update("Starting server...")
            try:
                self.server = IntervyoServer(
                    host=server_settings.host, port=server_settings.port
                )
                console.print("[green]✓ Server started successfully[/green]")
            except Exception as e:
                logger.error(f"Server init failed: {e}")
                raise

        console.print(
            f"[green]Server running at http://{self.server._get_local_ip()}:{server_settings.port}[/green]"
        )
        logger.info("IntervyoAI initialized successfully")

    def start(self):
        self._is_running = True
        logger.info("IntervyoAI started")

    def stop(self):
        self._is_running = False
        logger.info("IntervyoAI stopped")

    def run(self):
        self.initialize()
        self._is_running = True

        def signal_handler(sig, frame):
            console.print("\n[yellow]Shutting down...[/yellow]")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        console.print("\n[bold green]IntervyoAI is running![/bold green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        import threading

        server_thread = threading.Thread(target=self.server.run, daemon=True)
        server_thread.start()

        try:
            while self._is_running:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def main():
    app = IntervyoAI()
    app.run()


if __name__ == "__main__":
    main()
