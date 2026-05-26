import math

from filewise.embedding.fake import FakeEmbedding


def test_dim_and_name() -> None:
    e = FakeEmbedding()
    assert e.name == "fake"
    assert e.dim == 64


def test_deterministic() -> None:
    e = FakeEmbedding()
    a = e.embed(["hello world"])[0]
    b = e.embed(["hello world"])[0]
    assert a == b


def test_different_text_different_vec() -> None:
    e = FakeEmbedding()
    a = e.embed(["hello world"])[0]
    b = e.embed(["something totally different"])[0]
    assert a != b


def test_unit_norm() -> None:
    e = FakeEmbedding()
    v = e.embed(["unit norm please"])[0]
    norm = math.sqrt(sum(x * x for x in v))
    assert math.isclose(norm, 1.0, rel_tol=1e-5)


def test_empty_text_is_safe() -> None:
    e = FakeEmbedding()
    v = e.embed([""])[0]
    assert len(v) == 64
    norm = math.sqrt(sum(x * x for x in v))
    assert math.isclose(norm, 1.0, rel_tol=1e-5)
