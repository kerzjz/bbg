import requests
import plotext as plt
from rich.table import Table
from datetime import datetime, timedelta

# ============ 依赖检查：假期日历 ============
try:
    import exchange_calendars as xcals
    import pandas as pd
    ECAL_AVAILABLE = True
except ImportError:
    ECAL_AVAILABLE = False

# ============ 通用底层请求 ============

def _sina_quote(symbol):
    """新浪行情通用请求，返回逗号分隔列表"""
    try:
        url = f"http://hq.sinajs.cn/list={symbol}"
        r = requests.get(url, timeout=10)
        r.encoding = 'gb2312'
        text = r.text.strip()
        if not text or 'hq_str_' not in text:
            return None
        start = text.find('"') + 1
        end = text.rfind('"')
        if start <= 0 or end <= start:
            return None
        return text[start:end].split(',')
    except Exception:
        return None

def _tencent_quote(symbol):
    """腾讯行情通用请求，返回波浪号分隔列表"""
    try:
        url = f"https://qt.gtimg.cn/q={symbol}"
        r = requests.get(url, timeout=10)
        r.encoding = 'gb2312'
        text = r.text.strip()
        if not text or 'v_' not in text:
            return None
        start = text.find('"') + 1
        end = text.rfind('"')
        if start <= 0 or end <= start:
            return None
        return text[start:end].split('~')
    except Exception:
        return None

def _tencent_kline(code, region, limit=60):
    """腾讯K线（股票/指数通用）"""
    prefix_map = {"SH": "sh", "SZ": "sz", "HK": "hk", "US": "us", "CN": "sh"}
    region = _normalize_region(code, region)
    prefix = prefix_map.get(region, "sh")
    symbol = f"{prefix}{code}"
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=limit * 2)).strftime("%Y-%m-%d")
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param={symbol},day,{start},{end},{limit},qfq")
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("data", {}).get(symbol, {}).get("day", [])
    except Exception:
        return None

def _normalize_region(code, region):
    """CN 自动映射到 SH/SZ"""
    if region == "CN":
        return "SH" if code.startswith("6") else "SZ"
    return region

# ============ 各品类数据请求 ============

def req_stock(code, region):
    prefix_map = {"SH": "sh", "SZ": "sz", "HK": "hk", "US": "us",
                  "SG": "sg", "JP": "jp", "GB": "uk", "CN": "sh"}
    region = _normalize_region(code, region)
    prefix = prefix_map.get(region, "us")
    return _tencent_quote(f"{prefix}{code}")

def req_indices(code, region):
    prefix_map = {"SH": "sh", "SZ": "sz", "HK": "hk", "US": "us", "CN": "sh"}
    region = _normalize_region(code, region)
    prefix = prefix_map.get(region, "sh")
    return _tencent_quote(f"{prefix}{code}")

def req_future(code, region):
    # 自动补 0 表示连续合约（如 IF -> IF0）
    symbol = f"{code}0" if not code[-1].isdigit() else code
    return _sina_quote(symbol)

def req_forex(code, region):
    symbol = f"fx_s{code.lower()}"
    return _sina_quote(symbol)

def req_fund(code, region):
    symbol = f"f_{code}"
    return _sina_quote(symbol)

def req_crypto_ticker(code, region):
    symbol = f"{code.upper()}USDT"
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception:
        return None

def req_crypto_depth(code, region):
    symbol = f"{code.upper()}USDT"
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception:
        return None

def req_crypto_kline(code, region, limit=60):
    symbol = f"{code.upper()}USDT"
    url = (f"https://api.binance.com/api/v3/klines?"
           f"symbol={symbol}&interval=1d&limit={limit}")
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception:
        return None

# ============ 假期接口（本地计算，永不过期） ============

CALENDAR_MAP = {
    "CN": "XSHG", "SH": "XSHG", "SZ": "XSHE",
    "HK": "XHKG", "US": "XNYS",
    "SG": "XSES", "JP": "XJPX", "GB": "XLON", "BA": "XLON"
}

def get_holidays(region):
    if not ECAL_AVAILABLE:
        return ("[red]HOLIDAY requires exchange-calendars. "
                "Install: pip install exchange-calendars pandas[/red]")
    cal_code = CALENDAR_MAP.get(region)
    if not cal_code:
        return f"[red]No holiday calendar for {region}[/red]"
    try:
        cal = xcals.get_calendar(cal_code)
        today = pd.Timestamp.now(tz="UTC").normalize()
        future = today + pd.DateOffset(years=1)
        sessions = cal.sessions_in_range(today, future)
        all_days = pd.date_range(today, future, freq='D', tz="UTC")
        holidays = all_days.difference(sessions)
        holidays = [h for h in holidays if h.dayofweek not in (5, 6)]
        tbl = Table(title=f"{region} Market Holidays (Next 12 Months)", expand=True)
        tbl.add_column("Date", style="cyan")
        tbl.add_column("Name", style="green")
        tbl.add_column("Market", style="yellow")
        tbl.add_column("Trading Time", style="white")
        for h in holidays[:50]:
            tbl.add_row(h.strftime("%Y-%m-%d"), "Exchange Holiday", region, "Closed")
        return tbl
    except Exception as e:
        return f"[red]Calendar error: {e}[/red]"

# ============ 原有工具函数（完全不变） ============

def format_time(ts):
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
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
    valid_regions = {"US","SH","SZ","HK","SG","JP","GB","BA","CN"}
    valid_cates = {"stock","future","forex","indices","fund","crypto"}

    func = func if func in valid_funcs else "DES"
    region = region if region in valid_regions else "US"
    category = category if category in valid_cates else "stock"

    return code, region, category.lower(), func

# ============ 辅助建表函数 ============

def _info_table(title, rows):
    tbl = Table(title=title, expand=True)
    tbl.add_column("Field", style="cyan")
    tbl.add_column("Value", style="green")
    for k, v in rows:
        tbl.add_row(k, str(v))
    return tbl

def _quote_table(title, rows):
    tbl = Table(title=title, expand=True)
    tbl.add_column("FIELD", style="cyan")
    tbl.add_column("VALUE", style="green")
    for k, v in rows:
        tbl.add_row(k, str(v))
    return tbl

# ============ 品类处理函数 ============

def handle_stock(code, region, func):
    fields = req_stock(code, region)
    if not fields:
        return "[red]No DATA (Stock API failed)[/red]"
    if func in ("DES", "INFO"):
        return _info_table(f"{fields[1]} [{code} {region} STOCK]", [
            ("CODE", code), ("NAME", fields[1]), ("TYPE", "stock"),
            ("EXCHANGE", region), ("REGION", region)
        ])
    if func == "QUOTE":
        return _quote_table(f"{code} {region} STOCK QUOTE", [
            ("LAST", fields[3] if len(fields) > 3 else "N/A"),
            ("OPEN", fields[5] if len(fields) > 5 else "N/A"),
            ("HIGH", fields[33] if len(fields) > 33 else "N/A"),
            ("LOW", fields[34] if len(fields) > 34 else "N/A"),
            ("CHG", fields[31] if len(fields) > 31 else "N/A"),
            ("CHG%", fields[32] if len(fields) > 32 else "N/A"),
            ("TIME", fields[30] if len(fields) > 30 else "N/A"),
        ])
    if func == "TICK":
        return (f"[green]{code} {region} STOCK TICK[/green]\n"
                f"LAST: {fields[3] if len(fields) > 3 else 'N/A'}\n"
                f"VOL : {fields[6] if len(fields) > 6 else 'N/A'}\n"
                f"TIME: {fields[30] if len(fields) > 30 else 'N/A'}")
    if func == "DEPTH":
        tbl = Table(title=f"{code} {region} STOCK DEPTH", expand=True)
        tbl.add_column("POS", style="cyan")
        tbl.add_column("BID P", style="green")
        tbl.add_column("BID V", style="green")
        tbl.add_column("ASK P", style="red")
        tbl.add_column("ASK V", style="red")
        for i in range(5):
            b_idx = 9 + i * 2
            a_idx = 19 + i * 2
            tbl.add_row(str(i+1),
                        fields[b_idx] if len(fields) > b_idx else "",
                        fields[b_idx+1] if len(fields) > b_idx+1 else "",
                        fields[a_idx] if len(fields) > a_idx else "",
                        fields[a_idx+1] if len(fields) > a_idx+1 else "")
        return tbl
    return "[red]INVALID FUNCTION[/red]"

def handle_indices(code, region, func):
    fields = req_indices(code, region)
    if not fields:
        return "[red]No DATA (Indices API failed)[/red]"
    if func in ("DES", "INFO"):
        return _info_table(f"{fields[1]} [{code} {region} INDICES]", [
            ("CODE", code), ("NAME", fields[1]), ("TYPE", "indices"),
            ("EXCHANGE", region), ("REGION", region)
        ])
    if func == "QUOTE":
        return _quote_table(f"{code} {region} INDICES QUOTE", [
            ("LAST", fields[3] if len(fields) > 3 else "N/A"),
            ("OPEN", fields[5] if len(fields) > 5 else "N/A"),
            ("HIGH", fields[33] if len(fields) > 33 else "N/A"),
            ("LOW", fields[34] if len(fields) > 34 else "N/A"),
            ("CHG", fields[31] if len(fields) > 31 else "N/A"),
            ("CHG%", fields[32] if len(fields) > 32 else "N/A"),
            ("TIME", fields[30] if len(fields) > 30 else "N/A"),
        ])
    if func == "TICK":
        return (f"[green]{code} {region} INDICES TICK[/green]\n"
                f"LAST: {fields[3] if len(fields) > 3 else 'N/A'}\n"
                f"VOL : {fields[6] if len(fields) > 6 else 'N/A'}\n"
                f"TIME: {fields[30] if len(fields) > 30 else 'N/A'}")
    if func == "DEPTH":
        tbl = Table(title=f"{code} {region} INDICES DEPTH", expand=True)
        tbl.add_column("POS", style="cyan")
        tbl.add_column("BID P", style="green")
        tbl.add_column("BID V", style="green")
        tbl.add_column("ASK P", style="red")
        tbl.add_column("ASK V", style="red")
        for i in range(5):
            b_idx = 9 + i * 2
            a_idx = 19 + i * 2
            tbl.add_row(str(i+1),
                        fields[b_idx] if len(fields) > b_idx else "",
                        fields[b_idx+1] if len(fields) > b_idx+1 else "",
                        fields[a_idx] if len(fields) > a_idx else "",
                        fields[a_idx+1] if len(fields) > a_idx+1 else "")
        return tbl
    return "[red]INVALID FUNCTION[/red]"

def handle_future(code, region, func):
    fields = req_future(code, region)
    if not fields:
        return "[red]No DATA (Future API failed)[/red]"
    if func in ("DES", "INFO"):
        return _info_table(f"{fields[0]} [{code} {region} FUTURE]", [
            ("CODE", code), ("NAME", fields[0]), ("TYPE", "future"),
            ("EXCHANGE", region), ("REGION", region)
        ])
    if func == "QUOTE":
        return _quote_table(f"{code} {region} FUTURE QUOTE", [
            ("LAST", fields[1] if len(fields) > 1 else "N/A"),
            ("OPEN", fields[3] if len(fields) > 3 else "N/A"),
            ("HIGH", fields[4] if len(fields) > 4 else "N/A"),
            ("LOW", fields[5] if len(fields) > 5 else "N/A"),
            ("VOL", fields[6] if len(fields) > 6 else "N/A"),
            ("OI", fields[7] if len(fields) > 7 else "N/A"),
            ("TIME", f"{fields[13]} {fields[14]}" if len(fields) > 14 else "N/A"),
        ])
    if func == "TICK":
        return (f"[green]{code} {region} FUTURE TICK[/green]\n"
                f"LAST: {fields[1] if len(fields) > 1 else 'N/A'}\n"
                f"VOL : {fields[6] if len(fields) > 6 else 'N/A'}\n"
                f"TIME: {fields[13] if len(fields) > 13 else 'N/A'} "
                f"{fields[14] if len(fields) > 14 else ''}")
    if func == "DEPTH":
        tbl = Table(title=f"{code} {region} FUTURE DEPTH", expand=True)
        tbl.add_column("POS", style="cyan")
        tbl.add_column("BID P", style="green")
        tbl.add_column("BID V", style="green")
        tbl.add_column("ASK P", style="red")
        tbl.add_column("ASK V", style="red")
        for i in range(5):
            b_idx = 9 + i * 2
            a_idx = 19 + i * 2
            tbl.add_row(str(i+1),
                        fields[b_idx] if len(fields) > b_idx else "",
                        fields[b_idx+1] if len(fields) > b_idx+1 else "",
                        fields[a_idx] if len(fields) > a_idx else "",
                        fields[a_idx+1] if len(fields) > a_idx+1 else "")
        return tbl
    return "[red]INVALID FUNCTION[/red]"

def handle_forex(code, region, func):
    fields = req_forex(code, region)
    if not fields:
        return "[red]No DATA (Forex API failed)[/red]"
    if func in ("DES", "INFO"):
        return _info_table(f"{fields[0]} [{code} {region} FOREX]", [
            ("CODE", code), ("NAME", fields[0]), ("TYPE", "forex"),
            ("EXCHANGE", region), ("REGION", region)
        ])
    if func == "QUOTE":
        return _quote_table(f"{code} {region} FOREX QUOTE", [
            ("LAST", fields[1] if len(fields) > 1 else "N/A"),
            ("BID", fields[2] if len(fields) > 2 else "N/A"),
            ("ASK", fields[3] if len(fields) > 3 else "N/A"),
            ("HIGH", fields[6] if len(fields) > 6 else "N/A"),
            ("LOW", fields[7] if len(fields) > 7 else "N/A"),
            ("CHG", fields[4] if len(fields) > 4 else "N/A"),
            ("CHG%", fields[5] if len(fields) > 5 else "N/A"),
            ("TIME", fields[9] if len(fields) > 9 else "N/A"),
        ])
    if func == "TICK":
        return (f"[green]{code} {region} FOREX TICK[/green]\n"
                f"LAST: {fields[1] if len(fields) > 1 else 'N/A'}\n"
                f"TIME: {fields[9] if len(fields) > 9 else 'N/A'}")
    if func == "DEPTH":
        tbl = Table(title=f"{code} {region} FOREX DEPTH", expand=True)
        tbl.add_column("POS", style="cyan")
        tbl.add_column("BID P", style="green")
        tbl.add_column("ASK P", style="red")
        tbl.add_row("1",
                    fields[2] if len(fields) > 2 else "",
                    fields[3] if len(fields) > 3 else "")
        return tbl
    return "[red]INVALID FUNCTION[/red]"

def handle_fund(code, region, func):
    fields = req_fund(code, region)
    if not fields:
        return "[red]No DATA (Fund API failed)[/red]"
    if func in ("DES", "INFO"):
        return _info_table(f"{fields[0]} [{code} {region} FUND]", [
            ("CODE", code), ("NAME", fields[0]), ("TYPE", "fund"),
            ("EXCHANGE", region), ("REGION", region)
        ])
    if func == "QUOTE":
        return _quote_table(f"{code} {region} FUND QUOTE", [
            ("NAV", fields[1] if len(fields) > 1 else "N/A"),
            ("ACC NAV", fields[2] if len(fields) > 2 else "N/A"),
            ("DAILY CHG", fields[3] if len(fields) > 3 else "N/A"),
            ("DAILY CHG%", fields[4] if len(fields) > 4 else "N/A"),
            ("DATE", fields[5] if len(fields) > 5 else "N/A"),
        ])
    if func == "TICK":
        return (f"[green]{code} {region} FUND TICK[/green]\n"
                f"NAV : {fields[1] if len(fields) > 1 else 'N/A'}\n"
                f"DATE: {fields[5] if len(fields) > 5 else 'N/A'}")
    if func == "DEPTH":
        return "[red]DEPTH not available for Fund[/red]"
    return "[red]INVALID FUNCTION[/red]"

def handle_crypto(code, region, func):
    if func in ("DES", "INFO"):
        d = req_crypto_ticker(code, region)
        if not d or d.get("code"):
            return "[red]No DATA (Crypto API failed)[/red]"
        sym = d.get("symbol", f"{code}USDT")
        return _info_table(f"{sym} [{code} {region} CRYPTO]", [
            ("CODE", code), ("NAME", sym), ("TYPE", "crypto"),
            ("EXCHANGE", "Binance"), ("REGION", region)
        ])
    if func == "QUOTE":
        d = req_crypto_ticker(code, region)
        if not d or d.get("code"):
            return "[red]No DATA (Crypto API failed)[/red]"
        return _quote_table(f"{code} {region} CRYPTO QUOTE", [
            ("LAST", d.get("lastPrice", "N/A")),
            ("OPEN", d.get("openPrice", "N/A")),
            ("HIGH", d.get("highPrice", "N/A")),
            ("LOW", d.get("lowPrice", "N/A")),
            ("CHG", d.get("priceChange", "N/A")),
            ("CHG%", d.get("priceChangePercent", "N/A")),
            ("VOL", d.get("volume", "N/A")),
            ("TIME", format_time(d.get("closeTime", ""))),
        ])
    if func == "TICK":
        d = req_crypto_ticker(code, region)
        if not d or d.get("code"):
            return "[red]No DATA (Crypto API failed)[/red]"
        return (f"[green]{code} {region} CRYPTO TICK[/green]\n"
                f"LAST: {d.get('lastPrice', 'N/A')}\n"
                f"VOL : {d.get('volume', 'N/A')}\n"
                f"TIME: {format_time(d.get('closeTime', ''))}")
    if func == "DEPTH":
        d = req_crypto_depth(code, region)
        if not d or d.get("code"):
            return "[red]No DATA (Crypto API failed)[/red]"
        tbl = Table(title=f"{code} {region} CRYPTO DEPTH", expand=True)
        tbl.add_column("POS", style="cyan")
        tbl.add_column("BID P", style="green")
        tbl.add_column("BID V", style="green")
        tbl.add_column("ASK P", style="red")
        tbl.add_column("ASK V", style="red")
        bids = d.get("bids", [])
        asks = d.get("asks", [])
        for i in range(5):
            b = bids[i] if i < len(bids) else ["", ""]
            a = asks[i] if i < len(asks) else ["", ""]
            tbl.add_row(str(i+1), b[0], b[1], a[0], a[1])
        return tbl
    return "[red]INVALID FUNCTION[/red]"

# ============ 主入口（原有调用方式完全不变） ============

def get_stock_quote(full_command):
    try:
        code, region, cat, func = parse_command(full_command)
        if func == "HOLIDAY":
            return get_holidays(region)
        if cat == "stock":
            return handle_stock(code, region, func)
        elif cat == "indices":
            return handle_indices(code, region, func)
        elif cat == "future":
            return handle_future(code, region, func)
        elif cat == "forex":
            return handle_forex(code, region, func)
        elif cat == "fund":
            return handle_fund(code, region, func)
        elif cat == "crypto":
            return handle_crypto(code, region, func)
        else:
            return "[red]Unsupported category[/red]"
    except Exception as e:
        return f"[red]Command error: {e}[/red]"

def get_stock_chart(full_command):
    code, region, cat, _ = parse_command(full_command)
    if cat == "stock":
        data = _tencent_kline(code, region, limit=60)
    elif cat == "indices":
        data = _tencent_kline(code, region, limit=60)
    elif cat == "crypto":
        data = req_crypto_kline(code, region, limit=60)
    else:
        return "[red]CHART only supports stock/indices/crypto[/red]"
    if not data:
        return "[red]No KLINE DATA[/red]"
    closes = []
    for item in data:
        try:
            if cat == "crypto":
                closes.append(float(item[4]))
            else:
                closes.append(float(item[2]))
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