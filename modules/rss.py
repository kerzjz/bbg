import feedparser
import requests
from rich.table import Table
from datetime import datetime

# 精选稳定、无反爬、适配国内网络的财经RSS源
RSS_SOURCE_POOL = {
    "SINA": "https://finance.sina.com.cn/rss/finance.xml",
    "EASTMONEY": "https://rss.eastmoney.com/rss/finance.xml",
    "WALLSTREET": "https://rss.wallstreetcn.com/feed",
    "CNFIN": "http://rss.cnfinancial.com/rss/finance.xml",
    "SEC": "https://www.sec.gov/rss/news.xml"
}

def get_rss_source_table():
    """生成和股票模块风格一致的RSS源列表表格，解决LIST解析乱码/拆分问题"""
    table = Table(title="📰 RSS AVAILABLE SOURCES", expand=True)
    table.add_column("CODE", style="cyan bold")
    table.add_column("NAME", style="green")
    table.add_column("RSS URL", style="gray")

    for code, url in RSS_SOURCE_POOL.items():
        if "sina" in url.lower():
            name = "新浪财经"
        elif "eastmoney" in url.lower():
            name = "东方财富"
        elif "wallstreetcn" in url.lower():
            name = "华尔街见闻"
        elif "cnfinancial" in url.lower():
            name = "中国财经网"
        elif "sec.gov" in url.lower():
            name = "美国SEC财经"
        else:
            name = "未知财经源"
        table.add_row(code, name, url)
    return table

def get_rss_news(source_code: str, limit: int = 10) -> str | Table:
    """
    获取RSS新闻
    修复点：严格参数校验、编码兼容、超时兜底、防止命令解析错位
    """
    source_code = source_code.upper().strip()

    # 非法源直接返回提示，不崩程序
    if source_code not in RSS_SOURCE_POOL:
        return "[bold red]❌ 无效RSS源！请输入 RSS LIST 查看可用代码[/bold red]"

    # 条数容错，防止输入非数字报错
    try:
        limit = int(limit)
        limit = max(1, min(limit, 30))
    except:
        limit = 10

    try:
        # 超时+请求头防拦截
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(
            RSS_SOURCE_POOL[source_code],
            headers=headers,
            timeout=8
        )
        resp.encoding = "utf-8"

        feed = feedparser.parse(resp.text)
        if not feed.entries:
            return "[bold yellow]⚠️ 当前RSS源暂无更新新闻[/bold yellow]"

        # 构造和终端风格统一的输出
        out = f"[bold green]📡 {source_code} 最新财经新闻(前{limit}条)[/bold green]\n"
        for idx, entry in enumerate(feed.entries[:limit], 1):
            title = entry.get("title", "无标题").strip()
            pub_time = entry.get("published", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            link = entry.get("link", "无链接")

            out += f"\n{idx}. [bold white]{title}[/bold white]\n"
            out += f"🕒 {pub_time}\n🔗 {link}\n"

        return out

    except requests.exceptions.Timeout:
        return "[bold red]❌ RSS源请求超时，请稍后重试[/bold red]"
    except Exception as e:
        return f"[bold red]❌ RSS解析异常：{str(e)[:60]}...[/bold red]"
