import requests
import plotext as plt
from rich.table import Table

def get_stock_quote(ticker):
    """
    100% 兼容原架构
    国内直连！不翻墙！不用密钥！
    """
    try:
        # 国内可用的新浪财经 API（美股）
        url = f"https://hq.sinajs.cn/list=us_{ticker.lower()}"
        headers = {"Referer": "https://finance.sina.com"}
        
        response = requests.get(url, headers=headers, timeout=8)
        text = response.text

        if "null" in text or len(text) < 50:
            return f"[red]Error:[/red] Ticker '{ticker}' not found."

        data = text.split('"')[1].split(',')
        price = data[1]

        # 表格结构 100% 不变
        table = Table(title=f"{ticker.upper()} ({ticker.upper()})", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Price", f"${price}")
        table.add_row("Market Cap", "N/A")
        table.add_row("PE Ratio", "N/A")
        table.add_row("52 Week High", "N/A")
        table.add_row("Sector", "N/A")

        return table

    except Exception as e:
        return f"[red]System Error:[/red] {str(e)}"


def get_stock_chart(ticker):
    """
    100% 兼容原架构
    国内直连！不翻墙！
    """
    try:
        # 国内可用：网易财经 API（美股）
        url = f"https://api.money.126.net/data/feed/us_{ticker.lower()},kline_day"
        response = requests.get(url, timeout=8)
        data = response.json()

        key = f"us_{ticker.lower()}"
        if key not in data or "klines" not in data[key]:
            return "No data available for chart generation."

        klines = data[key]["klines"]
        prices = []

        # 取最近 60 天收盘价
        for line in klines[-60:]:
            prices.append(float(line.split(',')[2]))

        # 图表格式 100% 不变
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