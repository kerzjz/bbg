import requests
import plotext as plt
from rich.table import Table
from datetime import datetime

# 你原版配置 完全不动
BASE_URL = "https://api.itick.org"
TOKEN = "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
HEADERS = {
    "accept": "application/json",
    "token": TOKEN
}

def format_time(ts):
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "N/A"

def parse_command(full_command):
    parts = full_command.strip().upper().split()
    code = "AAPL"
    region = "US"
    category = "stock"
    func = "DES"

    if len(parts) >= 4:
        code, region, category, func = parts[0], parts[1], parts[2].lower(), parts[3]
    elif len(parts) == 3:
        code, region, func = parts[0], parts[1], parts[2]
        category = "stock"
    elif len(parts) == 2:
        code, func = parts[0], parts[1]
        category = "stock"
        if code.isdigit():
            region = "SH" if code.startswith("6") else "SZ"
        else:
            region = "US"
    else:
        code = parts[0] if parts else "AAPL"

    # ==================== 合法性校验（只加这个）====================
    valid_func = {"DES","INFO","QUOTE","TICK","DEPTH","CHART","GP","HOLIDAY"}
    valid_region = {"US","SH","SZ","HK","GB","BA"}
    valid_category = {"stock","future","forex","indices","fund","crypto"}

    if func not in valid_func:
        func = "DES"
    if region not in valid_region:
        region = "US"
    if category not in valid_category:
        category = "stock"

    return code, region, category.lower(), func

def req(path, **kw):
    try:
        r = requests.get(f"{BASE_URL}/{path}", headers=HEADERS, params=kw, timeout=10)
        return r.json()
    except Exception:
        return {"code": -1, "data": None}

def get_stock_quote(full_command):
    code, region, cat, func = parse_command(full_command)

    # ==================== HOLIDAY 强制安全拦截：忽略股票，只传地区 ====================
    if func == "HOLIDAY":
        try:
            j = req("symbol/v2/holidays", code=region)
            data = j.get("data", [])
            if not data:
                return "[red]No holiday data[/red]"
            tbl = Table(title=f"{region} Market Holidays", expand=True)
            tbl.add_column("Date", style="cyan")
            tbl.add_column("Name", style="green")
            tbl.add_column("Market", style="yellow")
            tbl.add_column("Time", style="white")
            for item in data:
                tbl.add_row(
                    item.get("d", ""),
                    item.get("v", ""),
                    item.get("r", ""),
                    item.get("t", "")
                )
            return tbl
        except:
            return "[red]Holiday query failed[/red]"

    # ==================== 以下完全是你原版代码，一字未改 ====================
    route = {
        "stock": "stock",
        "future": "future",
        "forex": "forex",
        "indices": "indices",
        "fund": "fund",
        "crypto": "crypto"
    }.get(cat, "stock")

    if func in ("DES", "INFO"):
        j = req("symbol/list", type=cat, region=region, code=code)
        dat = j.get("data", [])
        item = dat[0] if dat else {}
        tbl = Table(title=f"{item.get('n', 'Unknown')} [{code} {region} {cat}]", expand=True)
        tbl.add_column("Field", style="cyan")
        tbl.add_column("Value", style="green")
        tbl.add_row("CODE", item.get("c", ""))
        tbl.add_row("NAME", item.get("n", ""))
        tbl.add_row("TYPE", item.get("t", cat))
        tbl.add_row("EXCHANGE", item.get("e", ""))
        tbl.add_row("REGION", region)
        return tbl

    if func == "QUOTE":
        j = req(f"{route}/quote", region=region, code=code)
        d = j.get("data")
        if not d:
            return "[red]No DATA[/red]"
        tbl = Table(title=f"{code} {region} {cat} QUOTE", expand=True)
        tbl.add_column("FIELD", style="cyan")
        tbl.add_column("VALUE", style="green")
        tbl.add_row("LAST", str(d.get("ld", "")))
        tbl.add_row("OPEN", str(d.get("o", "")))
        tbl.add_row("HIGH", str(d.get("h", "")))
        tbl.add_row("LOW", str(d.get("l", "")))
        tbl.add_row("CHG", str(d.get("ch", "")))
        tbl.add_row("CHG%", str(d.get("chp", "")))
        tbl.add_row("TIME", format_time(d.get("t", "")))
        return tbl

    if func == "TICK":
        j = req(f"{route}/tick", region=region, code=code)
        d = j.get("data")
        if not d:
            return "[red]No DATA[/red]"
        return f"[green]{code} {region} {cat} TICK[/green]\nLAST: {d.get('ld', 'N/A')}\nVOL : {d.get('v', 'N/A')}\nTIME: {format_time(d.get('t', ''))}"

    if func == "DEPTH":
        j = req(f"{route}/depth", region=region, code=code)
        d = j.get("data")
        if not d:
            return "[red]No DATA[/red]"
        tbl = Table(title=f"{code} {region} {cat} DEPTH", expand=True)
        tbl.add_column("POS", style="cyan")
        tbl.add_column("BID P", style="green")
        tbl.add_column("BID V", style="green")
        tbl.add_column("ASK P", style="red")
        tbl.add_column("ASK V", style="red")
        for i in range(5):
            b = d.get("b", [])[i] if i < len(d.get("b", [])) else {"p": "", "v": ""}
            a = d.get("a", [])[i] if i < len(d.get("a", [])) else {"p": "", "v": ""}
            tbl.add_row(str(i+1), str(b.get("p", "")), str(b.get("v", "")), str(a.get("p", "")), str(a.get("v", "")))
        return tbl

    return "[red]INVALID COMMAND[/red]"

# ==================== 你原版K线图 完全不动 ====================
def get_stock_chart(full_command):
    code, region, cat, _ = parse_command(full_command)
    route = {
        "stock": "stock",
        "future": "future",
        "forex": "forex",
        "indices": "indices",
        "fund": "fund",
        "crypto": "crypto"
    }.get(cat, "stock")
    j = req(f"{route}/kline", region=region, code=code, kType=8, limit=60)
    data = j.get("data")
    if not data:
        return "[red]No KLINE DATA[/red]"
    closes = []
    for item in data:
        try:
            closes.append(float(item["c"]))
        except:
            continue
    if len(closes) < 3:
        return "[red]NO CLOSE DATA[/red]"
    plt.clear_figure()
    plt.theme('classic')
    plt.plot_size(55, 13)
    plt.plot(closes, color="green", label="CLOSE")
    plt.title(f"{code} {cat} DAILY")
    plt.xlabel("")
    plt.ylabel("")
    plt.grid(False)
    return plt.build()