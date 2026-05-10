# ====================== 自动安装依赖（已存在自动跳过）======================
import subprocess
import sys

def auto_install(packages):
    for pkg in packages:
        pkg_name = pkg.split("=")[0].split(">")[0]
        try:
            __import__(pkg_name)
            # 已安装 → 跳过！
            continue
        except ImportError:
            # 未安装 → 后台静默安装
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pkg,
                "-q", "--no-cache-dir", "--disable-pip-version-check"
            ])

# 你项目完整依赖（一个不少，全部功能）
auto_install([
    "textual>=0.40.0",
    "rich>=13.0.0",
    "requests>=2.31.0",
    "plotext>=5.0.0",
    "akshare>=1.10.0",
    "pandas>=1.0.0",
])
# ====================== 自动安装完成 ======================

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual import on
from rich.text import Text

# Import local modules
from modules import stocks

# ASCII Art Logo
WELCOME_LOGO = """
BLOOMBERG TERMINAL FREE (OPEN-TERMINAL)
2026 © Ker ZJZ Global Economic | Some Rights Reserved
Third-party APIs & Open-Source Components belong to their respective owners.

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
                    "[bold]REGIONS[bold]\n"
                    " US: United States of America\n"
                    " SH: Shanghai China\n"
                    " SZ: Shenzhen China\n"
                    " GB: Global (Forex)\n"
                    " BA: Blockchain (Crypto)\n"
                    "[bold]MARKETS[bold]\n"
                    " STOCK: Stock Equity\n"
                    " FOREX: Foreign Exchange\n"
                    " INDICES: Indices\n"
                    " FUTURE: Futures\n"
                    " FUND: Mutual Fund\n"
                    " CRYPTO: Cryptocurrency\n"
                    # " GOVT: Government Bonds"
                    # " CORP: Corporate Bonds\n"
                    "[bold]FUNCTIONS[bold]\n"
                    " DES/INFO: Basic Information\n"
                    # " INFO: Basic Information"
                    " CHART/GP: K-Line Chart\n"
                    # " GP: K-Line Chart"
                    " QUOTE: Real-Time Quote\n"
                    " TICK: Tick Data\n"
                    " DEPTH: Order Book Depth\n"
                    # " CN: News"
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
            todo
            """
            log.write(help_text)

        elif cmd == "CLS":
            log.clear()

        elif cmd in ("EXIT", "QUIT"):
            self.exit()

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