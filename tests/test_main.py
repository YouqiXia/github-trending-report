import os
from unittest.mock import patch, MagicMock
from scripts.main import load_config, run


def test_load_config(tmp_path):
    """应正确加载 YAML 配置。"""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        "trending:\n  source: ossinsight\n  count: 5\n  period: past_24_hours\n"
        "llm:\n  provider: openai\n  model: codex-mini-latest\n  max_readme_length: 8000\n"
        "push:\n  channel: wechat_work\n  summary_first: true\n"
    )
    config = load_config(str(config_file))
    assert config["trending"]["source"] == "ossinsight"
    assert config["trending"]["count"] == 5
    assert config["llm"]["model"] == "codex-mini-latest"


@patch("scripts.main.push_repo_report")
@patch("scripts.main.push_summary")
@patch("scripts.main.analyze_repo")
@patch("scripts.main.fetch_repo_details")
@patch("scripts.main.fetch_trending_list")
def test_run_full_pipeline(mock_fetch_list, mock_fetch_details, mock_analyze, mock_push_summary, mock_push_report):
    """应按顺序执行：抓取列表→获取详情→分析→推送。"""
    mock_fetch_list.return_value = [
        {"repo_name": "a/b", "stars": 100, "stars_today": 20, "language": "Python"},
    ]
    mock_fetch_details.return_value = {
        "repo_name": "a/b",
        "description": "test",
        "topics": [],
        "language": "Python",
        "stars": 100,
        "stars_today": 20,
        "created_at": "2025-01-01",
        "readme_content": "# Hello",
        "recent_issues": [],
        "recent_commits": [],
    }
    mock_analyze.return_value = "▸ 背景：测试"

    config = {
        "trending": {"source": "ossinsight", "count": 1, "period": "past_24_hours"},
        "llm": {"provider": "openai", "model": "codex-mini-latest", "max_readme_length": 8000},
        "push": {"channel": "wechat_work", "summary_first": True},
    }

    run(
        config=config,
        prompt_template="Analyze {{repo_name}}",
        api_key="fake-key",
        webhook_url="https://hook.example.com/xxx",
        github_token="fake-gh-token",
    )

    mock_fetch_list.assert_called_once_with(source="ossinsight", count=1, period="past_24_hours")
    mock_fetch_details.assert_called_once()
    mock_analyze.assert_called_once()
    mock_push_summary.assert_called_once()
    mock_push_report.assert_called_once()
