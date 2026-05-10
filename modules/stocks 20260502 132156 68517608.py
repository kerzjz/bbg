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

# ============ 腾讯财经接口封装（免费、免Token、国内直连） ============

def _normalize_region(code, region):
    """CN 自动映射到 SH/SZ，方便用户输入"""
    if region == "CN":
        return "SH" if code.startswith("6") else "SZ"
    return region

def req_tencent(code, region):
    """请求腾讯财经实时行情，返回字段列表（~分隔）"""
    prefix_map = {
        "SH": "sh", "SZ": "sz", "HK": "hk", "US": "us",
        "SG": "sg", "JP": "jp", "GB": "uk", "BA": "us"
    }
    region = _normalize_region(code, region)
    prefix = prefix_map.get(region, "us")
    symbol = f"{prefix}{code}"
    url = f"https://qt.gtimg.cn/q={symbol}"

    try:
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

def req_tencent_kline(code, region, limit=60):
    """请求腾讯K线，返回 [[date, open, close, low, high, vol], ...]"""
    prefix_map = {"SH": "sh", "SZ": "sz", "HK": "hk", "US": "us"}
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
        # 过滤周末，只保留交易所特殊假期
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

# ============ 主业务逻辑（接口已换，调用方式不变） ============

def get_stock_quote(full_command):
    try:
        code, region, cat, func = parse_command(full_command)

        # ==================== HOLIDAY：本地日历，永不过期 ====================
        if func == "HOLIDAY":
            return get_holidays(region)

        # ==================== 股票类：腾讯财经接口（免Token） ====================
        if cat == "stock" and region in ("US", "SH", "SZ", "HK", "SG", "JP", "GB", "CN"):
            fields = req_tencent(code, region)
            if not fields:
                return "[red]No DATA (Tencent API failed)[/red]"

            if func in ("DES", "INFO"):
                name = fields[1] if len(fields) > 1 else "Unknown"
                tbl = Table(title=f"{name} [{code} {region} {cat}]", expand=True)
                tbl.add_column("Field", style="cyan")
                tbl.add_column("Value", style="green")
                tbl.add_row("CODE", code)
                tbl.add_row("NAME", name)
                tbl.add_row("TYPE", cat)
                tbl.add_row("EXCHANGE", region)
                tbl.add_row("REGION", region)
                return tbl

            if func == "QUOTE":
                tbl = Table(title=f"{code} {region} {cat} QUOTE", expand=True)
                tbl.add_column("FIELD", style="cyan")
                tbl.add_column("VALUE", style="green")
                tbl.add_row("LAST", fields[3] if len(fields) > 3 else "N/A")
                tbl.add_row("OPEN", fields[5] if len(fields) > 5 else "N/A")
                tbl.add_row("HIGH", fields[33] if len(fields) > 33 else "N/A")
                tbl.add_row("LOW", fields[34] if len(fields) > 34 else "N/A")
                tbl.add_row("CHG", fields[31] if len(fields) > 31 else "N/A")
                tbl.add_row("CHG%", fields[32] if len(fields) > 32 else "N/A")
                tbl.add_row("TIME", fields[30] if len(fields) > 30 else "N/A")
                return tbl

            if func == "TICK":
                last = fields[3] if len(fields) > 3 else "N/A"
                vol = fields[6] if len(fields) > 6 else "N/A"
                tm = fields[30] if len(fields) > 30 else "N/A"
                return f"[green]{code} {region} {cat} TICK[/green]\nLAST: {last}\nVOL : {vol}\nTIME: {tm}"

            if func == "DEPTH":
                tbl = Table(title=f"{code} {region} {cat} DEPTH", expand=True)
                tbl.add_column("POS", style="cyan")
                tbl.add_column("BID P", style="green")
                tbl.add_column("BID V", style="green")
                tbl.add_column("ASK P", style="red")
                tbl.add_column("ASK V", style="red")

                for i in range(5):
                    b_idx = 9 + i * 2
                    a_idx = 19 + i * 2
                    bp = fields[b_idx] if len(fields) > b_idx else ""
                    bv = fields[b_idx+1] if len(fields) > b_idx+1 else ""
                    ap = fields[a_idx] if len(fields) > a_idx else ""
                    av = fields[a_idx+1] if len(fields) > a_idx+1 else ""
                    tbl.add_row(str(i+1), bp, bv, ap, av)
                return tbl

        # ==================== 非股票类：降级提示 ====================
        return (f"[red]{cat.upper()} / {region} not supported in free mode. "
                f"Supported: stock US/SH/SZ/HK/SG/JP/GB/CN[/red]")

    except Exception as e:
        return f"[red]Command error: {e}[/red]"

def get_stock_chart(full_command):
    code, region, cat, _ = parse_command(full_command)

    if cat != "stock" or region not in ("US", "SH", "SZ", "HK", "CN"):
        return "[red]CHART only supports stock US/SH/SZ/HK/CN in free mode[/red]"

    data = req_tencent_kline(code, region, limit=60)
    if not data:
        return "[red]No KLINE DATA[/red]"

    closes = []
    for item in data:
        try:
            closes.append(float(item[2]))  # 收盘价
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