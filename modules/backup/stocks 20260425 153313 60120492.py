from utils import req
import plotext as plt

def get_stock_quote(full_command):
    parts = full_command.upper().split()
    cmd = parts[0] if len(parts) > 0 else "EURUSD"
    region = parts[1] if len(parts) > 1 else "GB"
    cat = parts[2] if len(parts) > 2 else "FOREX"

    route = {
        "STOCK": "stock",
        "FUTURE": "future",
        "FOREX": "forex",
        "INDICES": "indices",
        "FUND": "fund",
        "CRYPTO": "crypto"
    }.get(cat, "forex")

    j = req(f"{route}/quote", region=region, code=cmd)
    data = j.get("data")
    if not data:
        return "[red]No Data[/red]"

    res = f"[white]{data.get('code', cmd)}[/white] | "
    res += f"[yellow]{data.get('name', '')}[/yellow]\n"
    res += f"Price: [green]{data.get('price', 'N/A')}[/green]\n"
    res += f"Change: [cyan]{data.get('change', 'N/A')}[/cyan] "
    res += f"[blue]{data.get('change_pct', 'N/A')}[/blue]"
    return res

def get_stock_chart(full_command):
    parts = full_command.upper().split()
    cmd = parts[0] if len(parts) > 0 else "EURUSD"
    region = parts[1] if len(parts) > 1 else "GB"
    cat = parts[2] if len(parts) > 2 else "FOREX"

    route = {
        "STOCK": "stock",
        "FUTURE": "future",
        "FOREX": "forex",
        "INDICES": "indices",
        "FUND": "fund",
        "CRYPTO": "crypto"
    }.get(cat, "forex")

    j = req(f"{route}/kline", region=region, code=cmd, kType=8, limit=40)
    data = j.get("data")
    if not data:
        return "[red]No KLINE DATA[/red]"

    closes = []
    for item in data:
        try:
            if isinstance(item, dict):
                closes.append(float(item.get("c", 0)))
            else:
                closes.append(float(item[4]))
        except:
            continue

    if len(closes) < 3:
        return "[red]NO CLOSE DATA[/red]"

    # ==================== 修复错位：固定宽度 ====================
    plt.clear_figure()
    plt.theme('classic')
    plt.plot_size(66, 14)
    plt.plot(closes, color="green", label="CLOSE")
    plt.title(f"{cmd} {cat} DAILY")
    plt.xlabel("")
    plt.ylabel("")
    plt.grid(False)
    return plt.build()

def get_stock_news(full_command):
    parts = full_command.upper().split()
    cmd = parts[0] if len(parts) > 0 else "EURUSD"
    region = parts[1] if len(parts) > 1 else "GB"
    cat = parts[2] if len(parts) > 2 else "FOREX"

    route = {
        "STOCK": "stock",
        "FUTURE": "future",
        "FOREX": "forex",
        "INDICES": "indices",
        "FUND": "fund",
        "CRYPTO": "crypto"
    }.get(cat, "forex")

    j = req(f"{route}/news", region=region, code=cmd, limit=3)
    data = j.get("data", [])
    if not data:
        return "[red]No News[/red]"

    res = ""
    for idx, item in enumerate(data, 1):
        res += f"[white]{idx}. {item.get('title', '')}[/white]\n"
        res += f"[dim]{item.get('datetime', '')} | {item.get('source', '')}[/dim]\n\n"
    return res