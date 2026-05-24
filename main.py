import sys
import os

# 终端标题全平台兼容
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleW("BLOOMBERG TERMINAL FREE (OPEN-TERMINAL) | Ker ZJZ Global Economic")
else:
    print("\033]0;BLOOMBERG TERMINAL FREE (OPEN-TERMINAL) | Ker ZJZ Global Economic\a", end="")

# 判断是否为 Termux (Android) 环境
IS_TERMUX = sys.platform == "linux" and os.path.exists("/data/data/com.termux")

# ====================== 自动安装依赖（全平台兼容：Termux跳过mini‑racer，其他正常）======================
import subprocess
import asyncio

def auto_install(packages):
    for pkg in packages:
        pkg_name = pkg.split(">=")[0]
        try:
            __import__(pkg_name)
            continue
        except ImportError:
            # Termux 特殊处理 akshare：跳过 mini‑racer，手动安装依赖
            if IS_TERMUX and pkg_name == "akshare":
                print("[INFO] Termux 环境：跳过 mini‑racer，无依赖安装 akshare")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", pkg, "--no-deps",
                    "--no-cache-dir", "--disable-pip-version-check"
                ])
                # 手动安装 akshare 必需依赖（排除无法编译的 mini‑racer）
                dep_list = [
                    "beautifulsoup4>=4.9.1", "lxml>=4.2.1", "pandas>=2.0.0",
                    "requests>=2.22.0", "curl_cffi>=0.13.0", "html5lib>=1.0.1",
                    "xlrd>=1.2.0", "tqdm>=4.43.0", "openpyxl>=3.0.3",
                    "jsonpath>=0.82", "tabulate>=0.8.6", "decorator>=4.4.2",
                    "webencodings", "et-xmlfile"
                ]
                for dep in dep_list:
                    dep_name = dep.split(">=")[0]
                    try:
                        __import__(dep_name)
                    except ImportError:
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install", dep,
                             "--no-cache-dir", "--disable-pip-version-check"
                        ])
            else:
                # Windows / Linux / macOS 正常安装
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", pkg,
                    "--no-cache-dir", "--disable-pip-version-check"
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
from textual.keys import Keys
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

    # 只加这三行
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_history = []
        self.history_index = -1
        self.temp_input = ""

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

    # 👇 修复后：正确的上下箭头监听（唯一改动点）
    def on_key(self, event):
        input_widget = self.query_one("#command_input", Input)
        if self.focused == input_widget:
            if event.key == Keys.Up:
                self.navigate_history(1)
            elif event.key == Keys.Down:
                self.navigate_history(-1)

    # 只加这个方法
    def navigate_history(self, direction):
        inp = self.query_one("#command_input")
        if self.history_index == -1 and direction == 1:
            self.temp_input = inp.value
        new_idx = self.history_index + direction
        if new_idx >= len(self.command_history):
            new_idx = len(self.command_history)-1
        if new_idx < -1:
            new_idx = -1
        if new_idx == -1:
            inp.value = self.temp_input
        else:
            inp.value = self.command_history[new_idx]
        self.history_index = new_idx
        inp.cursor_position = len(inp.value)

    @on(Input.Submitted)
    def handle_command(self, event: Input.Submitted):
        command = event.value.upper().strip()
        input_widget = self.query_one("#command_input")
        log = self.query_one("#output_log", RichLog)

        # 只加保存历史
        if command and (not self.command_history or self.command_history[0] != command):
            self.command_history.insert(0, command)
        self.history_index = -1
        self.temp_input = ""

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
  DES/INFO: Basic information
  QUOTE: Real-time quote
  CHART/GP: K-line chart
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
