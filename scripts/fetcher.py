"""GitHub Trending 数据抓取模块。

支持 OSSInsight API（优先）和 GitHub Trending 页面爬取（降级）。
通过 GitHub REST API 获取每个仓库的详细信息。
"""
import base64
import re

import requests
from bs4 import BeautifulSoup


def fetch_trending_list(source: str, count: int, period: str) -> list[dict]:
    """获取 Trending 仓库列表。

    先尝试 OSSInsight API，失败则降级到页面爬取。
    返回 list of dict，每个 dict 至少包含 repo_name 字段。
    """
    if source == "ossinsight":
        repos = _fetch_from_ossinsight(count, period)
        if repos:
            return repos

    return _fetch_from_scrape(count)


def _fetch_from_ossinsight(count: int, period: str) -> list[dict]:
    url = "https://api.ossinsight.io/v1/trends/repos/"
    params = {"period": period, "limit": count}
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        return []

    data = resp.json().get("data", [])
    return [
        {
            "repo_name": item["repo_name"],
            "language": item.get("language", ""),
            "stars": item.get("stars", 0),
            "forks": item.get("forks", 0),
            "description": item.get("description", ""),
        }
        for item in data[:count]
    ]


def _fetch_from_scrape(count: int) -> list[dict]:
    resp = requests.get("https://github.com/trending", timeout=30)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []
    for article in soup.select("article.Box-row")[:count]:
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        href = h2.get("href", "").strip("/")
        name = re.sub(r"\s+", "", href)
        lang_el = article.select_one("[itemprop='programmingLanguage']")
        language = lang_el.get_text(strip=True) if lang_el else ""
        repos.append({
            "repo_name": name,
            "language": language,
            "stars": 0,
            "forks": 0,
            "description": "",
        })
    return repos


def fetch_repo_details(
    repo_name: str,
    github_token: str | None = None,
    max_readme_length: int = 8000,
) -> dict:
    """从 GitHub REST API 获取仓库详细信息。"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    base_url = f"https://api.github.com/repos/{repo_name}"

    # 基本信息
    repo_resp = requests.get(base_url, headers=headers, timeout=30)
    repo_data = repo_resp.json() if repo_resp.status_code == 200 else {}

    # README
    readme_content = ""
    readme_resp = requests.get(f"{base_url}/readme", headers=headers, timeout=30)
    if readme_resp.status_code == 200:
        readme_data = readme_resp.json()
        if readme_data.get("encoding") == "base64":
            raw = base64.b64decode(readme_data.get("content", "")).decode("utf-8", errors="replace")
            readme_content = raw[:max_readme_length]

    # 最近 Issues
    issues_resp = requests.get(
        f"{base_url}/issues",
        headers=headers,
        params={"per_page": 10, "state": "open", "sort": "created", "direction": "desc"},
        timeout=30,
    )
    recent_issues = []
    if issues_resp.status_code == 200:
        recent_issues = [{"title": i["title"]} for i in issues_resp.json()[:10]]

    # 最近 Commits
    commits_resp = requests.get(
        f"{base_url}/commits",
        headers=headers,
        params={"per_page": 10},
        timeout=30,
    )
    recent_commits = []
    if commits_resp.status_code == 200:
        recent_commits = [
            {"message": c["commit"]["message"].split("\n")[0]}
            for c in commits_resp.json()[:10]
        ]

    return {
        "repo_name": repo_data.get("full_name", repo_name),
        "description": repo_data.get("description", ""),
        "topics": repo_data.get("topics", []),
        "language": repo_data.get("language", ""),
        "stars": repo_data.get("stargazers_count", 0),
        "created_at": repo_data.get("created_at", ""),
        "open_issues_count": repo_data.get("open_issues_count", 0),
        "readme_content": readme_content,
        "recent_issues": recent_issues,
        "recent_commits": recent_commits,
    }
