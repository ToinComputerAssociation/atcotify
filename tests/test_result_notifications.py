import asyncio
import datetime
import types

import pytest

from cogs import delivery_state as ds
from cogs.result import Contest_result
from cogs.time_utils import now_jst_naive

FMT = "%Y-%m-%d %H:%M:%S"


def make_contest(name, end_time, url):
    return {
        "name": name,
        "start_time": end_time.strftime(FMT),
        "end_time": end_time.strftime(FMT),
        "url": url,
    }


@pytest.fixture
def harness(tmp_path):
    store = ds.DeliveryStateStore(tmp_path / "delivery_state.json")
    cog = object.__new__(Contest_result)
    fake_contest_data = types.SimpleNamespace(contests=[])
    cog.bot = types.SimpleNamespace(
        get_cog=lambda name: fake_contest_data if name == "ContestData" else None
    )
    cog.results_config = {"111": "555"}
    cog.contests = []
    cog.store = store
    cog._result_send_failures = {}
    sent = []

    async def fake_send(contest, guild_id):
        sent.append((contest["name"], str(guild_id)))
        return True

    cog.send_contest_result = fake_send
    return types.SimpleNamespace(
        cog=cog, store=store, contest_data=fake_contest_data, sent=sent
    )


def run(cog):
    asyncio.run(cog._send_due_results())


def set_baseline_in_past(store, guild_id="111"):
    ds.ensure_result_enabled_at(store.state, guild_id, "2026-01-01 00:00:00")
    ds.save_delivery_state(store.state, store.path)


def test_fresh_guild_does_not_receive_past_contests(harness):
    now = now_jst_naive()
    past = make_contest(
        "ABC Past", now - datetime.timedelta(days=30), "https://atcoder.jp/contests/abc_past"
    )
    harness.contest_data.contests = [past]
    run(harness.cog)
    # 導入前に終了したコンテストは送られない
    assert harness.sent == []
    # 基準時刻が記録される
    assert ds.get_result_enabled_at(harness.store.state, "111") is not None


def test_contest_ending_after_baseline_is_sent_once(harness):
    set_baseline_in_past(harness.store)
    now = now_jst_naive()
    ended = make_contest(
        "ABC Ended", now - datetime.timedelta(hours=1), "https://atcoder.jp/contests/abc_ended"
    )
    upcoming = make_contest(
        "ABC Upcoming", now + datetime.timedelta(hours=1), "https://atcoder.jp/contests/abc_upcoming"
    )
    harness.contest_data.contests = [ended, upcoming]
    run(harness.cog)
    assert harness.sent == [("ABC Ended", "111")]
    # 再度回しても再送しない
    run(harness.cog)
    assert harness.sent == [("ABC Ended", "111")]


def test_new_contests_from_refresh_are_picked_up(harness):
    set_baseline_in_past(harness.store)
    now = now_jst_naive()
    first = make_contest(
        "ABC First", now - datetime.timedelta(hours=2), "https://atcoder.jp/contests/abc_first"
    )
    harness.contest_data.contests = [first]
    run(harness.cog)
    assert harness.sent == [("ABC First", "111")]

    # ContestData が24時間更新で新しいコンテストを取り込んだ想定（再起動なし）
    second = make_contest(
        "ABC Second", now - datetime.timedelta(minutes=30), "https://atcoder.jp/contests/abc_second"
    )
    harness.contest_data.contests = [first, second]
    run(harness.cog)
    assert harness.sent == [("ABC First", "111"), ("ABC Second", "111")]


def test_threads_and_results_histories_coexist(harness):
    """スレッド作成と結果通知の履歴が同じストアで互いを消さない。"""
    store = harness.store
    key = "https://atcoder.jp/contests/abc_x"
    store.mark_delivered(ds.KIND_THREADS_CREATED, key, "111")
    store.mark_delivered(ds.KIND_RESULT_SENT, key, "111")

    reloaded = ds.load_delivery_state(store.path)
    assert ds.is_delivered(reloaded, ds.KIND_THREADS_CREATED, key, "111")
    assert ds.is_delivered(reloaded, ds.KIND_RESULT_SENT, key, "111")
