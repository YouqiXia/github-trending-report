"""企业微信群机器人推送模块。

通过 Webhook 发送 Markdown 格式消息，单条限制 4096 字节。
"""
import time

import requests


MAX_MESSAGE_BYTES = 4096


def send_wechat_message(webhook_url: str, content: str) -> None:
    """发送一条 markdown 消息到企业微信群机器人。"""
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_MESSAGE_BYTES:
        content = encoded[:MAX_MESSAGE_BYTES - 6].decode("utf-8", errors="ignore") + "\n..."

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    requests.post(webhook_url, json=payload, timeout=30)


def push_summary(webhook_url: str, repos: list[dict]) -> None:
    """推送今日概览摘要。"""
    lines = ["**📊 GitHub Trending 日报**\n"]
    for i, repo in enumerate(repos, 1):
        name = repo["repo_name"]
        stars = repo.get("stars", 0)
        today = repo.get("stars_today", 0)
        lang = repo.get("language", "")
        lang_tag = f" [{lang}]" if lang else ""
        lines.append(f"{i}. {name} ⭐{stars} (+{today}){lang_tag}")

    send_wechat_message(webhook_url, "\n".join(lines))


def push_repo_report(webhook_url: str, repo: dict, analysis: str) -> None:
    """推送单个仓库的分析报告。"""
    name = repo["repo_name"]
    stars = repo.get("stars", 0)
    today = repo.get("stars_today", 0)
    lang = repo.get("language", "")
    lang_tag = f"[{lang}] " if lang else ""

    header = f"**📦 {name}** ⭐{stars} (+{today} today)\n{lang_tag}\n"
    content = header + analysis

    send_wechat_message(webhook_url, content)
    time.sleep(1)
