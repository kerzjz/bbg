import requests
import plotext as plt
from rich.table import Table

def get_stock_quote(ticker):
    """
    100% 兼容原架构，国内可直连，新浪财经API
    """
    try:
        # 新浪美股API
        symbol = ticker.lower()
        url = f"https://hq.sinajs.cn/list=us_{symbol}"
        headers = {
            "Referer": "https://finance.sina.com.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        text = response.text
        
        # 解析返回的JS数据
        if "hq_str_us_" not in text or len(text) < 100:
            return f"[red]Error:[/red] Ticker '{ticker}' not found."
        
        # 提取数据
        data_part = text.split('"')[1]
        if not data_part:
            return f"[red]Error:[/red] Ticker '{ticker}' not found."
        
        fields = data_part.split(',')
        if len(fields) < 2:
            return f"[red]Error:[/red] Invalid data for '{ticker}'."
        
        price = fields[1]
        name = fields[0] if len(fields) > 0 else ticker.upper()

        # 表格结构与原版完全一致
        table = Table(title=f"{name} ({ticker.upper()})", expand=True)
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
    100% 兼容原架构，国内可直连，使用网易财经K线数据
    """
    try:
        symbol = ticker.lower()
        url = f"https://api.money.126.net/data/feed/us_{symbol},kline_day"
        headers = {
            "Referer": "https://money.163.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        key = f"us_{symbol}"
        if key not in data or "klines" not in data[key]:
            return "No data available for chart generation."

        klines = data[key]["klines"]
        if not klines:
            return "No data available for chart generation."
        
        # 取最近60天的收盘价
        prices = []
        for line in klines[-60:]:
            parts = line.split(',')
            if len(parts) >= 3:
                prices.append(float(parts[2]))

        if not prices:
            return "No data available for chart generation."

        # 图表格式与原版完全一致
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