from unittest.mock import patch, MagicMock
from scripts.pusher import create_issue, build_summary_section, build_repo_section


@patch("scripts.pusher.requests.post")
def test_create_issue(mock_post):
    """应创建 GitHub Issue 并返回 URL。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"html_url": "https://github.com/owner/repo/issues/1"}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    url = create_issue(
        repo="owner/repo",
        title="Test Issue",
        body="Test body",
        github_token="fake-token",
        labels=["daily-report"],
    )
    assert url == "https://github.com/owner/repo/issues/1"
    mock_post.assert_called_once()
    call_json = mock_post.call_args[1]["json"]
    assert call_json["title"] == "Test Issue"
    assert call_json["labels"] == ["daily-report"]


def test_build_summary_section():
    """应生成概览 Markdown。"""
    repos = [
        {"repo_name": "a/b", "stars": 100, "stars_today": 20, "language": "Python"},
        {"repo_name": "c/d", "stars": 200, "stars_today": 50, "language": "Rust"},
    ]
    content = build_summary_section(repos)
    assert "a/b" in content
    assert "c/d" in content
    assert "Python" in content


def test_build_repo_section():
    """应生成单仓库分析 Markdown。"""
    repo = {"repo_name": "a/b", "stars": 100, "stars_today": 20, "language": "Python"}
    analysis = "▸ 背景：测试背景\n▸ 痛点：测试痛点"
    content = build_repo_section(repo, analysis)
    assert "a/b" in content
    assert "测试背景" in content
