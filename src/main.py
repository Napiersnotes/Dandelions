#!/usr/bin/env python3
"""
Dandelions - Multi-LLM Nostr MCP Bot
Main entry point with graceful startup/shutdown
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import settings
from src.nostr.client import NostrClient
from src.llm.manager import LLMManager
from src.mcp.server import MCPServer
from src.ui.web_app import WebUI
from src.utils.logger import setup_logger

console = Console()
logger = setup_logger(__name__)
app = typer.Typer(help="Dandelions - Nostr MCP Bot")

class DandelionsBot:
    """Main bot orchestrator"""
    
    def __init__(self):
        self.nostr_client: Optional[NostrClient] = None
        self.llm_manager: Optional[LLMManager] = None
        self.mcp_server: Optional[MCPServer] = None
        self.web_ui: Optional[WebUI] = None
        self.running = False
        
    async def initialize(self):
        """Initialize all components"""
        try:
            console.print("[bold green]🌸 Starting Dandelions Bot...[/bold green]")
            
            # Display banner
            self._display_banner()
            
            # Initialize LLM Manager
            console.print("[yellow]⚙️ Initializing LLM Manager...[/yellow]")
            self.llm_manager = LLMManager()
            await self.llm_manager.initialize()
            
            # Initialize Nostr Client
            console.print("[yellow]⚙️ Initializing Nostr Client...[/yellow]")
            self.nostr_client = NostrClient(llm_manager=self.llm_manager)
            await self.nostr_client.initialize()
            
            # Initialize MCP Server
            console.print("[yellow]⚙️ Initializing MCP Server...[/yellow]")
            self.mcp_server = MCPServer(
                nostr_client=self.nostr_client,
                llm_manager=self.llm_manager
            )
            await self.mcp_server.initialize()
            
            # Initialize Web UI if enabled
            if settings.WEB_UI_ENABLED:
                console.print("[yellow]⚙️ Initializing Web UI...[/yellow]")
                self.web_ui = WebUI(
                    nostr_client=self.nostr_client,
                    llm_manager=self.llm_manager
                )
                await self.web_ui.initialize()
            
            self.running = True
            console.print("[bold green]✅ Dandelions Bot initialized successfully![/bold green]")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    async def start(self):
        """Start all services"""
        try:
            # Start Nostr client
            await self.nostr_client.start()
            
            # Start MCP server
            await self.mcp_server.start()
            
            # Start Web UI
            if self.web_ui:
                await self.web_ui.start()
            
            # Display status
            self._display_status()
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Received shutdown signal...[/yellow]")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        console.print("[yellow]🔄 Shutting down...[/yellow]")
        
        if self.nostr_client:
            await self.nostr_client.stop()
        
        if self.mcp_server:
            await self.mcp_server.stop()
        
        if self.web_ui:
            await self.web_ui.stop()
        
        console.print("[bold green]👋 Dandelions Bot stopped[/bold green]")
    
    def _display_banner(self):
        """Display startup banner"""
        banner = """
╔══════════════════════════════════════════╗
║         🌸 Dandelions Bot v1.0 🌸         ║
║  Multi-LLM Nostr MCP Bot with Web UI     ║
╚══════════════════════════════════════════╝
        """
        console.print(Panel(banner, border_style="cyan"))
    
    def _display_status(self):
        """Display system status"""
        table = Table(title="System Status", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        table.add_row("LLM Manager", "✅", f"{len(self.llm_manager.providers)} providers loaded")
        table.add_row("Nostr Client", "✅", f"Connected to {len(settings.NOSTR_RELAYS)} relays")
        table.add_row("MCP Server", "✅", f"Port {settings.MCP_PORT}")
        table.add_row("Web UI", "✅" if settings.WEB_UI_ENABLED else "❌", 
                     f"http://localhost:{settings.WEB_UI_PORT}" if settings.WEB_UI_ENABLED else "Disabled")
        
        console.print(table)

@app.command()
def start(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    web_ui: bool = typer.Option(
        True,
        "--web-ui/--no-web-ui",
        help="Enable/disable web interface"
    ),
    headless: bool = typer.Option(
        False,
        "--headless",
        help="Run without any interface"
    )
):
    """Start the Dandelions bot"""
    # Load config if provided
    if config_file:
        settings.load_config(config_file)
    
    # Override web UI setting
    settings.WEB_UI_ENABLED = web_ui
    
    # Run bot
    bot = DandelionsBot()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        loop.create_task(bot.shutdown())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        loop.run_until_complete(bot.initialize())
        loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(bot.shutdown())

@app.command()
def setup():
    """Run interactive setup wizard"""
    from scripts.setup_wizard import run_setup_wizard
    run_setup_wizard()

@app.command()
def list_providers():
    """List available LLM providers"""
    manager = LLMManager()
    manager.list_providers()

@app.command()
def test_connection():
    """Test connections to all services"""
    # Implementation for connection testing
    pass

def main():
    """Main entry point"""
    app()

if __name__ == "__main__":
    main()
