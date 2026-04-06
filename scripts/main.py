"""主入口：编排 抓取 → 分析 → 推送 流程。"""
import os
import sys

import yaml

from scripts.fetcher import fetch_trending_list, fetch_repo_details
from scripts.analyzer import load_prompt_template, build_prompt, analyze_repo
from scripts.pusher import push_summary, push_repo_report


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(
    config: dict,
    prompt_template: str,
    api_key: str,
    webhook_url: str,
    github_token: str | None = None,
) -> None:
    trending_cfg = config["trending"]
    llm_cfg = config["llm"]
    push_cfg = config["push"]

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

    if push_cfg.get("summary_first", True):
        print("Pushing summary...")
        push_summary(webhook_url, repos)

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

        push_repo_report(webhook_url, details, analysis)

    print("Done.")


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = load_config(os.path.join(project_root, "config.yml"))
    prompt_template = load_prompt_template(os.path.join(project_root, "prompts", "analyze-repo.txt"))

    api_key = os.environ.get("LLM_API_KEY")
    webhook_url = os.environ.get("WECHAT_WEBHOOK_URL")
    github_token = os.environ.get("GITHUB_TOKEN")

    if not api_key:
        print("ERROR: LLM_API_KEY not set.")
        sys.exit(1)
    if not webhook_url:
        print("ERROR: WECHAT_WEBHOOK_URL not set.")
        sys.exit(1)

    run(config, prompt_template, api_key, webhook_url, github_token)


if __name__ == "__main__":
    main()
