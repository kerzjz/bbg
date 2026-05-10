import requests
import plotext as plt
from rich.table import Table

def get_stock_quote(ticker):
    """
    与原架构 100% 兼容，仅更换可用API
    """
    try:
        # 改用 Alpha Vantage 免费API（国内可访问，demo密钥可用）
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": "demo"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "Global Quote" not in data or not data["Global Quote"]:
            return f"[red]Error:[/red] Ticker '{ticker}' not found or data unavailable."

        gq = data["Global Quote"]
        price = gq.get("05. price", "N/A")
        change = float(gq.get("10. change percent", "0").strip('%'))

        # 表格结构完全不变
        table = Table(title=f"{ticker}", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Price", f"${price}")
        table.add_row("Market Cap", "N/A")  # 免费版无市值，保持字段存在
        table.add_row("PE Ratio", "N/A")
        table.add_row("52 Week High", "N/A")
        table.add_row("Sector", "N/A")

        return table

    except Exception as e:
        return f"[red]System Error:[/red] {str(e)}"


def get_stock_chart(ticker):
    """
    与原架构 100% 兼容，仅更换可用API
    """
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "apikey": "demo",
            "outputsize": "compact"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "Time Series (Daily)" not in data:
            return "No data available for chart generation."

        ts = data["Time Series (Daily)"]
        # 取最近60天数据（约3个月）
        dates = sorted(ts.keys(), reverse=True)[:60][::-1]
        prices = [float(ts[d]["4. close"]) for d in dates]

        # 图表格式完全不变
        plt.clear_figure()
        plt.theme('dark')
        plt.plot(prices, label="Close Price")
        plt.title(f"{ticker} - 3 Months Trend")
        plt.xlabel("Trading Days")
        plt.ylabel("Price ($)")
        plt.grid(True, True)
        plt.frame(True)

        return plt.build()

    except Exception as e:
        return f"[red]Chart Error:[/red] {str(e)}"