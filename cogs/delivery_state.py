"""サーバーごとの配信済み状態（スレッド作成・結果通知）の永続化。

コンテスト情報（asset/contests.yaml）は定期的に取得し直して差し替わるため、
送信済みフラグをコンテスト側に持たせると更新のたびに初期化されてしまう。
配信状態は「コンテストのキー × サーバーID」でこのモジュールが別に保持し、
コンテスト情報が更新されても維持されるようにする。
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


def contest_key(contest: dict[str, Any]) -> str:
    """コンテストを一意に指すキー。URLがあればURL、無ければ名前と開始時刻。"""
    url = str(contest.get("url") or "").strip()
    if url:
        return url
    return f"{contest.get('name', '')}@{contest.get('start_time', '')}"


def empty_delivery_state() -> dict[str, dict[str, list[str]]]:
    return {kind: {} for kind in _KINDS}


def load_delivery_state(
    path: Path = DELIVERY_STATE_FILE,
) -> dict[str, dict[str, list[str]]]:
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
    return state


def save_delivery_state(
    state: dict[str, dict[str, list[str]]],
    path: Path = DELIVERY_STATE_FILE,
) -> None:
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


def is_delivered(
    state: dict[str, dict[str, list[str]]],
    kind: str,
    key: str,
    guild_id: int | str,
) -> bool:
    return str(guild_id) in state.get(kind, {}).get(key, [])


def mark_delivered(
    state: dict[str, dict[str, list[str]]],
    kind: str,
    key: str,
    guild_id: int | str,
) -> bool:
    """配信済みに記録する。新規に記録したら True、既に記録済みなら False。"""
    guild_ids = state.setdefault(kind, {}).setdefault(key, [])
    guild_key = str(guild_id)
    if guild_key in guild_ids:
        return False
    guild_ids.append(guild_key)
    return True
