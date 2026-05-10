# -*- coding: utf-8 -*-
import requests
import plotext as plt
from rich.table import Table
from datetime import datetime

# ==================== 配置 ====================
BASE_URL = "https://api.itick.org"
TOKEN = "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
HEADERS = {
    "accept": "application/json",
    "token": TOKEN
}

# ==================== 工具：时间戳转日期 ====================
def format_timestamp(ts: int) -> str:
    """把毫秒级时间戳转成 2025-01-01 12:00:00"""
    if not ts:
        return "N/A"
    try:
        # 时间戳是毫秒，所以除以1000
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)

# ==================== 命令解析（兼容你的main） ====================
def parse_command(full_command):
    parts = full_command.strip().upper().split()
    code = "AAPL"
    func = "DES"

    if len(parts) >= 1:
        code = parts[0]
    if len(parts) >= 2:
        func = parts[1]
    
    # 自动判断市场
    region = "US"
    if code.isdigit():
        if code.startswith("6"):
            region = "SH"
        else:
            region = "SZ"
    return code, region, func

# ==================== 统一请求 ====================
def req(path, **kwargs):
    try:
        resp = requests.get(f"{BASE_URL}/{path}", headers=HEADERS, params=kwargs, timeout=10)
        return resp.json()
    except:
        return {"code": -1}

# ==================== 主函数：兼容main，支持所有API ====================
def get_stock_quote(full_command):
    code, region, func = parse_command(full_command)

    # --------------------
    # DES / INFO 完整资料
    # --------------------
    if func in ["DES", "INFO"]:
        j = req("stock/info", type="stock", region=region, code=code)
        if j.get("code") != 0:
            return "[red]无数据[/red]"
        d = j["data"]
        table = Table(title=f"{d.get('n')} | {code}", expand=True)
        table.add_column("字段", style="cyan")
        table.add_column("内容", style="green")
        table.add_row("代码", d.get("c", ""))
        table.add_row("名称", d.get("n", ""))
        table.add_row("交易所", d.get("e", ""))
        table.add_row("行业", d.get("i", ""))
        table.add_row("板块", d.get("s", ""))
        table.add_row("总市值", str(d.get("mcb", "")))
        table.add_row("市盈率", str(d.get("pet", "")))
        table.add_row("货币", d.get("fcc", ""))
        table.add_row("官网", d.get("wu", ""))
        return table

    # --------------------
    # QUOTE 实时报价
    # --------------------
    if func == "QUOTE":
        j = req("stock/quote", region=region, code=code)
        if j.get("code") != 0:
            return "[red]错误[/red]"
        d = j["data"]
        table = Table(title=f"{code} 实时报价")
        table.add_column("指标")
        table.add_column("数值")
        table.add_row("最新", str(d.get("ld")))
        table.add_row("开盘", str(d.get("o")))
        table.add_row("最高", str(d.get("h")))
        table.add_row("最低", str(d.get("l")))
        table.add_row("涨跌", str(d.get("ch")))
        table.add_row("涨幅%", str(d.get("chp")))
        table.add_row("时间", format_timestamp(d.get("t")))
        return table

    # --------------------
    # TICK 实时成交（已格式化时间戳）
    # --------------------
    if func == "TICK":
        j = req("stock/tick", region=region, code=code)
        if j.get("code") != 0:
            return "[red]错误[/red]"
        d = j["data"]
        price = d.get("ld", "N/A")
        volume = d.get("v", "N/A")
        time_str = format_timestamp(d.get("t"))
        return f"[green]{code} 实时成交[/green]\n价格: {price} | 成交量: {volume} | 时间: {time_str}"

    # --------------------
    # DEPTH 盘口深度
    # --------------------
    if func == "DEPTH":
        j = req("stock/depth", region=region, code=code)
        if j.get("code") != 0:
            return "[red]错误[/red]"
        d = j["data"]
        table = Table(title=f"{code} 五档盘口")
        table.add_column("档", justify="center")
        table.add_column("买价", justify="right")
        table.add_column("买量", justify="right")
        table.add_column("卖价", justify="right")
        table.add_column("卖量", justify="right")
        for i in range(5):
            b = d["b"][i] if i < len(d["b"]) else {"p": "", "v": ""}
            a = d["a"][i] if i < len(d["a"]) else {"p": "", "v": ""}
            table.add_row(str(i+1), str(b["p"]), str(b["v"]), str(a["p"]), str(a["v"]))
        table.caption = f"更新时间: {format_timestamp(d.get('t'))}"
        return table

    return "[red]不支持的命令[/red]"

# ==================== K线图表（完全兼容原来的CHART） ====================
def get_stock_chart(full_command):
    code, region, _ = parse_command(full_command)
    j = req("stock/kline", region=region, code=code, kType=8, limit=60)
    if j.get("code") != 0 or not j.get("data"):
        return "[red]无K线数据[/red]"
    closes = [float(k[4]) for k in j["data"] if len(k) >= 5]
    plt.clear_figure()
    plt.theme("dark")
    plt.plot(closes, label="收盘价")
    plt.title(f"{code} 日线图")
    return plt.build()