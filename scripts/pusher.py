"""GitHub Issue 推送模块。

将分析报告以 Issue 形式发布到仓库，通过 GitHub 通知邮件送达。
"""
import requests


def create_issue(
    repo: str,
    title: str,
    body: str,
    github_token: str,
    labels: list[str] | None = None,
) -> str:
    """创建 GitHub Issue，返回 Issue URL。"""
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
    }
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["html_url"]


def build_summary_section(repos: list[dict]) -> str:
    """生成今日概览部分的 Markdown。"""
    lines = ["## 今日概览\n"]
    for i, repo in enumerate(repos, 1):
        name = repo["repo_name"]
        stars = repo.get("stars", 0)
        today = repo.get("stars_today", 0)
        lang = repo.get("language", "")
        lang_tag = f" `{lang}`" if lang else ""
        lines.append(f"{i}. **{name}** ⭐{stars} (+{today}){lang_tag}")
    return "\n".join(lines)


def build_repo_section(repo: dict, analysis: str) -> str:
    """生成单个仓库分析部分的 Markdown。"""
    name = repo["repo_name"]
    stars = repo.get("stars", 0)
    today = repo.get("stars_today", 0)
    lang = repo.get("language", "")
    lang_tag = f"`{lang}` " if lang else ""

    header = f"### {name} ⭐{stars} (+{today} today) {lang_tag}\n"
    return header + "\n" + analysis
