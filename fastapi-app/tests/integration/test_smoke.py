import os
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000") 
TIMEOUT = 5

def test_root_alive():
    r = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
    assert r.status_code in (200, 404)

def test_docs_endpoint():
    r = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
    assert r.status_code in (200, 401, 403)

def test_health_optional():
    r = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert r.status_code in (200, 204)
