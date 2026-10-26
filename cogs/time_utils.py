"""時刻ユーティリティ。

コンテスト情報は日本時間（JST）の壁時計文字列（tzなし）で保持されている。
比較に使う現在時刻も、実行環境のタイムゾーンに依存しないよう、
常にJSTの壁時計（tzなし）で取得する。
"""

import datetime

JST = datetime.timezone(datetime.timedelta(hours=9), name="JST")


def now_jst_naive() -> datetime.datetime:
    """現在のJST壁時計を tz なし datetime で返す。"""
    return datetime.datetime.now(JST).replace(tzinfo=None)


def jst_timestamp(value: datetime.datetime) -> int:
    """JSTの壁時計（tzなし）を Unix タイムスタンプに変換する。

    time.mktime() は実行環境のローカルタイムゾーンに依存するため使わない。
    Discord の <t:...> 表示などに使う。
    """
    return int(value.replace(tzinfo=JST).timestamp())
