import feedparser
import requests
from rich.table import Table
from datetime import datetime

# 精选稳定、无反爬、适配国内网络的财经RSS源
RSS_SOURCE_POOL = {
    "HUXIU": "https://rss.huxiu.com",
#     "ECONOMIST": "https://economistnew.buzzing.cc/feed.xml ",
    "WSCN": "https://plink.anyfeeder.com/weixin/wallstreetcn",
    "NTS": "https://www.newtimespace.com/feed/rss_template.xml?id=100000&site=rss&lang=zh-cn",
#     "HEXUN": "https://news.hexun.com/rss/www_rss.xml", # 停更了
#     "BBG": "https://bloombergnew.buzzing.cc/feed.xml",
#     "FCB": "https://plink.anyfeeder.com/fortunechina/shangye", 
#     "FTCN": "https://www.ftchinese.com/rss/feed"
}

def get_rss_source_table():
    """生成和股票模块风格一致的RSS源列表表格，修复颜色报错"""
    table = Table(title="📰 RSS AVAILABLE SOURCES", expand=True)
    table.add_column("CODE", style="cyan bold")
    table.add_column("NAME", style="green")
    # 把 gray 改成 dim ！！！修复核心
    table.add_column("RSS URL", style="dim")

    for code, url in RSS_SOURCE_POOL.items():
        url_lower = url.lower()  # 统一转小写，只执行一次
        if "huxiu" in url_lower:
            name = "虎嗅"
#         elif "economist" in url_lower:
#             name = "经济学人"
        elif "wallstreetcn" in url_lower:
            name = "华尔街见闻"
        elif "newtimespace" in url_lower:
            name = "新时空"
#         elif "hexun" in url_lower: # 停更了
#             name = "和讯"    
#         elif "bloomberg" in url_lower:  # 更精准
#             name = "彭博社"
#         elif "fortunechina" in url_lower:  # ✅ 修复这里
#             name = "商业 - 财富中文网"
#         elif "ftchinese" in url_lower:     # ✅ 修复这里
#             name = "FTChinese"    
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