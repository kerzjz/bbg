def get_stock_chart(full_command):
    """K线图表 - 修复错位 + 恢复数据"""
    code, region, cat, _ = parse_command(full_command)
    route = {
        "STOCK": "stock",
        "FUTURE": "future",
        "FOREX": "forex",
        "INDICES": "indices",
        "FUND": "fund",
        "CRYPTO": "crypto"
    }.get(cat.upper(), "forex")

    # ==================== 修复：正确的kType参数 ====================
    j = req(f"{route}/kline", region=region, code=code, kType=1, limit=40)
    data = j.get("data")
    
    if not data:
        return "[red]No KLINE DATA[/red]"

    closes = []
    for item in data:
        try:
            if isinstance(item, dict):
                closes.append(float(item.get("c", 0)))
            else:
                closes.append(float(item[4]))
        except:
            continue

    if len(closes) < 3:
        return "[red]NO DATA[/red]"

    # ==================== 核心：修复错位（固定宽度） ====================
    plt.clear_figure()
    plt.theme('classic')
    plt.plot_size(68, 14)  # 👈 专治错位
    plt.plot(closes, color="green", marker="dot")
    plt.title(f"{code} {cat} DAILY")
    plt.axes(False)
    plt.grid(False)
    return plt.build()