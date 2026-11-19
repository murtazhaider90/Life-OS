import json
import httpx
import pytest

from desktop.client import LifeOSClient, LifeOSConnectionError


def test_sidecar_client_reads_status_and_sends_message():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "version": "0.6.0"})
        if request.url.path == "/api/assistant/status":
            return httpx.Response(200, json={"needs_input": True, "questions": [{"id": "missing_state"}]})
        if request.url.path == "/api/assistant/message":
            payload = json.loads(request.content.decode())
            return httpx.Response(200, json={"reply": f"heard: {payload['text']}", "action": "no_action"})
        return httpx.Response(404)

    client = LifeOSClient(transport=httpx.MockTransport(handler))
    assert client.health()["status"] == "ok"
    assert client.assistant_status()["questions"][0]["id"] == "missing_state"
    assert client.send_message("hello")["reply"] == "heard: hello"


def test_sidecar_client_wraps_connection_errors():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    client = LifeOSClient(transport=httpx.MockTransport(handler))
    with pytest.raises(LifeOSConnectionError):
        client.health()
