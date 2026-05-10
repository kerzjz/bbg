import requests
import plotext as plt
from rich.table import Table
from datetime import datetime
import re
import json

# ==================== 免费平替配置 ====================
# 股票/基金/指数/港股/美股  -> 新浪财经 + 腾讯财经
# 期货                     -> AkShare
# 外汇                     -> 新浪财经裸货币对接口 (USDCNY/HKDCNY/EURUSD...)
# 加密货币                 -> AkShare + CoinGecko
# =====================================================

try:
    import akshare as ak
    import pandas as pd
    AKSHARE_OK = True
except ImportError:
    AKSHARE_OK = False


# ==================== 外汇映射（裸货币对，不带 fx_s 前缀）====================
FX_SINA_MAP = {
    # 兑人民币
    "USDCNY": "USDCNY", "EURCNY": "EURCNY", "GBPCNY": "GBPCNY",
    "JPYCNY": "JPYCNY", "HKDCNY": "HKDCNY", "AUDCNY": "AUDCNY",
    "CADCNY": "CADCNY", "SGDCNY": "SGDCNY", "CHFCNY": "CHFCNY",
    "NZDCNY": "NZDCNY", "KRWCNY": "KRWCNY", "RUBCNY": "RUBCNY",
    "THBCNY": "THBCNY",
    # 主要交叉盘
    "EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "USDJPY": "USDJPY",
    "AUDUSD": "AUDUSD", "USDCAD": "USDCAD", "USDCHF": "USDCHF",
    "NZDUSD": "NZDUSD", "EURGBP": "EURGBP", "EURJPY": "EURJPY",
    "GBPJPY": "GBPJPY", "AUDJPY": "AUDJPY", "CADJPY": "CADJPY",
    "CHFJPY": "CHFJPY", "EURCHF": "EURCHF", "GBPCHF": "GBPCHF",
    "EURAUD": "EURAUD", "GBPAUD": "GBPAUD", "EURCAD": "EURCAD",
    "GBPCAD": "GBPCAD", "AUDCAD": "AUDCAD", "AUDCHF": "AUDCHF",
    "NZDJPY": "NZDJPY", "NZDCAD": "NZDCAD", "NZDCHF": "NZDCHF",
    "EURNZD": "EURNZD", "GBPNZD": "GBPNZD", "AUDNZD": "AUDNZD",
}


def format_time(ts):
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
        return str(ts)
    except:
        return "N/A"


def parse_command(full_command):
    safe_cmd = ""
    for ch in full_command:
        if ch.isalnum() or ch.isspace():
            safe_cmd += ch
    parts = safe_cmd.strip().upper().split()

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

    valid_funcs = {"DES","INFO","QUOTE","TICK","DEPTH","CHART","GP","HOLIDAY"}
    valid_regions = {"US","SH","SZ","HK","SG","JP","CN","GB","BA"}
    valid_cates = {"stock","future","forex","indices","fund","crypto"}

    func = func if func in valid_funcs else "DES"
    region = region if region in valid_regions else "US"
    category = category if category in valid_cates else "stock"

    return code, region, category.lower(), func


# ==================== 底层数据接口 ====================

def _sina_symbol(code, region, category):
    if category in ("stock", "indices", "fund"):
        if region in ("SH", "CN"):
            return f"sh{code}"
        elif region == "SZ":
            return f"sz{code}"
        elif region == "HK":
            return f"hk{code}"
        elif region == "US":
            return f"gb_{code.lower()}"
    elif category == "future":
        return f"{code}"
    return f"sh{code}"


def _fx_symbol(code, region):
    """生成新浪外汇接口用的裸货币对代码"""
    pair = f"{code}{region}".upper()
    if pair in FX_SINA_MAP:
        return FX_SINA_MAP[pair]

    # region 是人民币/中国 → 查外币兑人民币
    if region.upper() in ("CN", "SH", "SZ", "CNY"):
        return f"{code.upper()}CNY"

    # code 是人民币 → 反向输入，同样映射为外币兑人民币
    if code.upper() in ("CNY", "CN"):
        return f"{region.upper()}CNY"

    # 其他交叉盘
    return f"{code.upper()}{region.upper()}"


def _fetch_sina_quote(symbol):
    url = f"http://hq.sinajs.cn/list={symbol}"
    try:
        r = requests.get(url, timeout=10, headers={"Referer": "https://finance.sina.com.cn"})
        r.encoding = 'gb2312'
        text = r.text.strip()
        if not text:
            return None
        m = re.search(r'var hq_str_[^=]+="([^"]*)"', text)
        if not m:
            return None
        content = m.group(1)
        if not content:
            return None
        return content.split(',')
    except Exception:
        return None


def _parse_a_stock(parts):
    if len(parts) < 33:
        return None
    try:
        last = float(parts[3])
        yc = float(parts[2])
        ch = round(last - yc, 2)
        chp = round(ch / yc * 100, 2) if yc != 0 else 0
    except:
        ch, chp = "", ""
    return {
        "n": parts[0],
        "o": parts[1],
        "h": parts[4],
        "l": parts[5],
        "ld": parts[3],
        "ch": str(ch),
        "chp": f"{chp}%",
        "v": parts[8],
        "tu": parts[9],
        "t": f"{parts[30]} {parts[31]}" if len(parts) > 31 else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "b": [
            {"p": parts[11], "v": parts[10]},
            {"p": parts[13], "v": parts[12]},
            {"p": parts[15], "v": parts[14]},
            {"p": parts[17], "v": parts[16]},
            {"p": parts[19], "v": parts[18]},
        ],
        "a": [
            {"p": parts[21], "v": parts[20]},
            {"p": parts[23], "v": parts[22]},
            {"p": parts[25], "v": parts[24]},
            {"p": parts[27], "v": parts[26]},
            {"p": parts[29], "v": parts[28]},
        ]
    }


def _parse_hk_stock(parts):
    if len(parts) < 7:
        return None
    return {
        "n": parts[0],
        "ld": parts[1],
        "ch": parts[2],
        "chp": f"{parts[3]}%" if parts[3] else "",
        "o": parts[4] if len(parts) > 4 else "",
        "h": parts[5] if len(parts) > 5 else "",
        "l": parts[6] if len(parts) > 6 else "",
        "v": parts[9] if len(parts) > 9 else "",
        "tu": parts[10] if len(parts) > 10 else "",
        "t": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "b": [], "a": []
    }


def _parse_us_stock(parts):
    if len(parts) < 6:
        return None
    return {
        "n": parts[0],
        "ld": parts[1],
        "ch": parts[2],
        "chp": f"{parts[3]}%" if parts[3] else "",
        "o": parts[4],
        "h": parts[5],
        "l": parts[6] if len(parts) > 6 else "",
        "v": parts[9] if len(parts) > 9 else "",
        "tu": parts[10] if len(parts) > 10 else "",
        "t": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "b": [], "a": []
    }


def _parse_fx(parts):
    """
    新浪外汇接口返回11个字段 [^65^]:
    [0]代码, [1]时间, [2]最新/买价, [3]卖价, [4]最高, [5]成交量,
    [6]?, [7]?, [8]最低, [9]昨收, [10]名称
    示例: USDCNY,15:48:29,6.2313,6.2316,6.2452,188,6.2459,6.2459,6.2271,6.2313,美元人民币
    """
    if len(parts) < 10:
        return None
    try:
        last = float(parts[2])
        yc = float(parts[9]) if len(parts) > 9 else last
        ch = round(last - yc, 4)
        chp = round(ch / yc * 100, 2) if yc != 0 else 0
    except:
        ch, chp = 0, 0

    return {
        "n": parts[10] if len(parts) > 10 and parts[10] else parts[0],
        "ld": parts[2],
        "o": parts[9] if len(parts) > 9 else parts[2],
        "h": parts[4] if len(parts) > 4 else "",
        "l": parts[8] if len(parts) > 8 else "",
        "ch": str(ch),
        "chp": f"{chp}%",
        "v": parts[5] if len(parts) > 5 else "N/A",
        "t": parts[1] if len(parts) > 1 else datetime.now().strftime("%H:%M:%S"),
        "b": [{"p": parts[2] if len(parts) > 2 else "", "v": "N/A"}],
        "a": [{"p": parts[3] if len(parts) > 3 else "", "v": "N/A"}],
    }


def _fetch_kline_tencent(code, region, limit=60):
    mapping = {"SH": "sh", "SZ": "sz", "HK": "hk", "US": "us", "CN": "sh"}
    prefix = mapping.get(region, "sh")
    sc = f"{prefix}{code}"
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sc},day,,,{limit},qfq"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        json_data = r.json()
        stock_data = json_data.get("data", {}).get(sc, {})
        klines = stock_data.get("qfqday") or stock_data.get("day") or []
        result = []
        for item in klines:
            if isinstance(item, list) and len(item) >= 5:
                ts = int(datetime.strptime(item[0], "%Y-%m-%d").timestamp() * 1000)
                result.append({
                    "t": ts,
                    "o": item[1],
                    "c": item[2],
                    "l": item[3],
                    "h": item[4],
                    "v": item[5] if len(item) > 5 else "0"
                })
        return result
    except Exception:
        return None


def _fetch_futures_kline_sina(code, limit=60):
    url = (f"https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
           f"var _{code}=/InnerFuturesNewService.getDailyKLine?symbol={code}")
    try:
        r = requests.get(url, timeout=10)
        m = re.search(r'\((\[.*?\])\)', r.text)
        if not m:
            return None
        data = json.loads(m.group(1))
        result = []
        for item in data[-limit:]:
            dt = datetime.strptime(item[0], "%Y-%m-%d")
            result.append({
                "t": int(dt.timestamp() * 1000),
                "o": item[1],
                "h": item[2],
                "l": item[3],
                "c": item[4],
                "v": item[5]
            })
        return result
    except Exception:
        return None


def _crypto_kline_coingecko(code, limit=60):
    symbol_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "LTC": "litecoin",
        "BCH": "bitcoin-cash", "XRP": "ripple", "EOS": "eos",
        "DOT": "polkadot", "ADA": "cardano", "LINK": "chainlink",
        "SOL": "solana", "DOGE": "dogecoin", "AVAX": "avalanche-2"
    }
    coin_id = symbol_map.get(code.upper(), code.lower())
    url = (f"https://api.coingecko.com/api/v3/coins/{coin_id}/"
           f"market_chart?vs_currency=usd&days={limit}")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        prices = r.json().get("prices", [])
        if not prices:
            return None
        result = []
        for ts, price in prices:
            result.append({
                "t": int(ts),
                "o": str(price),
                "c": str(price),
                "h": str(price),
                "l": str(price),
                "v": "0"
            })
        return result
    except Exception:
        return None


def req(path, **kw):
    code = kw.get("code", "")
    region = kw.get("region", "US")
    cat = kw.get("type", "stock").lower()

    if not cat or cat == "stock":
        if path.startswith("future/"):
            cat = "future"
        elif path.startswith("forex/"):
            cat = "forex"
        elif path.startswith("crypto/"):
            cat = "crypto"
        elif path.startswith("indices/"):
            cat = "indices"
        elif path.startswith("fund/"):
            cat = "fund"

    # ==================== 期货 ====================
    if cat == "future":
        if not AKSHARE_OK:
            return {"code": -1, "data": None}
        try:
            if "kline" in path:
                data = _fetch_futures_kline_sina(code, kw.get("limit", 60))
                if data:
                    return {"code": 0, "data": data}
                return {"code": -1, "data": None}

            if region in ("SH", "SZ", "CN"):
                df = ak.futures_zh_spot(symbol=code, market="CF", adjust='0')
                if df.empty:
                    return {"code": -1, "data": None}
                row = df.iloc[0]
                data = {
                    "n": str(row.get("symbol", code)),
                    "ld": str(row.get("last", row.get("trade", ""))),
                    "o": str(row.get("open", "")),
                    "h": str(row.get("high", "")),
                    "l": str(row.get("low", "")),
                    "ch": str(row.get("change", "")),
                    "chp": f"{row.get('changepercent', '')}%" if pd.notna(row.get('changepercent')) else "",
                    "v": str(row.get("volume", "")),
                    "t": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "b": [], "a": []
                }
                return {"code": 0, "data": data}
            else:
                df = ak.futures_foreign_commodity_realtime(symbol=code)
                if df.empty:
                    return {"code": -1, "data": None}
                row = df.iloc[0]
                data = {
                    "n": str(row.get("名称", code)),
                    "ld": str(row.get("最新价", "")),
                    "o": str(row.get("开盘价", "")),
                    "h": str(row.get("最高价", "")),
                    "l": str(row.get("最低价", "")),
                    "ch": str(row.get("涨跌额", "")),
                    "chp": f"{row.get('涨跌幅', '')}%" if pd.notna(row.get('涨跌幅')) else "",
                    "v": str(row.get("持仓量", "")),
                    "t": f"{row.get('日期', '')} {row.get('行情时间', '')}",
                    "b": [], "a": []
                }
                return {"code": 0, "data": data}
        except Exception:
            return {"code": -1, "data": None}

    # ==================== 外汇（修复版：裸货币对接口）====================
    elif cat == "forex":
        symbol = _fx_symbol(code, region)
        parts = _fetch_sina_quote(symbol)
        if parts is None:
            return {"code": -1, "data": None}
        data = _parse_fx(parts)
        if data is None:
            return {"code": -1, "data": None}
        if "kline" in path:
            return {"code": -1, "data": None}
        return {"code": 0, "data": data}

    # ==================== 加密货币 ====================
    elif cat == "crypto":
        if "kline" in path:
            data = _crypto_kline_coingecko(code, kw.get("limit", 60))
            if data:
                return {"code": 0, "data": data}
            return {"code": -1, "data": None}

        if not AKSHARE_OK:
            return {"code": -1, "data": None}
        try:
            df = ak.crypto_js_spot()
            if df.empty:
                return {"code": -1, "data": None}
            mask = df["交易品种"].str.contains(code, case=False, na=False)
            matched = df[mask]
            if matched.empty:
                return {"code": -1, "data": None}
            row = matched.iloc[0]
            data = {
                "n": str(row.get("交易品种", code)),
                "ld": str(row.get("最近报价", "")),
                "o": "",
                "h": str(row.get("24小时最高", "")),
                "l": str(row.get("24小时最低", "")),
                "ch": str(row.get("涨跌额", "")),
                "chp": f"{row.get('涨跌幅', '')}%" if pd.notna(row.get('涨跌幅')) else "",
                "v": str(row.get("24小时成交量", "")),
                "t": str(row.get("更新时间", "")),
                "b": [], "a": []
            }
            return {"code": 0, "data": data}
        except Exception:
            return {"code": -1, "data": None}

    # ==================== 股票/基金/指数 ====================
    symbol = _sina_symbol(code, region, cat)

    if "quote" in path or "tick" in path or "depth" in path:
        parts = _fetch_sina_quote(symbol)
        if parts is None:
            return {"code": -1, "data": None}

        if region in ("SH", "SZ", "CN") and cat in ("stock", "indices", "fund"):
            data = _parse_a_stock(parts)
        elif region == "HK":
            data = _parse_hk_stock(parts)
        elif region == "US":
            data = _parse_us_stock(parts)
        else:
            data = _parse_a_stock(parts)

        return {"code": 0, "data": data}

    elif "kline" in path:
        limit = kw.get("limit", 60)
        data = _fetch_kline_tencent(code, region, limit)
        if data:
            return {"code": 0, "data": data}
        return {"code": -1, "data": None}

    elif "symbol/list" in path or "info" in path:
        parts = _fetch_sina_quote(symbol)
        name = parts[0] if parts else "Unknown"
        return {"code": 0, "data": [{"c": code, "n": name, "t": cat, "e": region}]}

    elif "holidays" in path:
        return {"code": 0, "data": []}

    return {"code": -1, "data": None}


# ==================== 上层逻辑完全不变 ====================

def get_stock_quote(full_command):
    try:
        code, region, cat, func = parse_command(full_command)

        if func == "HOLIDAY":
            return f"[yellow]Holiday data not available in free tier[/yellow]"

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
    except Exception as e:
        return f"[red]Command error: {e}[/red]"


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