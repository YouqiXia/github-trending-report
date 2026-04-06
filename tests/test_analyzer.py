from unittest.mock import patch, MagicMock
from scripts.analyzer import load_prompt_template, build_prompt, analyze_repo


def test_load_prompt_template(tmp_path):
    """应正确读取 prompt 模板文件。"""
    template_file = tmp_path / "test.txt"
    template_file.write_text("Hello {{repo_name}}, stars: {{stars}}")
    result = load_prompt_template(str(template_file))
    assert "{{repo_name}}" in result
    assert "{{stars}}" in result


def test_build_prompt():
    """应将占位符替换为实际数据。"""
    template = "Repo: {{repo_name}}, Lang: {{language}}, Stars: {{stars}}"
    repo_data = {
        "repo_name": "owner/test",
        "language": "Python",
        "stars": 1000,
        "stars_today": 200,
        "description": "A test tool",
        "readme_content": "# Test",
        "topics": ["ai", "tool"],
        "created_at": "2025-01-01",
        "recent_issues": [{"title": "bug"}],
        "recent_commits": [{"message": "fix bug"}],
    }
    result = build_prompt(template, repo_data)
    assert "owner/test" in result
    assert "Python" in result
    assert "1000" in result


@patch("scripts.analyzer.openai.OpenAI")
def test_analyze_repo(mock_openai_cls):
    """应调用 OpenAI API 并返回分析文本。"""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = "▸ 背景：这是测试分析"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    result = analyze_repo(
        prompt="Analyze this repo",
        api_key="fake-key",
        model="codex-mini-latest",
    )
    assert "背景" in result
    mock_client.chat.completions.create.assert_called_once()
