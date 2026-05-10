from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual import on
from rich.text import Text

# Import local modules
from modules import stocks, crypto, ai

# ASCII Art Logo
WELCOME_LOGO = """
BLOOMBERG TERMINAL FREE (OPEN-TERMINAL)
2026 (c) Ker ZJZ Global Economic

 > SYSTEM READY.
 > CONNECTED TO: MARKET
 > TYPE 'HELP' FOR COMMANDS.
"""

class OpenTerminal(App):
    """
    Main Application Class for Bloomberg Terminal Free.
    Uses Textual for TUI rendering.
    """
    TITLE = "BLOOMBERG TERMINAL FREE (OPEN-TERMINAL) | Ker ZJZ Global Economic"
    
    def compose(self) -> ComposeResult:
        """Construct the UI layout."""
        yield Header(show_clock=True)
        
        with Horizontal():
            # Sidebar with Cheat Sheet
            with Container(id="sidebar"):
                yield Static(
                    "[bold underline]MARKET KEYS[/bold underline]\n\n"
                    "[green]F2: GOVT\n"
                    "F3: CORP\n"
                    "F8: EQUITY\n"
                    "F11: CRYPTO[/green]\n\n"
                    "[bold underline]FUNCTIONS[/bold underline]\n\n"
                    "[yellow]DES[/yellow]: Desc.\n"
                    "[yellow]GP[/yellow]: Chart\n"
                    "[yellow]CN[/yellow]: News"
                    "STOCK: 股票\n"
                )
            
            # Main Content Window (Log)
            with Vertical(id="main-window"):
                yield RichLog(id="output_log", markup=True, wrap=True)
                
        # Command Line Input (Fixed at bottom)
        yield Input(placeholder="COMMAND LINE > Type ticker or command...", id="command_input")
        yield Footer()

    def on_mount(self):
        """Event fired when the application starts."""
        log = self.query_one("#output_log", RichLog)
        # Display welcome message
        log.write(Text(WELCOME_LOGO, style="bold orange1"))
        # Focus on input immediately
        self.query_one("#command_input").focus()

    @on(Input.Submitted)
    def handle_command(self, event: Input.Submitted):
        """Main Command Parser Logic."""
        command = event.value.upper().strip()
        input_widget = self.query_one("#command_input")
        log = self.query_one("#output_log", RichLog)
        
        # Clear input field after submission
        input_widget.value = ""
        
        # Log the command entered by user
        log.write(f"\n[reverse] COMMAND [/reverse] {command}")
        
        parts = command.split()
        if not parts:
            return

        cmd = parts[0]

        # --- SYSTEM COMMANDS ---
        if cmd == "HELP":
            help_text = """
            [bold]AVAILABLE COMMANDS:[/bold]
            
            [yellow]STOCKS:[/yellow]
            {TICKER} DES    -> Default US Stock Desc (e.g., AAPL DES)
            {TICKER} CHART  -> Default US Stock Chart (e.g., TSLA CHART)
            {TICKER} {REGION} {TYPE} DES  -> Custom Desc (e.g., 000001 SZ STOCK DES)
            {TICKER} {REGION} {TYPE} CHART -> Custom Chart (e.g., BA US STOCK CHART)
            
            [yellow]CRYPTO:[/yellow]
            CRYPTO          -> Top 10 Currencies
            
            [yellow]AI ASSISTANT:[/yellow]
            ASK {QUERY}     -> Ask Warren AI (e.g., ASK Why is market down?)
            
            [yellow]SYSTEM:[/yellow]
            CLS             -> Clear Screen
            EXIT            -> Quit
            """
            log.write(help_text)

        elif cmd == "CLS":
            log.clear()

        elif cmd in ("EXIT", "QUIT"):
            self.exit()

        # --- MODULE: CRYPTO ---
        elif cmd == "CRYPTO":
            log.write("[blink]Fetching Crypto Data...[/blink]")
            # Run in main thread for MVP (should be async in production)
            data = crypto.get_top_crypto()
            log.write(data)

        # --- MODULE: AI ---
        elif cmd == "ASK":
            if len(parts) < 2:
                log.write("[red]Error:[/red] Please provide a question.")
            else:
                question = " ".join(parts[1:])
                log.write("[blink]Thinking (Llama-3)...[/blink]")
                # Simulating response delay
                self.set_timer(1.0, lambda: log.write(ai.ask_warren(question)))

        # --- MODULE: STOCKS ---
        else:
            # 把整行命令直接传给 stocks 模块，不再自己解析 sub_cmd
            full_command = " ".join(parts)
            
            # 判断最后一个词是 DES/CHART
            if len(parts) >= 2 and parts[-1] in ("DES", "QUOTE", "CHART", "GP"):
                func = parts[-1]
                if func in ("DES", "QUOTE"):
                    log.write(stocks.get_stock_quote(full_command))
                elif func in ("CHART", "GP"):
                    log.write(f"[bold]Plotting {cmd}...[/bold]")
                    chart = stocks.get_stock_chart(full_command)
                    log.write(Text(chart))
            else:
                # 默认 DES
                log.write(stocks.get_stock_quote(full_command))

if __name__ == "__main__":
    app = OpenTerminal()
    app.run()