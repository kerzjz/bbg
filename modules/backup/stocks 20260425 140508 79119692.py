import requests
import plotext as plt
from rich.table import Table

def get_stock_quote(ticker):
    """
    100% 兼容你原架构，使用 itick.org 真实美股 API
    国内可直连、非网页、返回真实JSON
    """
    try:
        url = "https://api.itick.org/symbol/list?type=stock&region=us&code=" + ticker.upper()
        headers = {
            "accept": "application/json",
            "token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data or "symbol" not in data:
            return f"[red]Error:[/red] Ticker '{ticker}' not found."

        q = data["symbol"]
        price = q.get("price", "N/A")
        market_cap = q.get("marketCap", 0)
        pe = q.get("peRatio", "N/A")
        high52 = q.get("week52High", "N/A")
        name = q.get("name", ticker)
        sector = q.get("sector", "N/A")

        # 表格结构与你原代码完全一致
        table = Table(title=f"{name} ({ticker.upper()})", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Price", f"${price}")
        table.add_row("Market Cap", f"${market_cap:,}")
        table.add_row("PE Ratio", str(pe))
        table.add_row("52 Week High", str(high52))
        table.add_row("Sector", sector)

        return table

    except Exception as e:
        return f"[red]System Error:[/red] {str(e)}"


def get_stock_chart(ticker):
    """
    100% 兼容你原架构，使用 itick.org K线 API
    国内可直连、真实数据
    """
    try:
        url = f"https://api.itick.org/chart/day?symbol={ticker.upper()}&limit=60"
        headers = {
            "accept": "application/json",
            "token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data or "klines" not in data:
            return "No data available for chart generation."

        prices = [float(kline["close"]) for kline in data["klines"] if "close" in kline]

        if not prices:
            return "No data available for chart generation."

        # 图表格式与你原代码完全一致
        plt.clear_figure()
        plt.theme('dark')
        plt.plot(prices, label="Close Price")
        plt.title(f"{ticker.upper()} - 3 Months Trend")
        plt.xlabel("Trading Days")
        plt.ylabel("Price ($)")
        plt.grid(True, True)
        plt.frame(True)

        return plt.build()

    except Exception as e:
        return f"[red]Chart Error:[/red] {str(e)}"