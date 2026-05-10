import requests
import plotext as plt
from rich.table import Table

def get_stock_quote(ticker):
    try:
        url = "https://api.itick.org/symbol/list?type=stock&region=us&code=" + ticker.upper()
        headers = {
            "accept": "application/json",
            "token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # --------------------------
        # 这里是你原来错误的核心！
        # API 返回结构是 data → list
        # --------------------------
        if not data or "data" not in data or len(data["data"]) == 0:
            return f"[red]Error:[/red] Ticker '{ticker}' not found."

        # 取出第一个匹配的股票
        stocks_list = data["data"]
        target_stock = None

        # 精确匹配代码（比如 BA 就只返回 BA）
        for s in stocks_list:
            if s.get("c", "").upper() == ticker.upper():
                target_stock = s
                break

        if not target_stock:
            target_stock = stocks_list[0]

        # 字段对应 API 返回：c=代码, n=名称, e=交易所, s=行业
        code = target_stock.get("c", ticker)
        name = target_stock.get("n", "Unknown")
        exchange = target_stock.get("e", "N/A")
        sector = target_stock.get("s", "N/A")

        # 这个接口不返回价格，所以显示提示
        table = Table(title=f"{name} ({code})", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Code", code)
        table.add_row("Name", name)
        table.add_row("Exchange", exchange)
        table.add_row("Sector", sector)
        table.add_row("Price", "API 不提供实时价格（请用 CHART 查看K线）")

        return table

    except Exception as e:
        return f"[red]System Error:[/red] {str(e)}"


def get_stock_chart(ticker):
    try:
        url = f"https://api.itick.org/chart/day?symbol={ticker.upper()}&limit=60"
        headers = {
            "accept": "application/json",
            "token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 正确解析 K线
        if not data or "data" not in data or len(data["data"]) == 0:
            return "No chart data available."

        klines = data["data"]
        prices = []

        # 解析收盘价
        for line in klines:
            if len(line) >= 4:
                close_price = line[3]
                prices.append(float(close_price))

        if not prices:
            return "No valid price data."

        plt.clear_figure()
        plt.theme('dark')
        plt.plot(prices, label="Close Price")
        plt.title(f"{ticker.upper()} - Trend")
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.grid(True, True)
        return plt.build()

    except Exception as e:
        return f"[red]Chart Error:[/red] {str(e)}"