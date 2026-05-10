# -*- coding: utf-8 -*-
import requests
import plotext as plt
from rich.table import Table
from datetime import datetime

# ==================== 官方固定配置 ====================
BASE_URL = "https://api.itick.org"
TOKEN = "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
HEADERS = {
    "accept": "application/json",
    "token": TOKEN
}

# ==================== 工具：时间格式化 ====================
def format_time(ts):
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "N/A"

# ==================== 命令解析：代码 地区 品类 功能 ====================
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

    return code, region, category.lower(), func

# ==================== 安全请求 ====================
def req(path, **kw):
    try:
        r = requests.get(f"{BASE_URL}/{path}", headers=HEADERS, params=kw, timeout=10)
        return r.json()
    except Exception:
        return {"code": -1, "data": None}

# ==================== 全品类：DES / INFO / QUOTE / TICK / DEPTH ====================
def get_stock_quote(full_command):
    code, region, cat, func = parse_command(full_command)

    # 品类路由（严格对应官方 API）
    route = {
        "stock": "stock",
        "future": "future",
        "forex": "forex",
        "indices": "indices",
        "fund": "fund",
        "crypto": "crypto"
    }.get(cat, "stock")

    # ------------------------------
    # DES / INFO（产品资料 + 基础信息）
    # ------------------------------
    if func in ("DES", "INFO"):
        j = req("symbol/list", type=cat, region=region, code=code)
        dat = j.get("data", [])
        item = dat[0] if dat else {}
        tbl = Table(title=f"{item.get('n', 'Unknown')} [{code.upper()} {region.upper()} {cat.upper()}]", expand=True)
        tbl.add_column("Field", style="cyan")
        tbl.add_column("Value", style="green")
        tbl.add_row("CODE", item.get("c", ""))
        tbl.add_row("NAME", item.get("n", ""))
        tbl.add_row("TYPE", item.get("t", cat))
        tbl.add_row("EXCHANGE", item.get("e", ""))
        tbl.add_row("REGION", region)
        return tbl

    # ------------------------------
    # QUOTE 实时报价
    # ------------------------------
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

    # ------------------------------
    # TICK 实时成交
    # ------------------------------
    if func == "TICK":
        j = req(f"{route}/tick", region=region, code=code)
        d = j.get("data")
        if not d:
            return "[red]No DATA[/red]"
        return (
            f"[green]{code} {region} {cat} TICK[/green]\n"
            f"LAST: {d.get('ld', 'N/A')}\n"
            f"VOL : {d.get('v', 'N/A')}\n"
            f"TIME: {format_time(d.get('t', ''))}"
        )

    # ------------------------------
    # DEPTH 盘口
    # ------------------------------
    if func == "DEPTH":
        j = req(f"{route}/depth", region=region, code=code)
        d = j.get("data")
        if not d:
            return "[red]No DATA[/red]"
        tbl = Table(title=f"{code} {region} {cat} DEPTH", expand=True)
        tbl.add_column("POS", style="cyan")
        tbl.add_column("BID P", style="green"), tbl.add_column("BID V", style="green")
        tbl.add_column("ASK P", style="red"), tbl.add_column("ASK V", style="red")
        for i in range(5):
            b = d.get("b", [])[i] if i < len(d.get("b", [])) else {"p": "", "v": ""}
            a = d.get("a", [])[i] if i < len(d.get("a", [])) else {"p": "", "v": ""}
            tbl.add_row(str(i+1), str(b.get("p", "")), str(b.get("v", "")), str(a.get("p", "")), str(a.get("v", "")))
        return tbl

    return "[red]INVALID COMMAND[/red]"

# ==================== 全品类 K线 CHART ====================
def get_stock_chart(full_command):
    code, region, cat, _ = parse_command(full_command)
    route = {
        "stock": "stock", "future": "future", "forex": "forex",
        "indices": "indices", "fund": "fund", "crypto": "crypto"
    }.get(cat, "stock")

    j = req(f"{route}/kline", region=region, code=code, kType=8, limit=60)
    data = j.get("data")
    if not data:
        return "[red]No KLINE DATA[/red]"

    closes = []
    for item in data:
        if isinstance(item, dict) and "c" in item:
            closes.append(float(item["c"]))
        elif isinstance(item, (list, tuple)) and len(item) >= 5:
            closes.append(float(item[4]))

    if not closes:
        return "[red]NO CLOSE DATA[/red]"

    plt.clear_figure()
    plt.theme("dark")
    plt.plot(closes, label="CLOSE")
    plt.title(f"{code} {region} {cat} DAILY")
    return plt.build()