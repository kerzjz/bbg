# -*- coding: utf-8 -*-
import requests
import plotext as plt
from rich.table import Table
from typing import Optional, Dict, Any

# ====================== 全局配置 ======================
BASE_URL = "https://api.itick.org"
TOKEN = "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3255e1ab931339b"
HEADERS = {
    "accept": "application/json",
    "token": TOKEN
}

# ====================== 命令解析器 ======================
def parse_command(full_command: str):
    parts = full_command.strip().upper().split()
    func = "DES"
    if parts and parts[-1] in ["DES", "INFO", "QUOTE", "TICK", "DEPTH", "CHART", "GP"]:
        func = parts[-1]
        data_parts = parts[:-1]
    else:
        data_parts = parts

    code = "AAPL"
    region = "US"
    category = "stock"

    if len(data_parts) >= 1:
        code = data_parts[0]
    if len(data_parts) >= 2:
        region = data_parts[1]
    if len(data_parts) >= 3:
        category = data_parts[2].lower()

    if code.isdigit():
        if code.startswith("6"):
            region = "SH"
        else:
            region = "SZ"
    return code, region, category.lower(), func

# ====================== 统一请求工具 ======================
def api_request(endpoint: str, **kwargs) -> Dict[str, Any]:
    try:
        resp = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers=HEADERS,
            params=kwargs,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}"}

# ====================== 全品类 基础信息 / 报价 / 成交 / 盘口 ======================
def get_stock_quote(full_command: str):
    code, region, cat, func = parse_command(full_command)

    # ==============================================
    # 1. 股票 STOCK —— 全部接口
    # ==============================================
    if cat == "stock":
        if func in ["DES", "INFO"]:
            d = api_request("stock/info", type="stock", region=region, code=code)
            if d.get("code") != 0 or not d.get("data"): return "[red]无股票资料[/red]"
            dt = d["data"]
            tb = Table(title=f"{dt.get('n')} ({code})", expand=True)
            tb.add_column("字段", style="cyan")
            tb.add_column("内容", style="green")
            tb.add_row("代码", dt.get("c", ""))
            tb.add_row("名称", dt.get("n", ""))
            tb.add_row("交易所", dt.get("e", ""))
            tb.add_row("行业", dt.get("i", ""))
            tb.add_row("总市值", str(dt.get("mcb", "")))
            tb.add_row("市盈率", str(dt.get("pet", "")))
            return tb

        if func == "QUOTE":
            d = api_request("stock/quote", region=region, code=code)
            if d.get("code") !=0: return "[red]报价失败[/red]"
            dt = d["data"]
            tb = Table(title=f"{code} 实时报价")
            tb.add_column("指标"), tb.add_column("数值")
            tb.add_row("最新", str(dt.get("ld")))
            tb.add_row("开盘", str(dt.get("o")))
            tb.add_row("最高", str(dt.get("h")))
            tb.add_row("最低", str(dt.get("l")))
            tb.add_row("涨跌", str(dt.get("ch")))
            tb.add_row("涨幅%", str(dt.get("chp")))
            return tb

        if func == "TICK":
            d = api_request("stock/tick", region=region, code=code)
            if d.get("code")!=0: return "[red]成交失败[/red]"
            dt = d["data"]
            return f"[green]STOCK TICK {code}[/green]\n价格: {dt.get('ld')}  成交量: {dt.get('v')}  时间: {dt.get('t')}"

        if func == "DEPTH":
            d = api_request("stock/depth", region=region, code=code)
            if d.get("code")!=0: return "[red]盘口失败[/red]"
            dt = d["data"]
            tb = Table(title=f"{code} 五档盘口")
            tb.add_column("档"), tb.add_column("买价"), tb.add_column("买量"), tb.add_column("卖价"), tb.add_column("卖量")
            for i in range(5):
                b = dt["b"][i] if i < len(dt["b"]) else {"p":"","v":""}
                a = dt["a"][i] if i < len(dt["a"]) else {"p":"","v":""}
                tb.add_row(str(i+1), str(b["p"]), str(b["v"]), str(a["p"]), str(a["v"]))
            return tb

    # ==============================================
    # 2. 期货 FUTURE —— 全部接口
    # ==============================================
    if cat == "future":
        if func in ["INFO","DES"]:
            d = api_request("symbol/list", type="future", region=region, code=code)
            dat = d.get("data",[])
            item = dat[0] if dat else {}
            tb = Table(title=f"期货 {code}")
            tb.add_column("字段"), tb.add_column("值")
            tb.add_row("代码", item.get("c","")), tb.add_row("名称", item.get("n",""))
            return tb
        if func == "QUOTE": return api_request("future/quote", region=region, code=code)
        if func == "TICK": return api_request("future/tick", region=region, code=code)
        if func == "DEPTH": return api_request("future/depth", region=region, code=code)

    # ==============================================
    # 3. 外汇 FOREX —— 全部接口
    # ==============================================
    if cat == "forex":
        if func in ["INFO","DES"]: return api_request("symbol/list", type="forex", code=code)
        if func == "QUOTE": return api_request("forex/quote", region="GB", code=code)
        if func == "TICK": return api_request("forex/tick", region="GB", code=code)
        if func == "DEPTH": return api_request("forex/depth", region="GB", code=code)

    # ==============================================
    # 4. 指数 INDICES —— 全部接口
    # ==============================================
    if cat == "indices":
        if func in ["INFO","DES"]: return api_request("symbol/list", type="indices", code=code)
        if func == "QUOTE": return api_request("indices/quote", region="GB", code=code)
        if func == "TICK": return api_request("indices/tick", region="GB", code=code)
        if func == "DEPTH": return api_request("indices/depth", region="GB", code=code)

    # ==============================================
    # 5. 基金 FUND —— 全部接口
    # ==============================================
    if cat == "fund":
        if func in ["INFO","DES"]: return api_request("symbol/list", type="fund", region=region, code=code)
        if func == "QUOTE": return api_request("fund/quote", region=region, code=code)
        if func == "TICK": return api_request("fund/tick", region=region, code=code)
        if func == "DEPTH": return api_request("fund/depth", region=region, code=code)

    # ==============================================
    # 6. 加密货币 CRYPTO —— 全部接口
    # ==============================================
    if cat == "crypto":
        if func in ["INFO","DES"]: return api_request("symbol/list", type="crypto", code=code)
        if func == "QUOTE": return api_request("crypto/quote", region="BA", code=code)
        if func == "TICK": return api_request("crypto/tick", region="BA", code=code)
        if func == "DEPTH": return api_request("crypto/depth", region="BA", code=code)

    return "[red]命令不支持[/red]"

# ====================== 全品类 K线 ======================
def get_stock_chart(full_command: str):
    code, region, cat, _ = parse_command(full_command)
    route_map = {
        "stock": ("stock/kline", region),
        "future": ("future/kline", region),
        "forex": ("forex/kline", "GB"),
        "indices": ("indices/kline", "GB"),
        "fund": ("fund/kline", region),
        "crypto": ("crypto/kline", "BA")
    }
    if cat not in route_map: return "[red]不支持的K线品种[/red]"
    path, reg = route_map[cat]
    data = api_request(path, region=reg, code=code, kType=8, limit=60)
    if data.get("code")!=0 or not data.get("data"): return "[red]无K线数据[/red]"
    closes = [float(k[4]) for k in data["data"] if len(k)>=5]
    plt.clear_figure()
    plt.theme("dark")
    plt.plot(closes, label="收盘价")
    plt.title(f"{code} {cat.upper()}")
    return plt.build()

# ====================== 批量接口（全部包含！）======================
def get_stock_quotes(codes: str): return api_request("stock/quotes", codes=codes)
def get_stock_ticks(codes: str): return api_request("stock/ticks", codes=codes)
def get_stock_depths(codes: str): return api_request("stock/depths", codes=codes)
def get_stock_klines(codes: str, ktype: int = 8): return api_request("stock/klines", codes=codes, kType=ktype)

def get_future_quotes(codes: str): return api_request("future/quotes", codes=codes)
def get_forex_quotes(codes: str): return api_request("forex/quotes", codes=codes)
def get_indices_quotes(codes: str): return api_request("indices/quotes", codes=codes)
def get_fund_quotes(codes: str): return api_request("fund/quotes", codes=codes)
def get_crypto_quotes(codes: str): return api_request("crypto/quotes", codes=codes)

# ====================== 全品种清单 ======================
def get_symbol_list(type_val: str): return api_request("symbol/list", type=type_val)