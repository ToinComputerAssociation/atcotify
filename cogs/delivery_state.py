"""サーバーごとの配信済み状態（スレッド作成・結果通知）の永続化。

コンテスト情報（asset/contests.yaml）は定期的に取得し直して差し替わるため、
送信済みフラグをコンテスト側に持たせると更新のたびに初期化されてしまう。
配信状態は「コンテストのキー × サーバーID」でこのモジュールが別に保持し、
コンテスト情報が更新されても維持されるようにする。

複数のCogが同じファイルへ書き込むため、状態は DeliveryStateStore を
プロセス内で1つだけ共有して使うこと。Cogごとに読み込んだ辞書を丸ごと
書き戻すと、別Cogの記録を古い状態で上書きしてしまう。
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

DELIVERY_STATE_FILE = Path("asset/delivery_state.json")

KIND_THREADS_CREATED = "threads_created"
KIND_RESULT_SENT = "result_sent"
_KINDS = (KIND_THREADS_CREATED, KIND_RESULT_SENT)
_META_RESULT_ENABLED_AT = "result_enabled_at"


def contest_key(contest: dict[str, Any]) -> str:
    """コンテストを一意に指すキー。URLがあればURL、無ければ名前と開始時刻。"""
    url = str(contest.get("url") or "").strip()
    if url:
        return url
    return f"{contest.get('name', '')}@{contest.get('start_time', '')}"


def empty_delivery_state() -> dict[str, Any]:
    state: dict[str, Any] = {kind: {} for kind in _KINDS}
    state[_META_RESULT_ENABLED_AT] = {}
    return state


def load_delivery_state(path: Path = DELIVERY_STATE_FILE) -> dict[str, Any]:
    state = empty_delivery_state()
    if not path.exists():
        return state

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return state
    for kind in _KINDS:
        entries = data.get(kind)
        if not isinstance(entries, dict):
            continue
        for key, guild_ids in entries.items():
            if isinstance(guild_ids, list):
                state[kind][str(key)] = [str(guild_id) for guild_id in guild_ids]
    enabled_at = data.get(_META_RESULT_ENABLED_AT)
    if isinstance(enabled_at, dict):
        for guild_id, when in enabled_at.items():
            if isinstance(when, str):
                state[_META_RESULT_ENABLED_AT][str(guild_id)] = when
    return state


def save_delivery_state(state: dict[str, Any], path: Path = DELIVERY_STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def is_delivered(state: dict[str, Any], kind: str, key: str, guild_id: int | str) -> bool:
    return str(guild_id) in state.get(kind, {}).get(key, [])


def mark_delivered(state: dict[str, Any], kind: str, key: str, guild_id: int | str) -> bool:
    """配信済みに記録する。新規に記録したら True、既に記録済みなら False。"""
    guild_ids = state.setdefault(kind, {}).setdefault(key, [])
    guild_key = str(guild_id)
    if guild_key in guild_ids:
        return False
    guild_ids.append(guild_key)
    return True


def get_result_enabled_at(state: dict[str, Any], guild_id: int | str) -> str | None:
    """そのサーバーで結果通知が有効になった時刻（未登録なら None）。"""
    return state.get(_META_RESULT_ENABLED_AT, {}).get(str(guild_id))


def ensure_result_enabled_at(state: dict[str, Any], guild_id: int | str, when: str) -> str:
    """結果通知の有効化時刻を未登録なら記録し、登録済みの値を返す。

    導入前に終了したコンテストを一括送信しないための基準時刻として使う。
    """
    enabled = state.setdefault(_META_RESULT_ENABLED_AT, {})
    guild_key = str(guild_id)
    if guild_key not in enabled:
        enabled[guild_key] = when
    return enabled[guild_key]


class DeliveryStateStore:
    """配信状態の共有ストア。Bot全体で1つだけ保持し、全Cogで使い回す。"""

    def __init__(self, path: Path = DELIVERY_STATE_FILE):
        self.path = path
        self.state = load_delivery_state(path)

    def is_delivered(self, kind: str, key: str, guild_id: int | str) -> bool:
        return is_delivered(self.state, kind, key, guild_id)

    def mark_delivered(self, kind: str, key: str, guild_id: int | str) -> bool:
        newly_marked = mark_delivered(self.state, kind, key, guild_id)
        if newly_marked:
            save_delivery_state(self.state, self.path)
        return newly_marked

    def get_result_enabled_at(self, guild_id: int | str) -> str | None:
        return get_result_enabled_at(self.state, guild_id)

    def ensure_result_enabled_at(self, guild_id: int | str, when: str) -> str:
        before = get_result_enabled_at(self.state, guild_id)
        enabled_at = ensure_result_enabled_at(self.state, guild_id, when)
        if before is None:
            save_delivery_state(self.state, self.path)
        return enabled_at


_shared_store: DeliveryStateStore | None = None


def get_shared_store() -> DeliveryStateStore:
    """プロセス共有のストアを返す（初回だけファイルから読み込む）。"""
    global _shared_store
    if _shared_store is None:
        _shared_store = DeliveryStateStore()
    return _shared_store
