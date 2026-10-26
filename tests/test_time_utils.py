import datetime

from cogs.time_utils import JST, now_jst_naive


def test_now_jst_naive_is_naive_jst_wall_clock():
    before = datetime.datetime.now(JST).replace(tzinfo=None)
    value = now_jst_naive()
    after = datetime.datetime.now(JST).replace(tzinfo=None)
    assert value.tzinfo is None
    assert before <= value <= after


def test_now_jst_naive_differs_from_utc_by_nine_hours():
    utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    jst_now = now_jst_naive()
    delta = (jst_now - utc_now).total_seconds()
    # 実行をまたぐ誤差を許しても、9時間±数秒の範囲にある
    assert 9 * 3600 - 10 < delta < 9 * 3600 + 10
