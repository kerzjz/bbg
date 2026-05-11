import requests
import plotext as plt
from rich.table import Table
from datetime import datetime
import re
import json

try:
    import akshare as ak
    import pandas as pd
    AKSHARE_OK = True
except ImportError:
    AKSHARE_OK = False


REGION_TO_CURRENCY = {
    "US": "USD", "HK": "HKD", "JP": "JPY", "GB": "GBP",
    "SG": "SGD", "CN": "CNY", "SH": "CNY", "SZ": "CNY", "CNY": "CNY",
    "EU": "EUR", "AU": "AUD", "CA": "CAD", "CH": "CHF", "NZ": "NZD",
    "KR": "KRW", "RU": "RUB", "TH": "THB",
}

GOLD_SINA_MAP = {
    "AU": "hf_GC",
    "XAU": "hf_GC",
    "AG": "hf_SI",
    "XAG": "hf_SI",
    "PT": "hf_PL",
    "PD": "hf_PA",
}

FX_SINA_MAP = {
    "USDCNY": "USDCNY", "EURCNY": "EURCNY", "GBPCNY": "GBPCNY",
    "JPYCNY": "JPYCNY", "HKDCNY": "HKDCNY", "AUDCNY": "AUDCNY",
    "CADCNY": "CADCNY", "SGDCNY": "SGDCNY", "CHFCNY": "CHFCNY",
    "NZDCNY": "NZDCNY", "KRWCNY": "KRWCNY", "RUBCNY": "RUBCNY",
    "THBCNY": "THBCNY",
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


def _to_currency(x):
    return REGION_TO_CURRENCY.get(x.upper(), x.upper())


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
    valid_regions = {"US","SH","SZ","HK","SG","JP","CN","GB","BA","CNY"}
    valid_cates = {"stock","future","forex","indices","fund","crypto","gold"}

    func = func if func in valid_funcs else "DES"
    region = region if region in valid_regions else "US"
    category = category if category in valid_cates else "stock"

    return code, region, category.lower(), func


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
    c1 = _to_currency(code)
    c2 = _to_currency(region)
    pair = f"{c1}{c2}"
    if pair in FX_SINA_MAP:
        return FX_SINA_MAP[pair], False
    pair_rev = f"{c2}{c1}"
    if pair_rev in FX_SINA_MAP:
        return FX_SINA_MAP[pair_rev], True
    return pair, False


def _inverse_fx(data):
    try:
        for key in ["ld", "o"]:
            v = data.get(key)
            if v:
                f = float(v)
                if f != 0:
                    data[key] = str(round(1.0 / f, 4))

        h, l = data.get("h"), data.get("l")
        if h and l:
            h_f, l_f = float(h), float(l)
            if h_f != 0 and l_f != 0:
                data["h"] = str(round(1.0 / l_f, 4))
                data["l"] = str(round(1.0 / h_f, 4))

        b = data.get("b", [])
        a = data.get("a", [])
        if b and a and b[0].get("p") and a[0].get("p"):
            b_f = float(b[0]["p"])
            a_f = float(a[0]["p"])
            if b_f != 0 and a_f != 0:
                data["b"] = [{"p": str(round(1.0 / a_f, 4)), "v": "N/A"}]
                data["a"] = [{"p": str(round(1.0 / b_f, 4)), "v": "N/A"}]

        data["ch"] = "N/A"
        data["chp"] = "N/A"
    except Exception:
        pass
    return data


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


def _parse_gold_sina(parts):
    if not parts or len(parts) < 8:
        return None
    try:
        last = float(parts[1]) if parts[1] else 0
        yc = float(parts[7]) if len(parts) > 7 and parts[7] else last
        ch = round(last - yc, 2)
        chp = round(ch / yc * 100, 2) if yc != 0 else 0
    except:
        ch, chp = 0, 0

    return {
        "n": parts[0] if parts[0] else "\u9ec4\u91d1",
        "ld": parts[1] if len(parts) > 1 else "",
        "o": parts[8] if len(parts) > 8 else (parts[7] if len(parts) > 7 else ""),
        "h": parts[4] if len(parts) > 4 else "",
        "l": parts[5] if len(parts) > 5 else "",
        "ch": str(ch),
        "chp": f"{chp}%",
        "v": parts[9] if len(parts) > 9 else "N/A",
        "t": f"{parts[12]} {parts[13]}" if len(parts) > 13 else (parts[6] if len(parts) > 6 else ""),
        "b": [{"p": parts[2] if len(parts) > 2 else "", "v": parts[10] if len(parts) > 10 else "N/A"}],
        "a": [{"p": parts[3] if len(parts) > 3 else "", "v": parts[11] if len(parts) > 11 else "N/A"}],
    }


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
    if not parts or len(parts) < 2:
        return None

    if len(parts) >= 10:
        try:
            last = float(parts[2]) if parts[2] else 0
            yc = float(parts[9]) if len(parts) > 9 and parts[9] else last
            ch = round(last - yc, 4)
            chp = round(ch / yc * 100, 2) if yc != 0 else 0
            return {
                "n": parts[10] if len(parts) > 10 and parts[10] else parts[0],
                "ld": parts[2],
                "o": parts[9] if len(parts) > 9 and parts[9] else parts[2],
                "h": parts[4] if len(parts) > 4 else "",
                "l": parts[8] if len(parts) > 8 else "",
                "ch": str(ch),
                "chp": f"{chp}%",
                "v": parts[5] if len(parts) > 5 else "N/A",
                "t": parts[1] if len(parts) > 1 else "",
                "b": [{"p": parts[2] if len(parts) > 2 else "", "v": "N/A"}],
                "a": [{"p": parts[3] if len(parts) > 3 else "", "v": "N/A"}],
            }
        except:
            pass

    if len(parts) >= 3:
        return {
            "n": parts[0],
            "ld": parts[2],
            "o": parts[2],
            "h": parts[2],
            "l": parts[2],
            "ch": "0",
            "chp": "0%",
            "v": "N/A",
            "t": parts[1] if len(parts) > 1 else "",
            "b": [{"p": parts[2], "v": "N/A"}],
            "a": [{"p": parts[3] if len(parts) > 3 else parts[2], "v": "N/A"}],
        }

    return None


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


def _fetch_fx_erapi(base, target):
    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("result") != "success":
            return None
        rate = data.get("rates", {}).get(target)
        if rate is None:
            return None
        return {
            "n": f"{base}/{target}",
            "ld": str(rate),
            "o": str(rate),
            "h": str(rate),
            "l": str(rate),
            "ch": "0",
            "chp": "0%",
            "v": "N/A",
            "t": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "b": [{"p": str(rate), "v": "N/A"}],
            "a": [{"p": str(rate), "v": "N/A"}],
        }
    except Exception:
        return None


def _fetch_fx_boc(base, target):
    if not AKSHARE_OK:
        return None
    try:
        df = ak.currency_boc_safe()
        if df.empty:
            return None
        latest = df.iloc[-1]
        date_str = str(latest.get("\u65e5\u671f", ""))

        boc_map = {
            "USD": "\u7f8e\u5143", "EUR": "\u6b27\u5143", "JPY": "\u65e5\u5143", "GBP": "\u82f1\u9551",
            "HKD": "\u6e2f\u5e01", "AUD": "\u6fb3\u5927\u5229\u4e9a\u5143", "CAD": "\u52a0\u62ff\u5927\u5143",
            "SGD": "\u65b0\u52a0\u5761\u5143", "CHF": "\u745e\u58eb\u6cd5\u90ce", "KRW": "\u97e9\u56fd\u5143",
            "THB": "\u6cf0\u56fd\u94e2", "RUB": "\u5362\u5e03", "NZD": "\u65b0\u897f\u5170\u5143",
            "CNY": "\u4eba\u6c11\u5e01"
        }
        base_name = boc_map.get(base, base)
        target_name = boc_map.get(target, target)

        if target == "CNY":
            rate = latest.get(base_name, None)
        elif base == "CNY":
            rate = latest.get(target_name, None)
            if rate:
                try:
                    rate = round(1.0 / float(rate), 4)
                except:
                    rate = None
        else:
            r1 = latest.get(base_name, None)
            r2 = latest.get(target_name, None)
            if r1 and r2:
                try:
                    rate = round(float(r1) / float(r2), 4)
                except:
                    rate = None
            else:
                rate = None

        if rate is None:
            return None

        return {
            "n": f"{base}/{target} (BOC)",
            "ld": str(rate),
            "o": str(rate),
            "h": str(rate),
            "l": str(rate),
            "ch": "0",
            "chp": "0%",
            "v": "N/A",
            "t": date_str,
            "b": [{"p": str(rate), "v": "N/A"}],
            "a": [{"p": str(rate), "v": "N/A"}],
        }
    except Exception:
        return None


def _fetch_fx_fallback(code, region):
    base = _to_currency(code)
    target = _to_currency(region)
    data = _fetch_fx_erapi(base, target)
    if data:
        return data
    data = _fetch_fx_boc(base, target)
    if data:
        return data
    return None


def _fetch_gold_akshare():
    if not AKSHARE_OK:
        return None
    try:
        df = ak.spot_golden_benchmark_sge()
        if df.empty:
            return None
        latest = df.iloc[-1]
        return {
            "n": "\u4e0a\u6d77\u91d1(Au99.99)",
            "ld": str(latest.get("\u4ef7\u683c", "")),
            "o": str(latest.get("\u4ef7\u683c", "")),
            "h": str(latest.get("\u4ef7\u683c", "")),
            "l": str(latest.get("\u4ef7\u683c", "")),
            "ch": "0",
            "chp": "0%",
            "v": "N/A",
            "t": str(latest.get("\u65e5\u671f", "")),
            "b": [{"p": str(latest.get("\u4ef7\u683c", "")), "v": "N/A"}],
            "a": [{"p": str(latest.get("\u4ef7\u683c", "")), "v": "N/A"}],
        }
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
        elif path.startswith("gold/"):
            cat = "gold"

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
                    "n": str(row.get("\u540d\u79f0", code)),
                    "ld": str(row.get("\u6700\u65b0\u4ef7", "")),
                    "o": str(row.get("\u5f00\u76d8\u4ef7", "")),
                    "h": str(row.get("\u6700\u9ad8\u4ef7", "")),
                    "l": str(row.get("\u6700\u4f4e\u4ef7", "")),
                    "ch": str(row.get("\u6da8\u8dcc\u989d", "")),
                    "chp": f"{row.get('\u6da8\u8dcc\u5e45', '')}%" if pd.notna(row.get('\u6da8\u8dcc\u5e45')) else "",
                    "v": str(row.get("\u6301\u4ed3\u91cf", "")),
                    "t": f"{row.get('\u65e5\u671f', '')} {row.get('\u884c\u60c5\u65f6\u95f4', '')}",
                    "b": [], "a": []
                }
                return {"code": 0, "data": data}
        except Exception:
            return {"code": -1, "data": None}

    elif cat == "forex":
        symbol, need_inverse = _fx_symbol(code, region)
        parts = _fetch_sina_quote(symbol)
        data = None
        if parts is not None:
            data = _parse_fx(parts)
            if data and need_inverse:
                data = _inverse_fx(data)

        if data is None:
            data = _fetch_fx_fallback(code, region)

        if data is None:
            return {"code": -1, "data": None}
        if "kline" in path:
            return {"code": -1, "data": None}
        return {"code": 0, "data": data}

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
            mask = df["\u4ea4\u6613\u54c1\u79cd"].str.contains(code, case=False, na=False)
            matched = df[mask]
            if matched.empty:
                return {"code": -1, "data": None}
            row = matched.iloc[0]
            data = {
                "n": str(row.get("\u4ea4\u6613\u54c1\u79cd", code)),
                "ld": str(row.get("\u6700\u8fd1\u62a5\u4ef7", "")),
                "o": "",
                "h": str(row.get("24\u5c0f\u65f6\u6700\u9ad8", "")),
                "l": str(row.get("24\u5c0f\u65f6\u6700\u4f4e", "")),
                "ch": str(row.get("\u6da8\u8dcc\u989d", "")),
                "chp": f"{row.get('\u6da8\u8dcc\u5e45', '')}%" if pd.notna(row.get('\u6da8\u8dcc\u5e45')) else "",
                "v": str(row.get("24\u5c0f\u65f6\u6210\u4ea4\u91cf", "")),
                "t": str(row.get("\u66f4\u65b0\u65f6\u95f4", "")),
                "b": [], "a": []
            }
            return {"code": 0, "data": data}
        except Exception:
            return {"code": -1, "data": None}

    elif cat == "gold":
        symbol = GOLD_SINA_MAP.get(code.upper(), "hf_GC")
        parts = _fetch_sina_quote(symbol)
        data = None
        if parts is not None:
            data = _parse_gold_sina(parts)

        if data is None and region in ("CN", "SH", "SZ", "CNY"):
            data = _fetch_gold_akshare()

        if data is None:
            return {"code": -1, "data": None}
        if "kline" in path:
            return {"code": -1, "data": None}
        return {"code": 0, "data": data}

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
            "crypto": "crypto",
            "gold": "gold"
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
        "crypto": "crypto",
        "gold": "gold"
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