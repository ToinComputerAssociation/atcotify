import pytest

from cogs import delivery_state as ds

CONTEST = {
    "name": "AtCoder ABC 001",
    "start_time": "2026-10-31 21:00:00",
    "url": "https://atcoder.jp/contests/abc001",
}


@pytest.fixture
def state_path(tmp_path):
    return tmp_path / "delivery_state.json"


def test_contest_key_prefers_url():
    assert ds.contest_key(CONTEST) == "https://atcoder.jp/contests/abc001"


def test_contest_key_fallback():
    contest = {"name": "ABC 001", "start_time": "2026-10-31 21:00:00", "url": ""}
    assert ds.contest_key(contest) == "ABC 001@2026-10-31 21:00:00"


def test_mark_and_is_delivered_per_guild():
    state = ds.empty_delivery_state()
    key = ds.contest_key(CONTEST)
    assert not ds.is_delivered(state, ds.KIND_RESULT_SENT, key, 111)
    assert ds.mark_delivered(state, ds.KIND_RESULT_SENT, key, 111) is True
    assert ds.is_delivered(state, ds.KIND_RESULT_SENT, key, 111)
    # 別サーバーは未送信のまま
    assert not ds.is_delivered(state, ds.KIND_RESULT_SENT, key, 222)
    # 二重記録は False
    assert ds.mark_delivered(state, ds.KIND_RESULT_SENT, key, 111) is False
    # 種類が違えば独立
    assert not ds.is_delivered(state, ds.KIND_THREADS_CREATED, key, 111)


def test_persistence_roundtrip(state_path):
    state = ds.empty_delivery_state()
    key = ds.contest_key(CONTEST)
    ds.mark_delivered(state, ds.KIND_THREADS_CREATED, key, 111)
    ds.mark_delivered(state, ds.KIND_RESULT_SENT, key, 111)
    ds.mark_delivered(state, ds.KIND_RESULT_SENT, key, 222)
    ds.save_delivery_state(state, state_path)

    loaded = ds.load_delivery_state(state_path)
    assert ds.is_delivered(loaded, ds.KIND_THREADS_CREATED, key, 111)
    assert ds.is_delivered(loaded, ds.KIND_RESULT_SENT, key, 111)
    assert ds.is_delivered(loaded, ds.KIND_RESULT_SENT, key, 222)
    assert not ds.is_delivered(loaded, ds.KIND_THREADS_CREATED, key, 222)


def test_state_survives_contest_list_refresh(state_path):
    """コンテスト情報が新しいdictに差し替わっても配信状態は維持される。"""
    state = ds.empty_delivery_state()
    key = ds.contest_key(CONTEST)
    ds.mark_delivered(state, ds.KIND_RESULT_SENT, key, 111)
    ds.save_delivery_state(state, state_path)

    # 24時間ごとの取得で作り直される新しいコンテストdict（フラグなし）
    refreshed_contest = {
        "name": "AtCoder ABC 001",
        "start_time": "2026-10-31 21:00:00",
        "end_time": "2026-10-31 22:40:00",
        "url": "https://atcoder.jp/contests/abc001",
    }
    loaded = ds.load_delivery_state(state_path)
    assert ds.contest_key(refreshed_contest) == key
    assert ds.is_delivered(loaded, ds.KIND_RESULT_SENT, ds.contest_key(refreshed_contest), 111)


def test_load_missing_file_returns_empty(state_path):
    assert ds.load_delivery_state(state_path) == ds.empty_delivery_state()
