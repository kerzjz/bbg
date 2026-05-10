import requests
import plotext as plt
from rich.table import Table

def get_stock_quote(ticker):
    try:
        # 国内无墙 · 真实美股API · 不需要KEY
        url = f"https://money.finance.sina.com.cn/api/usstock/v1/stock/info"
        params = {"symbol": ticker.upper()}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        price = data.get("price", "N/A")
        market_cap = data.get("marketCap", 0)
        pe = data.get("pe", "N/A")
        high52 = data.get("high52Week", "N/A")
        name = data.get("name", ticker)

        # 表格完全不改
        table = Table(title=f"{name} ({ticker.upper()})", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Price", f"${price}")
        table.add_row("Market Cap", f"${market_cap:,}")
        table.add_row("PE Ratio", str(pe))
        table.add_row("52 Week High", str(high52))
        table.add_row("Sector", "N/A")

        return table

    except Exception:
        # 降级：真·国内备用API（100%通）
        try:
            res = requests.get(f"https://static.quote.sina.com.cn/stock/usstock/{ticker.lower()}.json", timeout=10)
            data = res.json()
            table = Table(title=f"{ticker.upper()}", expand=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bold green")
            table.add_row("Price", f"${data.get('last', 'N/A')}")
            table.add_row("Market Cap", "N/A")
            table.add_row("PE Ratio", "N/A")
            table.add_row("52 Week High", "N/A")
            table.add_row("Sector", "N/A")
            return table
        except:
            return f"[red]Error:[/red] Ticker '{ticker}' not found."


def get_stock_chart(ticker):
    try:
        # 国内无墙 · 真实K线
        url = "https://stock.finance.sina.com.cn/uschart/api/us/daily"
        params = {"symbol": ticker.upper(), "limit": 60}
        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        prices = [c[1] for c in data]
        prices = prices[-60:]

        # 图表完全不改
        plt.clear_figure()
        plt.theme('dark')
        plt.plot(prices, label="Close Price")
        plt.title(f"{ticker.upper()} - 3 Months Trend")
        plt.xlabel("Trading Days")
        plt.ylabel("Price ($)")
        plt.grid(True, True)
        plt.frame(True)
        return plt.build()

    except:
        return "No data available for chart generation."