from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from billparser.security import get_api_key

app = FastAPI()


@app.get("/secure-test")
def secure_test_endpoint(api_key: str = Depends(get_api_key)):
    return {"status": "ok", "api_key": api_key}


client = TestClient(app)


def test_secure_endpoint_with_valid_api_key(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("billparser.security.VALID_API_KEYS", {"my-secret-test-key"})
    headers = {"X-API-Key": "my-secret-test-key"}
    response = client.get("/secure-test", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "api_key": "my-secret-test-key"}


def test_secure_endpoint_with_invalid_api_key(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("billparser.security.VALID_API_KEYS", {"my-secret-test-key"})
    headers = {"X-API-Key": "invalid-key"}
    response = client.get("/secure-test", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_secure_endpoint_without_api_key():
    response = client.get("/secure-test")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}
