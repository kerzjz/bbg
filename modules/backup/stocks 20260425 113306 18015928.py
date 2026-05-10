import requests
import plotext as plt
from rich.table import Table

def get_stock_quote(ticker):
    """
    原架构 100% 保留
    函数、表格、返回格式完全不变
    """
    try:
        url = f"https://api.iex.cloud/v1/data/core/quote/{ticker}?token=pk_7d4a5b40c5f54f8b9ecf55c9e356b1c4"
        res = requests.get(url, timeout=10)
        data = res.json()

        if not data or "latestPrice" not in data[0]:
            return f"[red]Error:[/red] Ticker '{ticker}' not found or data unavailable."

        d = data[0]
        table = Table(title=f"{ticker}", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Price", f"${d.get('latestPrice', 'N/A')}")
        table.add_row("Market Cap", f"${d.get('marketCap', 0):,}")
        table.add_row("PE Ratio", str(d.get('peRatio', 'N/A')))
        table.add_row("52 Week High", str(d.get('week52High', 'N/A')))
        table.add_row("Sector", "N/A")

        return table

    except Exception as e:
        return f"[red]System Error:[/red] {str(e)}"


def get_stock_chart(ticker):
    """
    原架构 100% 保留
    图表格式、返回格式完全不变
    """
    try:
        url = f"https://api.iex.cloud/v1/data/core/chart/{ticker}/3m?token=pk_7d4a5b40c5f54f8b9ecf55c9e356b1c4"
        res = requests.get(url, timeout=10)
        data = res.json()

        if not data:
            return "No data available for chart generation."

        prices = [float(day["close"]) for day in data]

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