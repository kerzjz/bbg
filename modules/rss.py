import feedparser
import requests

# 就用你指定的这一个 RSS，不换！
RSS_SOURCE = "https://plink.anyfeeder.com/weixin/wallstreetcn"

def get_rss_list():
    return (
        "[bold cyan]📰 RSS 已启用（华尔街见闻微信）[/bold cyan]\n"
        "命令：\n"
        "RSS        → 查看最新 10 条\n"
        "RSS 5      → 查看最新 5 条\n"
        "RSS LIST   → 查看说明"
    )

def get_rss_news(limit=10):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(RSS_SOURCE, headers=headers, timeout=12)
        resp.encoding = "utf-8"
        feed = feedparser.parse(resp.text)

        if not feed.entries:
            return "[bold red]❌ 未获取到任何新闻[/bold red]"

        # 只取标题 + 做成超链接，不显示 URL
        out = "[bold green]✅ 华尔街见闻（微信）最新新闻[/bold green]\n"
        for i, entry in enumerate(feed.entries[:limit]):
            title = entry.get("title", "无标题")
            link = entry.get("link", "")

            # Rich / Textual 超链接格式：[link=URL]文字[/link]
            out += f"\n{i+1}. [link={link}]{title}[/link]"

        return out

    except Exception as e:
        return f"[bold red]❌ 获取失败：{str(e)[:50]}[/bold red]"