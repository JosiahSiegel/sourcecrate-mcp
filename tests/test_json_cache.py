import sqlite3
from concurrent.futures import ThreadPoolExecutor

from source_crate.utils.json_cache import JsonCache


def test_json_roundtrip_expiry_and_isolation(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("source_crate.utils.json_cache.time.time", lambda: clock[0])
    cache = JsonCache(tmp_path)
    original = {"title": "研究", "papers": [{"score": 75.5}]}
    assert cache.set("paper", original, expire=5)
    original["papers"].clear()
    assert JsonCache(tmp_path).get("paper")["papers"] == [{"score": 75.5}]
    clock[0] = 105.0
    assert cache.get("paper") is None


def test_cache_rejects_non_json_and_tampered_payload(tmp_path):
    cache = JsonCache(tmp_path)
    assert not cache.set("object", object())
    assert cache.set("paper", {"title": "safe"})
    with sqlite3.connect(cache.path) as db:
        db.execute("UPDATE entries SET value = ?", (b"\x80\x04pickle-is-never-loaded",))
    assert cache.get("paper") is None
    assert cache.delete("paper")
    assert not cache.delete("paper")


def test_cache_budget_and_concurrent_writers(tmp_path):
    cache = JsonCache(tmp_path, size_limit=50)
    assert not cache.set("oversized", "x" * 51)
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(pool.map(lambda n: cache.set(str(n), "1234567890"), range(12)))
    with sqlite3.connect(cache.path) as db:
        assert db.execute("SELECT SUM(length(value)) FROM entries").fetchone()[0] <= 50
    assert cache.volume() > 0


def test_unwritable_cache_is_optional(tmp_path):
    occupied = tmp_path / "file"
    occupied.write_text("not a directory")
    cache = JsonCache(occupied)
    assert cache.get("key", "fallback") == "fallback"
    assert not cache.set("key", {})
