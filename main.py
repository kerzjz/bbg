import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(
    "BLOOMBERG TERMINAL FREE (OPEN-TERMINAL) | Ker ZJZ Global Economic"
)

# ====================== SSH/tmate 终端自动修复（云端自动开，本地自动关）======================
# 只有在 GitHub Actions / Linux 云端环境才执行，本地 Windows 绝对不跑！
# if os.environ.get("GITHUB_ACTIONS") == "true" or os.name != "nt":
#     print("✅ 检测到云端环境，自动启用 tmate / 终端修复")
#     os.environ["TERM"] = "xterm-256color"
#     os.system("tmate set mouse on 2>/dev/null")
# else:
#     print("✅ 检测到本地 Windows 环境，跳过 tmate 配置，不炸终端！")
# ==========================================================================================

# ====================== 自动安装依赖（已存在自动跳过）======================
import subprocess
import sys
import asyncio

def auto_install(packages):
    for pkg in packages:
        pkg_name = pkg.split("=")[0].split(">")[0]
        try:
            __import__(pkg_name)
            continue
        except ImportError:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pkg,
                "-q", "--no-cache-dir", "--disable-pip-version-check"
            ])

auto_install([
    "textual>=0.40.0",
    "rich>=13.0.0",
    "requests>=2.31.0",
    "plotext>=5.0.0",
    "akshare>=1.10.0",
    "pandas>=1.0.0",
    "feedparser>=1.0.0",
])
# ====================== 自动安装完成 ======================

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual import on
from rich.text import Text

# Import local modules
from modules import stocks, rss  # 确保 rss 模块已正确导入

WELCOME_LOGO = """
BLOOMBERG TERMINAL FREE (OPEN-TERMINAL)
2026 © Ker ZJZ Global Economic | Some Rights Reserved
Third-party APIs & Open-Source Components belong to their respective owners.

 > SYSTEM READY.
 > CONNECTED TO: MARKET
 > TYPE 'HELP' FOR COMMANDS.
"""

class OpenTerminal(App):
    TITLE = "BLOOMBERG TERMINAL FREE (OPEN-TERMINAL) | Ker ZJZ Global Economic"
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal():
            with Container(id="sidebar"):
                yield Static(
                    "[bold]SEARCH: {PRODUCT} {REGION} {MARKET} {FUNCTION}[bold]\n"
                    "[bold]PRODUCTS[bold]\n"
                    " AU: Gold (Gold)\n"
                    " AG: Silver (Gold)\n"
                    " PT: Platinum (Gold)\n"
                    " PD: Palladium (Gold)\n"
                    " {SYMBOL}: PRODUCTS (Stock, Forex, Indices, Future, Fund, Crypto)\n"
                    "[bold]REGIONS[bold]\n"
                    " US: United States of America\n"
                    " SH: Shanghai China\n"
                    " SZ: Shenzhen China\n"
                    " GB: Global (Forex)\n"
                    " BA: Blockchain (Crypto)\n"
                    "[bold]MARKETS[bold]\n"
                    " STOCK: Stock Equity\n"
                    " GOLD: Gold\n"
                    " FOREX: Foreign Exchange\n"
                    " INDICES: Indices\n"
                    " FUTURE: Futures\n"
                    " FUND: Mutual Fund\n"
                    " CRYPTO: Cryptocurrency\n"
                    "[bold]FUNCTIONS[bold]\n"
                    " DES/INFO: Basic Information\n"
                    " CHART/GP: K-Line Chart\n"
                    " QUOTE: Real-Time Quote\n"
                    " TICK: Tick Data\n"
                    " DEPTH: Order Book Depth\n"
                    "[bold]RSS COMMANDS[bold]\n"
                    " RSS LIST: Show all RSS sources\n"
                    " RSS [CODE]: Get news (e.g. RSS NTS)\n"
                )
            
            with Vertical(id="main-window"):
                yield RichLog(id="output_log", markup=True, wrap=True)
                
        yield Input(placeholder="COMMAND LINE > Type ticker or command...", id="command_input")
        yield Footer()

    def on_mount(self):
        log = self.query_one("#output_log", RichLog)
        log.write(Text(WELCOME_LOGO, style="bold orange1"))
        self.query_one("#command_input").focus()

    @on(Input.Submitted)
    def handle_command(self, event: Input.Submitted):
        command = event.value.upper().strip()
        input_widget = self.query_one("#command_input")
        log = self.query_one("#output_log", RichLog)
        
        input_widget.value = ""
        log.write(f"\n[reverse] COMMAND [/reverse] {command}")
        
        parts = command.split()
        if not parts:
            return

        cmd = parts[0]

        # ========== 优先处理 RSS 指令 ==========
        if cmd == "RSS":
            if len(parts) == 1:
                # 仅输入 RSS，提示用法
                log.write("[bold yellow]⚠️ RSS Usage:[/bold yellow]\n"
                          "  RSS LIST - Show all available RSS sources\n"
                          "  RSS [CODE] [LIMIT] - Get news (e.g. RSS SINA 5)")
            elif parts[1] == "LIST":
                # 显示 RSS 源列表
                rss_table = rss.get_rss_source_table()
                log.write(rss_table)
            else:
                # 解析 RSS 源和条数
                source_code = parts[1] if len(parts) >= 2 else ""
                limit = parts[2] if len(parts) >= 3 else 10
                news = rss.get_rss_news(source_code, limit)
                log.write(news)
            return  # 终止后续解析，避免进入股票逻辑

        # ========== 原有指令逻辑 ==========
        if cmd == "HELP":
            help_text = """
[bold green]📖 OPEN-TERMINAL HELP[/bold green]
[bold]Basic Commands:[/bold]
  HELP - Show this help message
  CLS - Clear screen
  EXIT/QUIT - Exit the terminal
[bold]RSS Commands:[/bold]
  RSS LIST - Show all available RSS news sources
  RSS [CODE] [LIMIT] - Get news from specified source (e.g. RSS SINA 5)
[bold]Stock/Forex/Gold Commands:[/bold]
  [CODE] [REGION] [FUNC] - Basic query (e.g. AAPL US QUOTE)
  [CODE] [FUNC] - Quick query (e.g. 600000 SH DES, BTC BA QUOTE)
[bold]Functions:[/bold]
  DES/INFO - Basic information
  QUOTE - Real-time quote
  CHART/GP - K-line chart
  TICK - Tick data
  DEPTH - Order book depth
            """
            log.write(help_text)

        elif cmd == "CLS":
            log.clear()

        elif cmd in ("EXIT", "QUIT"):
            self.exit()

        else:
            full_command = " ".join(parts)
            if len(parts) >= 2 and parts[-1] in ("DES", "QUOTE", "CHART", "GP"):
                func = parts[-1]
                if func in ("DES", "QUOTE"):
                    log.write(stocks.get_stock_quote(full_command))
                elif func in ("CHART", "GP"):
                    log.write(f"[bold]Plotting {cmd}...[/bold]")
                    chart = stocks.get_stock_chart(full_command)
                    log.write(Text(chart))
            else:
                log.write(stocks.get_stock_quote(full_command))

# ====================== ✅ 核心修复：异步启动 ======================
if __name__ == "__main__":
    async def main():
        app = OpenTerminal()
        await app.run_async()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass