# -*- coding: utf-8 -*-
import requests
import plotext as plt
from rich.table import Table
from datetime import datetime

# ==================== 固定配置 ====================
BASE_URL = "https://api.itick.org"
TOKEN = "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
HEADERS = {
    "accept": "application/json",
    "token": TOKEN
}

# ==================== 工具：时间戳格式化 ====================
def format_time(ts):
    try:
        return datetime.fromtimestamp(int(ts)/1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)

# ==================== 核心：完美解析 代码 地区 功能 ====================
def parse_command(full_command):
    parts = full_command.strip().upper().split()
    
    code   = "AAPL"
    region = "US"
    func   = "DES"

    if len(parts) == 2:
        code, func       = parts[0], parts[1]
    elif len(parts) >= 3:
        code, region, func = parts[0], parts[1], parts[2]

    # 自动兼容 A股
    if code.isdigit():
        if len(code) == 5:
            region = "HK"
        elif code.startswith("6"):
            region = "SH"
        else:
            region = "SZ"

    return code, region, func

# ==================== 统一请求 ====================
def req(path, **kw):
    try:
        return requests.get(f"{BASE_URL}/{path}", headers=HEADERS, params=kw, timeout=8).json()
    except:
        return {"code":-1}

# ==================== 主接口：全功能全地区 ====================
def get_stock_quote(full_command):
    code, region, func = parse_command(full_command)

    # ------------------------------
    # DES / INFO
    # ------------------------------
    if func in ("DES", "INFO"):
        d = req("stock/info", type="stock", region=region, code=code)
        if d.get("code") !=0: return "[red]无数据[/red]"
        dt = d["data"]
        t = Table(title=f"{dt.get('n')} [{code} {region}]", expand=True)
        t.add_column("字段", style="cyan")
        t.add_column("内容", style="green")
        t.add_row("代码", dt.get("c",""))
        t.add_row("名称", dt.get("n",""))
        t.add_row("地区", region)
        t.add_row("交易所", dt.get("e",""))
        t.add_row("行业", dt.get("i",""))
        t.add_row("市值", str(dt.get("mcb","")))
        t.add_row("PE", str(dt.get("pet","")))
        return t

    # ------------------------------
    # QUOTE 实时报价
    # ------------------------------
    if func == "QUOTE":
        d = req("stock/quote", region=region, code=code)
        if d.get("code") !=0: return "[red]QUOTE 失败[/red]"
        dt = d["data"]
        t = Table(title=f"{code} {region} 实时报价")
        t.add_column("指标"), t.add_column("数值")
        t.add_row("最新", str(dt.get("ld")))
        t.add_row("开盘", str(dt.get("o")))
        t.add_row("最高", str(dt.get("h")))
        t.add_row("最低", str(dt.get("l")))
        t.add_row("涨跌", str(dt.get("ch")))
        t.add_row("涨幅%", str(dt.get("chp")))
        t.add_row("时间", format_time(dt.get("t",0)))
        return t

    # ------------------------------
    # TICK 实时成交
    # ------------------------------
    if func == "TICK":
        d = req("stock/tick", region=region, code=code)
        if d.get("code") !=0: return "[red]TICK 失败[/red]"
        dt = d["data"]
        return f"[green]{code} {region} TICK[/green]\n价格: {dt.get('ld')} | 量: {dt.get('v')} | 时间: {format_time(dt.get('t'))}"

    # ------------------------------
    # DEPTH 盘口
    # ------------------------------
    if func == "DEPTH":
        d = req("stock/depth", region=region, code=code)
        if d.get("code") !=0: return "[red]DEPTH 失败[/red]"
        dt = d["data"]
        t = Table(title=f"{code} {region} 五档盘口")
        t.add_column("档","买价","买量","卖价","卖量")
        for i in range(5):
            b = dt["b"][i] if i<len(dt["b"]) else {"p":"","v":""}
            a = dt["a"][i] if i<len(dt["a"]) else {"p":"","v":""}
            t.add_row(str(i+1), str(b["p"]), str(b["v"]), str(a["p"]), str(a["v"]))
        t.caption = f"更新: {format_time(dt.get('t'))}"
        return t

    return "[red]不支持[/red]"

# ==================== K线 CHART ====================
def get_stock_chart(full_command):
    code, region, _ = parse_command(full_command)
    d = req("stock/kline", region=region, code=code, kType=8, limit=60)
    if d.get("code") !=0 or not d.get("data"): return "[red]无K线[/red]"
    closes = [float(x[4]) for x in d["data"]]
    plt.clear_figure()
    plt.plot(closes, label="Close")
    plt.title(f"{code} {region}")
    return plt.build()