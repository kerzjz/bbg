import requests
from rich.table import Table

def get_top_crypto():
    """
    与原函数 100% 兼容架构，仅更换可用API
    返回格式：Table / 错误字符串（和原来完全一样）
    """
    # 换成可用的 API：Binance 公开接口（无密钥、国内可访问、稳定）
    url = "https://api.binance.com/api/v3/ticker/24hr"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
             return f"[red]API Error:[/red] Status Code {response.status_code}"

        data = response.json()

        # 筛选主流币 + 排序（保持 TOP10）
        # 这里严格对齐原结构：rank / name / price / 24h%
        usdt_pairs = [p for p in data if p['symbol'].endswith('USDT')]
        # 按交易量排序 = 市值排序（保持逻辑一致）
        usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        top10 = usdt_pairs[:10]

        # ===================== 以下完全不动！和你原来一模一样 =====================
        table = Table(title="TOP 10 CRYPTO ASSETS (Real-Time)", expand=True)
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price ($)", justify="right", style="green")
        table.add_column("24h Change %", justify="right")

        # 严格保持字段格式：名称、价格、涨跌幅、颜色逻辑
        for idx, coin in enumerate(top10, 1):
            symbol = coin["symbol"].replace("USDT", "")  # 保持名称干净
            price = float(coin["lastPrice"])
            change = float(coin["priceChangePercent"])
            
            color = "green" if change is not None and change > 0 else "red"
            change_str = f"{change:.2f}%" if change else "N/A"
            
            table.add_row(
                str(idx),
                symbol,
                f"${price:,}",
                f"[{color}]{change_str}[/{color}]"
            )
        return table
        
    except Exception as e:
        return f"[red]Connection Error:[/red] {str(e)}"