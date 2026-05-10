import requests
import plotext as plt
from rich.table import Table

def parse_command(command):
    """
    解析格式：
    BA US STOCK
    000001 SZ STOCK
    600000 SH STOCK
    BTC BA CRYPTO
    """
    parts = command.strip().upper().split()
    code = parts[0]
    region = "US"   # 默认美股
    type_ = "STOCK" # 默认股票

    if len(parts) >= 2:
        region = parts[1]  # US / SH / SZ / HK / JP
    if len(parts) >= 3:
        type_ = parts[2]   # STOCK / INDICES / CRYPTO / FOREX

    # 直接使用真实region：SH / SZ / US / HK 等
    return code, region, type_

def get_stock_quote(command):
    try:
        code, region, type_ = parse_command(command)

        url = f"https://api.itick.org/symbol/list?type={type_}&region={region}&code={code}"
        headers = {
            "accept": "application/json",
            "token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        res = response.json()

        if res.get("code") != 0 or not res.get("data"):
            return f"[red]Error:[/red] No data for {command}"

        data_list = res["data"]
        target = None
        for item in data_list:
            if item.get("c", "").upper() == code.upper():
                target = item
                break
        if not target:
            target = data_list[0]

        table = Table(title=f"{target.get('n', 'Name')} ({target.get('c', code)})", expand=True)
        table.add_column("Info", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Code", target.get("c", ""))
        table.add_row("Name", target.get("n", ""))
        table.add_row("Exchange", target.get("e", ""))
        table.add_row("Sector", target.get("s", ""))
        table.add_row("Region", region)
        table.add_row("Type", type_)

        return table

    except Exception as e:
        return f"[red]System Error:[/red] {str(e)}"

def get_stock_chart(command):
    try:
        code, region, type_ = parse_command(command)

        url = f"https://api.itick.org/chart/day?symbol={code}&region={region}&type={type_}&limit=60"
        headers = {
            "accept": "application/json",
            "token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
        }

        response = requests.get(url, headers=headers, timeout=10)
        res = response.json()

        if res.get("code") != 0 or not res.get("data"):
            return "[red]No chart data[/red]"

        klines = res["data"]
        prices = []
        for line in klines:
            if len(line) >= 5:
                prices.append(float(line[4]))

        if not prices:
            return "[red]No price data[/red]"

        plt.clear_figure()
        plt.theme('dark')
        plt.plot(prices, label="Close")
        plt.title(f"{code} {region} {type_}")
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.grid(True)
        return plt.build()

    except Exception as e:
        return f"[red]Chart Error:[/red] {str(e)}"