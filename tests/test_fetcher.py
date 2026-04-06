import os
import json
from unittest.mock import patch, MagicMock
from scripts.fetcher import fetch_trending_list, fetch_repo_details


def _make_ossinsight_response(repos):
    """构造 OSSInsight API 响应。"""
    return {
        "data": [
            {"repo_name": r["name"], "language": r.get("language", "Python"),
             "stars": r.get("stars", 100), "forks": r.get("forks", 10),
             "description": r.get("description", "A test repo")}
            for r in repos
        ]
    }


@patch("scripts.fetcher.requests.get")
def test_fetch_trending_list_ossinsight(mock_get):
    """OSSInsight API 正常返回时，应解析出仓库列表。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _make_ossinsight_response([
        {"name": "owner/repo-a", "stars": 500},
        {"name": "owner/repo-b", "stars": 300},
    ])
    mock_get.return_value = mock_resp

    repos = fetch_trending_list(source="ossinsight", count=2, period="past_24_hours")
    assert len(repos) == 2
    assert repos[0]["repo_name"] == "owner/repo-a"
    assert repos[0]["stars"] == 500


@patch("scripts.fetcher.requests.get")
def test_fetch_trending_list_ossinsight_fallback_to_scrape(mock_get):
    """OSSInsight API 失败时，应降级到页面爬取。"""
    fail_resp = MagicMock()
    fail_resp.status_code = 500

    html = """
    <article class="Box-row">
      <h2 class="h3 lh-condensed">
        <a href="/owner/repo-c">owner / repo-c</a>
      </h2>
      <span class="d-inline-block ml-0 mr-3" itemprop="programmingLanguage">Rust</span>
      <a class="Link--muted d-inline-block mr-3" href="/owner/repo-c/stargazers">100</a>
    </article>
    """
    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.text = html

    mock_get.side_effect = [fail_resp, ok_resp]

    repos = fetch_trending_list(source="ossinsight", count=5, period="past_24_hours")
    assert len(repos) >= 1
    assert repos[0]["repo_name"] == "owner/repo-c"


@patch("scripts.fetcher.requests.get")
def test_fetch_repo_details(mock_get):
    """应从 GitHub REST API 获取仓库详情。"""
    repo_resp = MagicMock()
    repo_resp.status_code = 200
    repo_resp.json.return_value = {
        "full_name": "owner/repo-a",
        "description": "A great tool",
        "topics": ["ai", "agent"],
        "language": "Python",
        "stargazers_count": 500,
        "created_at": "2025-01-15T00:00:00Z",
        "open_issues_count": 12,
    }

    readme_resp = MagicMock()
    readme_resp.status_code = 200
    readme_resp.json.return_value = {
        "content": "IyBIZWxsbw==",
        "encoding": "base64",
    }

    issues_resp = MagicMock()
    issues_resp.status_code = 200
    issues_resp.json.return_value = [
        {"title": "Bug: crash on start"},
        {"title": "Feature: add dark mode"},
    ]

    commits_resp = MagicMock()
    commits_resp.status_code = 200
    commits_resp.json.return_value = [
        {"commit": {"message": "fix: resolve startup crash"}},
        {"commit": {"message": "feat: add dark mode support"}},
    ]

    mock_get.side_effect = [repo_resp, readme_resp, issues_resp, commits_resp]

    details = fetch_repo_details("owner/repo-a", github_token="fake-token", max_readme_length=8000)
    assert details["repo_name"] == "owner/repo-a"
    assert details["description"] == "A great tool"
    assert "ai" in details["topics"]
    assert "# Hello" in details["readme_content"]
    assert len(details["recent_issues"]) == 2
    assert len(details["recent_commits"]) == 2
