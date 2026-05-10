import requests
import plotext as plt
from rich.table import Table
from datetime import datetime
import re

# ==================== 免费平替配置 ====================
# 原 iTick API 已过期，改用新浪财经/腾讯财经公开接口
# 无需 Token，国内直接访问，真实数据
# =====================================================

def format_time(ts):
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
        return str(ts)
    except:
        return "N/A"

def parse_command(full_command):
    # 安全过滤：只保留字母、数字、空格，防止特殊符号炸程序
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

    # 合法性校验（不修改逻辑，只拦截非法值）
    valid_funcs = {"DES","INFO","QUOTE","TICK","DEPTH","CHART","GP","HOLIDAY"}
    valid_regions = {"US","SH","SZ","HK","SG","JP","CN","GB","BA"}
    valid_cates = {"stock","future","forex","indices","fund","crypto"}

    func = func if func in valid_funcs else "DES"
    region = region if region in valid_regions else "US"
    category = category if category in valid_cates else "stock"

    return code, region, category.lower(), func


# ==================== 底层免费数据接口（新增/替换部分） ====================

def _sina_symbol(code, region, category):
    """生成新浪财经接口用的 symbol"""
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
    elif category in ("forex", "crypto"):
        return f"{code}"
    return f"sh{code}"


def _fetch_sina_quote(symbol):
    """从新浪财经获取原始行情字符串"""
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
    """解析A股/基金/指数行情（新浪格式）"""
    # 字段顺序: 名称,开盘,昨收,最新,最高,最低,买1价,卖1价,成交量,成交额,
    #           买1量,买1价,买2量,买2价...买5量,买5价,
    #           卖1量,卖1价...卖5量,卖5价,日期,时间
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
    """解析港股行情（新浪格式）"""
    # 字段: 英文名称,最新价,涨跌额,涨跌幅,开盘价,最高价,最低价,买价,卖价,成交量,成交额...
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
    """解析美股行情（新浪格式）"""
    # 字段: 名称,最新价,涨跌额,涨跌幅,开盘价,最高价,最低价,52周高,52周低,成交量,成交额...
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


def _fetch_kline_tencent(code, region, limit=60):
    """从腾讯财经获取日K线（前复权）"""
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


def req(path, **kw):
    """
    兼容原 req 函数签名。
    底层改为新浪财经/腾讯财经免费接口。
    """
    code = kw.get("code", "")
    region = kw.get("region", "US")
    cat = kw.get("type", "stock").lower()
    symbol = _sina_symbol(code, region, cat)

    # 根据 path 判断请求类型
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

        # ==================== HOLIDAY ====================
        if func == "HOLIDAY":
            return f"[yellow]Holiday data not available in free tier (no free cross-market holiday API found)[/yellow]"

        # ==================== DES / INFO ====================
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