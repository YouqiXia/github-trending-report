from unittest.mock import patch, MagicMock
from scripts.pusher import send_wechat_message, push_summary, push_repo_report


@patch("scripts.pusher.requests.post")
def test_send_wechat_message(mock_post):
    """应 POST markdown 消息到 Webhook URL。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"errcode": 0}
    mock_post.return_value = mock_resp

    send_wechat_message("https://hook.example.com/xxx", "# Hello")
    mock_post.assert_called_once()
    call_json = mock_post.call_args[1]["json"]
    assert call_json["msgtype"] == "markdown"
    assert call_json["markdown"]["content"] == "# Hello"


@patch("scripts.pusher.send_wechat_message")
def test_push_summary(mock_send):
    """应格式化并发送今日概览。"""
    repos = [
        {"repo_name": "a/b", "stars": 100, "stars_today": 20, "language": "Python"},
        {"repo_name": "c/d", "stars": 200, "stars_today": 50, "language": "Rust"},
    ]
    push_summary("https://hook.example.com/xxx", repos)
    mock_send.assert_called_once()
    content = mock_send.call_args[0][1]
    assert "a/b" in content
    assert "c/d" in content


@patch("scripts.pusher.send_wechat_message")
def test_push_repo_report(mock_send):
    """应格式化并发送单仓库报告。"""
    repo = {"repo_name": "a/b", "stars": 100, "stars_today": 20, "language": "Python"}
    analysis = "▸ 背景：测试背景\n▸ 痛点：测试痛点"
    push_repo_report("https://hook.example.com/xxx", repo, analysis)
    mock_send.assert_called_once()
    content = mock_send.call_args[0][1]
    assert "a/b" in content
    assert "测试背景" in content


@patch("scripts.pusher.requests.post")
def test_send_wechat_message_truncates_long_content(mock_post):
    """超过 4096 字节的消息应被截断。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"errcode": 0}
    mock_post.return_value = mock_resp

    long_content = "A" * 5000
    send_wechat_message("https://hook.example.com/xxx", long_content)
    call_json = mock_post.call_args[1]["json"]
    assert len(call_json["markdown"]["content"].encode("utf-8")) <= 4096
