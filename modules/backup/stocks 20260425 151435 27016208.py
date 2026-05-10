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
        return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "未知时间"

# ==================== 核心解析：代码 地区 功能 ====================
def parse_command(full_command):
    parts = full_command.strip().upper().split()
    code = "AAPL"
    region = "US"
    func = "DES"

    if len(parts) == 2:
        code, func = parts
    elif len(parts) >= 3:
        code, region, func = parts[0], parts[1], parts[2]

    # A股自动判断
    if code.isdigit():
        if len(code) == 5:
            region = "HK"
        elif code.startswith("6"):
            region = "SH"
        else:
            region = "SZ"
    return code, region, func

# ==================== 安全请求：永不崩溃 ====================
def req(path, **kw):
    try:
        res = requests.get(f"{BASE_URL}/{path}", headers=HEADERS, params=kw, timeout=8)
        data = res.json()
        if not isinstance(data, dict):
            return {"code": -1, "data": None}
        return data
    except:
        return {"code": -1, "data": None}

# ==================== 主查询接口 ====================
def get_stock_quote(full_command):
    code, region, func = parse_command(full_command)

    # DES / INFO
    if func in ("DES", "INFO"):
        d = req("stock/info", type="stock", region=region, code=code)
        data = d.get("data")
        if not data:
            return "[red]无资料数据[/red]"
        t = Table(title=f"{data.get('n', '未知')} [{code} {region}]", expand=True)
        t.add_column("字段", style="cyan")
        t.add_column("内容", style="green")
        t.add_row("代码", data.get("c", ""))
        t.add_row("名称", data.get("n", ""))
        t.add_row("地区", region)
        t.add_row("交易所", data.get("e", ""))
        t.add_row("行业", data.get("i", ""))
        t.add_row("市值", str(data.get("mcb", "")))
        t.add_row("PE", str(data.get("pet", "")))
        return t

    # QUOTE
    if func == "QUOTE":
        d = req("stock/quote", region=region, code=code)
        data = d.get("data")
        if not data:
            return "[red]无报价数据[/red]"
        t = Table(title=f"{code} {region} 实时报价")
        t.add_column("指标")
        t.add_column("数值")
        t.add_row("最新", str(data.get("ld", "")))
        t.add_row("开盘", str(data.get("o", "")))
        t.add_row("最高", str(data.get("h", "")))
        t.add_row("最低", str(data.get("l", "")))
        t.add_row("涨跌", str(data.get("ch", "")))
        t.add_row("涨幅%", str(data.get("chp", "")))
        t.add_row("时间", format_time(data.get("t", 0)))
        return t

    # TICK
    if func == "TICK":
        d = req("stock/tick", region=region, code=code)
        data = d.get("data")
        if not data:
            return "[red]无成交数据[/red]"
        price = data.get("ld", "N/A")
        vol = data.get("v", "N/A")
        time = format_time(data.get("t", 0))
        return f"[green]{code} {region} TICK[/green]\n价格: {price} | 量: {vol} | 时间: {time}"

    # DEPTH
    if func == "DEPTH":
        d = req("stock/depth", region=region, code=code)
        data = d.get("data")
        if not data:
            return "[red]无盘口数据[/red]"
        t = Table(title=f"{code} {region} 五档盘口")
        t.add_column("档", "买价", "买量", "卖价", "卖量")
        for i in range(5):
            b = data.get("b", [])[i] if i < len(data.get("b", [])) else {"p": "", "v": ""}
            a = data.get("a", [])[i] if i < len(data.get("a", [])) else {"p": "", "v": ""}
            t.add_row(str(i+1), str(b["p"]), str(b["v"]), str(a["p"]), str(a["v"]))
        t.caption = f"更新: {format_time(data.get('t', 0))}"
        return t

    return "[red]不支持的命令[/red]"

# ==================== K线图表 ====================
def get_stock_chart(full_command):
    code, region, _ = parse_command(full_command)
    d = req("stock/kline", region=region, code=code, kType=8, limit=60)
    data = d.get("data")
    if not data:
        return "[red]无K线数据[/red]"
    try:
        closes = [float(x[4]) for x in data if len(x) >= 5]
    except:
        return "[red]K线数据异常[/red]"
    plt.clear_figure()
    plt.plot(closes, label="Close")
    plt.title(f"{code} {region}")
    return plt.build()