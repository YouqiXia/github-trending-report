"""AI 分析模块。

读取 prompt 模板，填充仓库数据，调用 OpenAI Codex API 生成分析报告。
"""
import json

import openai


def load_prompt_template(template_path: str) -> str:
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(template: str, repo_data: dict) -> str:
    """将模板中的占位符替换为实际仓库数据。"""
    replacements = {
        "{{repo_name}}": str(repo_data.get("repo_name", "")),
        "{{repo_description}}": str(repo_data.get("description", "")),
        "{{language}}": str(repo_data.get("language", "")),
        "{{stars}}": str(repo_data.get("stars", 0)),
        "{{stars_today}}": str(repo_data.get("stars_today", 0)),
        "{{created_at}}": str(repo_data.get("created_at", "")),
        "{{topics}}": ", ".join(repo_data.get("topics", [])),
        "{{readme_content}}": str(repo_data.get("readme_content", "")),
        "{{recent_issues}}": json.dumps(repo_data.get("recent_issues", []), ensure_ascii=False),
        "{{recent_commits}}": json.dumps(repo_data.get("recent_commits", []), ensure_ascii=False),
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def analyze_repo(prompt: str, api_key: str, model: str, base_url: str | None = None) -> str:
    """调用 OpenAI API 分析仓库，返回分析文本。"""
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = openai.OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content
