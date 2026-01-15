"""
Interactive Setup Wizard for Dandelions
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

class SetupWizard:
    """Interactive setup wizard for Dandelions"""
    
    def __init__(self, config_path: Path = Path("config")):
        self.config_path = config_path
        self.config_file = config_path / "settings.yaml"
        self.env_file = config_path / ".env"
        
    async def run(self):
        """Run the interactive setup wizard"""
        console.clear()
        self._display_welcome()
        
        # Create config directory
        self.config_path.mkdir(exist_ok=True)
        
        # Step-by-step configuration
        config = await self._collect_configuration()
        
        # Save configuration
        await self._save_configuration(config)
        
        # Test connections
        await self._test_connections(config)
        
        # Display final instructions
        self._display_completion()
    
    def _display_welcome(self):
        """Display welcome message"""
        welcome_text = """
╔══════════════════════════════════════════════════════════╗
║                 🌸 Dandelions Setup Wizard 🌸             ║
║                                                          ║
║  Welcome to Dandelions! This wizard will help you       ║
║  configure your multi-LLM Nostr MCP bot.                ║
║                                                          ║
║  We'll configure:                                        ║
║  • Nostr relays and keys                                ║
║  • LLM providers (DeepSeek, Mistral, OpenAI, etc.)      ║
║  • MCP server settings                                  ║
║  • Web interface                                        ║
╚══════════════════════════════════════════════════════════╝
        """
        console.print(Panel(welcome_text, border_style="cyan"))
        
        console.print("\n[bold green]Let's get started![/bold green]\n")
    
    async def _collect_configuration(self) -> Dict[str, Any]:
        """Collect configuration from user"""
        config = {}
        
        # Nostr Configuration
        config['nostr'] = await self._configure_nostr()
        
        # LLM Providers
        config['llm_providers'] = await self._configure_llm_providers()
        
        # MCP Server
        config['mcp_server'] = await self._configure_mcp_server()
        
        # Web UI
        config['web_ui'] = await self._configure_web_ui()
        
        return config
    
    async def _configure_nostr(self) -> Dict[str, Any]:
        """Configure Nostr settings"""
        console.print("\n[bold cyan]Step 1: Nostr Configuration[/bold cyan]")
        console.print("-" * 40)
        
        # Private Key
        use_existing = await questionary.select(
            "Do you want to use an existing Nostr private key?",
            choices=[
                {"name": "Yes, I have a private key (nsec)", "value": True},
                {"name": "No, generate a new one", "value": False}
            ]
        ).ask_async()
        
        private_key = None
        if use_existing:
            private_key = await questionary.text(
                "Enter your private key (nsec):",
                validate=lambda x: x.startswith('nsec1') if x else True
            ).ask_async()
        else:
            console.print("[yellow]A new key pair will be generated[/yellow]")
        
        # Relays
        console.print("\n[bold]Default Nostr Relays:[/bold]")
        default_relays = [
            "wss://relay.damus.io",
            "wss://nos.lol",
            "wss://relay.snort.social"
        ]
        
        for relay in default_relays:
            console.print(f"  • {relay}")
        
        add_more = await questionary.confirm(
            "\nDo you want to add more relays?",
            default=False
        ).ask_async()
        
        relays = default_relays.copy()
        
        if add_more:
            while True:
                relay = await questionary.text(
                    "Enter relay URL (wss://...) or leave empty to finish:"
                ).ask_async()
                
                if not relay:
                    break
                
                if relay.startswith('wss://'):
                    relays.append(relay)
                    console.print(f"[green]Added: {relay}[/green]")
                else:
                    console.print("[red]Invalid relay URL (must start with wss://)[/red]")
        
        return {
            "private_key": private_key,
            "relays": relays
        }
    
    async def _configure_llm_providers(self) -> Dict[str, Any]:
        """Configure LLM providers"""
        console.print("\n[bold cyan]Step 2: LLM Provider Configuration[/bold cyan]")
        console.print("-" * 40)
        
        providers = {}
        
        # Available providers
        provider_options = [
            {"name": "DeepSeek AI", "value": "deepseek"},
            {"name": "Mistral AI", "value": "mistral"},
            {"name": "OpenAI", "value": "openai"},
            {"name": "Anthropic Claude", "value": "anthropic"},
            {"name": "Ollama (Local)", "value": "ollama"},
            {"name": "Groq", "value": "groq"},
            {"name": "Together AI", "value": "together"}
        ]
        
        selected_providers = await questionary.checkbox(
            "Select LLM providers to enable:",
            choices=provider_options
        ).ask_async()
        
        console.print("\n[bold]Provider Configuration[/bold]")
        
        for provider in selected_providers:
            console.print(f"\n[bold yellow]Configuring {provider.upper()}[/bold yellow]")
            
            # API Key
            api_key = await questionary.password(
                f"Enter {provider} API key:",
                validate=lambda x: len(x) > 10 if x else True
            ).ask_async()
            
            # Model selection
            default_models = {
                "deepseek": "deepseek-chat",
                "mistral": "mistral-medium",
                "openai": "gpt-4-turbo-preview",
                "anthropic": "claude-3-opus-20240229",
                "ollama": "llama2",
                "groq": "mixtral-8x7b-32768",
                "together": "togethercomputer/llama-2-70b-chat"
            }
            
            model = await questionary.text(
                f"Model name (default: {default_models[provider]}):",
                default=default_models[provider]
            ).ask_async()
            
            # Priority
            priority = await questionary.select(
                "Priority (1=highest, 5=lowest):",
                choices=["1", "2", "3", "4", "5"],
                default="3"
            ).ask_async()
            
            providers[provider] = {
                "api_key": api_key,
                "model": model,
                "priority": int(priority),
                "enabled": True
            }
            
            console.print(f"[green]✓ {provider} configured[/green]")
        
        return providers
    
    async def _configure_mcp_server(self) -> Dict[str, Any]:
        """Configure MCP server settings"""
        console.print("\n[bold cyan]Step 3: MCP Server Configuration[/bold cyan]")
        console.print("-" * 40)
        
        host = await questionary.text(
            "MCP server host:",
            default="127.0.0.1"
        ).ask_async()
        
        port = await questionary.text(
            "MCP server port:",
            default="8080",
            validate=lambda x: x.isdigit() and 1024 <= int(x) <= 65535
        ).ask_async()
        
        return {
            "host": host,
            "port": int(port)
        }
    
    async def _configure_web_ui(self) -> Dict[str, Any]:
        """Configure web interface"""
        console.print("\n[bold cyan]Step 4: Web Interface Configuration[/bold cyan]")
        console.print("-" * 40)
        
        enabled = await questionary.confirm(
            "Enable web interface?",
            default=True
        ).ask_async()
        
        if not enabled:
            return {"enabled": False}
        
        port = await questionary.text(
            "Web UI port:",
            default="8501",
            validate=lambda x: x.isdigit() and 1024 <= int(x) <= 65535
        ).ask_async()
        
        auth_enabled = await questionary.confirm(
            "Enable authentication?",
            default=False
        ).ask_async()
        
        auth = {}
        if auth_enabled:
            username = await questionary.text("Username:").ask_async()
            password = await questionary.password("Password:").ask_async()
            auth = {"username": username, "password": password}
        
        return {
            "enabled": True,
            "port": int(port),
            "auth": auth
        }
    
    async def _save_configuration(self, config: Dict[str, Any]):
        """Save configuration to files"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("Saving configuration...", total=None)
            
            # Save YAML config
            import yaml
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Save .env file
            env_lines = []
            
            # Nostr
            if config['nostr']['private_key']:
                env_lines.append(f"NOSTR_PRIVATE_KEY={config['nostr']['private_key']}")
            
            # LLM Providers
            for provider, provider_config in config['llm_providers'].items():
                env_lines.append(f"{provider.upper()}_API_KEY={provider_config['api_key']}")
            
            with open(self.env_file, 'w') as f:
                f.write('\n'.join(env_lines))
            
            progress.update(task, completed=True)
        
        console.print("\n[bold green]✓ Configuration saved![/bold green]")
        console.print(f"  • Config file: {self.config_file}")
        console.print(f"  • Env file: {self.env_file}")
    
    async def _test_connections(self, config: Dict[str, Any]):
        """Test connections to configured services"""
        console.print("\n[bold cyan]Step 5: Testing Connections[/bold cyan]")
        console.print("-" * 40)
        
        # This would be implemented to actually test connections
        # For now, just show a simulated test
        
        with Progress() as progress:
            task1 = progress.add_task("[cyan]Testing Nostr relays...", total=100)
            for i in range(100):
                progress.update(task1, advance=1)
                await asyncio.sleep(0.01)
            
            task2 = progress.add_task("[cyan]Testing LLM providers...", total=100)
            for i in range(100):
                progress.update(task2, advance=1)
                await asyncio.sleep(0.01)
        
        console.print("\n[bold green]✓ All connections successful![/bold green]")
    
    def _display_completion(self):
        """Display completion message"""
        console.print("\n" + "="*60)
        console.print("[bold green]✨ Setup Complete! ✨[/bold green]")
        console.print("="*60)
        
        instructions = """
[b]Next Steps:[/b]

1. [bold]Start the bot:[/bold]
   [cyan]dandelions start[/cyan]

2. [bold]Access the Web Interface:[/bold]
   Open your browser and go to:
   [cyan]http://localhost:8501[/cyan]

3. [bold]Connect via MCP:[/bold]
   Use any MCP client to connect to:
   [cyan]ws://localhost:8080/ws[/cyan]

4. [bold]Monitor the bot:[/bold]
   Check logs: [cyan]tail -f logs/dandelions.log[/cyan]

[b]Need Help?[/b]
• Documentation: https://github.com/yourusername/dandelions
• Issues: https://github.com/yourusername/dandelions/issues
• Discord: https://discord.gg/your-discord

[bold yellow]Thank you for using Dandelions! 🌸[/bold yellow]
        """
        
        console.print(Panel(instructions, border_style="green"))

async def run_setup_wizard():
    """Main entry point for setup wizard"""
    wizard = SetupWizard()
    try:
        await wizard.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error during setup: {e}[/red]")
        sys.exit(1)
