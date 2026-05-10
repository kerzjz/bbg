import requests
import plotext as plt
from rich.table import Table

def parse_command(full_command):
    """
    兼容所有格式：
    1. AAPL DES
    2. 000001 DES
    3. BA US STOCK DES
    4. 000001 SZ STOCK CHART
    """
    parts = full_command.strip().upper().split()
    
    # 先分离出功能词（最后一个）
    func = "DES"
    if parts[-1] in ["DES", "QUOTE", "CHART", "GP"]:
        func = parts[-1]
        data_parts = parts[:-1]
    else:
        data_parts = parts

    # 解析标的信息
    if len(data_parts) == 1:
        # 格式：AAPL
        code = data_parts[0]
        # 自动判断市场：
        if code.isdigit():
            if code.startswith("60") or code.startswith("68"):
                region = "SH"
            else:
                region = "SZ"
        else:
            region = "US"
        type_ = "STOCK"
    elif len(data_parts) == 3:
        # 格式：BA US STOCK
        code = data_parts[0]
        region = data_parts[1]
        type_ = data_parts[2]
    else:
        # 异常格式，默认美股
        code = data_parts[0]
        region = "US"
        type_ = "STOCK"

    return code, region, type_, func

def get_stock_quote(full_command):
    try:
        code, region, type_, _ = parse_command(full_command)

        url = f"https://api.itick.org/symbol/list?type={type_}&region={region}&code={code}"
        headers = {
            "accept": "application/json",
            "token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        res = response.json()

        if res.get("code") != 0 or not res.get("data"):
            return f"[red]Error:[/red] No data for {code} {region} {type_}"

        data_list = res["data"]
        target = None
        for item in data_list:
            if item.get("c", "").upper() == code.upper():
                target = item
                break
        if not target and data_list:
            target = data_list[0]

        table = Table(title=f"{target.get('n', 'Name')} ({target.get('c', code)})", expand=True)
        table.add_column("Field", style="cyan")
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

def get_stock_chart(full_command):
    try:
        code, region, type_, _ = parse_command(full_command)

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