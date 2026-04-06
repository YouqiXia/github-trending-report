"""主入口：编排 抓取 → 分析 → 推送 流程。"""
import os
import sys
from datetime import datetime, timezone, timedelta

import yaml

from scripts.fetcher import fetch_trending_list, fetch_repo_details
from scripts.analyzer import load_prompt_template, build_prompt, analyze_repo
from scripts.pusher import create_issue, build_summary_section, build_repo_section


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(
    config: dict,
    prompt_template: str,
    api_key: str,
    github_token: str,
    issue_repo: str,
) -> None:
    trending_cfg = config["trending"]
    llm_cfg = config["llm"]

    print(f"Fetching trending repos (source={trending_cfg['source']}, count={trending_cfg['count']})...")
    repos = fetch_trending_list(
        source=trending_cfg["source"],
        count=trending_cfg["count"],
        period=trending_cfg["period"],
    )
    if not repos:
        print("No trending repos found. Exiting.")
        return

    print(f"Found {len(repos)} trending repos.")

    # 构建报告内容
    sections = [build_summary_section(repos), "\n---\n"]

    for i, repo in enumerate(repos, 1):
        repo_name = repo["repo_name"]
        print(f"[{i}/{len(repos)}] Processing {repo_name}...")

        details = fetch_repo_details(
            repo_name,
            github_token=github_token,
            max_readme_length=llm_cfg.get("max_readme_length", 8000),
        )
        details["stars_today"] = repo.get("stars_today", 0)

        prompt = build_prompt(prompt_template, details)
        analysis = analyze_repo(
            prompt, api_key=api_key, model=llm_cfg["model"],
            base_url=llm_cfg.get("base_url"),
        )

        sections.append(build_repo_section(details, analysis))
        sections.append("\n---\n")

    # 创建 Issue
    beijing_tz = timezone(timedelta(hours=8))
    today = datetime.now(beijing_tz).strftime("%Y-%m-%d")
    title = f"GitHub Trending 日报 | {today}"
    body = "\n".join(sections)

    print("Creating issue...")
    issue_url = create_issue(
        repo=issue_repo,
        title=title,
        body=body,
        github_token=github_token,
        labels=["daily-report"],
    )
    print(f"Done. Issue created: {issue_url}")


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = load_config(os.path.join(project_root, "config.yml"))
    prompt_template = load_prompt_template(os.path.join(project_root, "prompts", "analyze-repo.txt"))

    api_key = os.environ.get("LLM_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    issue_repo = os.environ.get("ISSUE_REPO", config.get("push", {}).get("issue_repo", ""))

    if not api_key:
        print("ERROR: LLM_API_KEY not set.")
        sys.exit(1)
    if not github_token:
        print("ERROR: GITHUB_TOKEN not set.")
        sys.exit(1)
    if not issue_repo:
        print("ERROR: ISSUE_REPO not set.")
        sys.exit(1)

    run(config, prompt_template, api_key, github_token, issue_repo)


if __name__ == "__main__":
    main()
