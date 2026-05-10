import sys
import json
import requests
import plotext as plt
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()
plt.clear_figure()
plt.theme('classic')

# 全局配置 - 终端宽度固定，彻底解决错位
CHART_WIDTH = 68
CHART_HEIGHT = 14

def req(api, params=None, **kwargs):
    """统一请求接口"""
    try:
        base_url = "https://api.kaifa96.com/api"
        payload = kwargs.copy()
        if params:
            payload.update(params)
        response = requests.get(f"{base_url}/{api}", params=payload, timeout=8)
        return response.json() if response.status_code == 200 else {"code": -1}
    except:
        return {"code": -1}

def parse_command(cmd):
    """解析命令：CNYUSD GB FOREX CHART"""
    parts = cmd.strip().upper().split()
    code = parts[0] if len(parts) > 0 else "EURUSD"
    region = parts[1] if len(parts) > 1 else "GB"
    cat = parts[2] if len(parts) > 2 else "FOREX"
    func = parts[3] if len(parts) > 3 else "CHART"
    return code, region, cat, func

def get_stock_chart(full_command):
    """K线图表 - 修复错位核心"""
    code, region, cat, _ = parse_command(full_command)
    route = {
        "STOCK": "stock", "FUTURE": "future", "FOREX": "forex",
        "INDICES": "indices", "FUND": "fund", "CRYPTO": "crypto"
    }.get(cat, "forex")

    j = req(f"{route}/kline", region=region, code=code, kType=8, limit=40)
    data = j.get("data")
    if not data:
        return "[red]No Kline Data[/red]"

    closes = []
    for item in data:
        try:
            if isinstance(item, dict):
                closes.append(float(item.get("c", 0)))
            else:
                closes.append(float(item[4]))
        except:
            continue

    if len(closes) < 5:
        return "[red]Insufficient Data[/red]"

    # 固定尺寸 = 永不错位
    plt.clear_figure()
    plt.plot_size(CHART_WIDTH, CHART_HEIGHT)
    plt.plot(closes, color="green", marker="dot")
    plt.title(f"{code} {cat} DAILY")
    plt.axes(False)
    plt.grid(False)
    return plt.build()

def get_description(full_command):
    """基础信息"""
    code, region, cat, _ = parse_command(full_command)
    return f"[yellow]{code} | {cat} | {region}[/yellow]"

def show_help():
    """帮助菜单"""
    return """
[blue]MARKET KEYS[/blue]
F2: GOVT    F3: CORP    F8: EQUITY    F11: CRYPTO

[green]FUNCTIONS[/green]
DES: Info    GP: Chart    CN: News
[white]Example: CNYUSD GB FOREX CHART[/white]
"""

def render_screen(command_input):
    """主界面渲染"""
    console.clear()
    now = datetime.now().strftime("%H:%M:%S")
    title = Text(f"BLOOMBERG TERMINAL FREE | Ker ZJZ Global Economic {now}", justify="left")
    
    top_right = ""
    if command_input.strip():
        top_right = f"COMMAND {command_input}"
    
    console.print(Panel(title, style="white"))
    console.print(show_help())

    if "CHART" in command_input.upper():
        chart = get_stock_chart(command_input)
        console.print(chart)
    elif "DES" in command_input.upper():
        console.print(get_description(command_input))

    # 固定命令行框
    console.print(Panel("COMMAND LINE > Type ticker or command...", style="blue", height=3))

def main():
    """主循环"""
    while True:
        console.clear()
        render_screen("")
        cmd = console.input("\033[92mINPUT > \033[0m")
        if cmd.upper() in ["EXIT", "Q"]:
            break
        render_screen(cmd)
        console.input("\n[yellow]Press ENTER to continue...[/yellow]")

if __name__ == "__main__":
    main()