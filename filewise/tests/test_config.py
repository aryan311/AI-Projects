import os

from filewise.config import Config


def test_defaults() -> None:
    for k in list(os.environ):
        if k.startswith("FILEWISE_"):
            del os.environ[k]
    cfg = Config.from_env()
    assert cfg.embed_model == "fake"
    assert cfg.llm == "fake:echo"
    assert cfg.chunk_size == 800
    assert cfg.chunk_overlap == 120
    assert cfg.retrieval_k == 5
    assert cfg.score_threshold == 0.35
    assert cfg.max_upload_bytes == 25 * 1024 * 1024


def test_env_overrides(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("FILEWISE_CHUNK_SIZE", "400")
    monkeypatch.setenv("FILEWISE_SCORE_THRESHOLD", "0.5")
    cfg = Config.from_env()
    assert cfg.chunk_size == 400
    assert cfg.score_threshold == 0.5
