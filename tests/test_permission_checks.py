import asyncio
import types

import discord
import pytest

from cogs import school_settings as ss
from cogs.permission_checks import (
    user_can_manage_bot_settings,
    user_is_guild_administrator,
)


@pytest.fixture(autouse=True)
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "bot_settings.json"
    monkeypatch.setattr(ss, "BOT_SETTINGS_FILE", path)
    ss.set_admin_role_id_for_guild(111, 222)
    return path


class FakePerms:
    def __init__(self, administrator):
        self.administrator = administrator


class FakeRole:
    def __init__(self, role_id):
        self.id = role_id


class FakeMember(discord.Member):
    @property
    def guild_permissions(self):
        return self._perms

    @property
    def roles(self):
        return self._roles


def make_interaction(*, administrator=False, role_ids=(), in_guild=True):
    member = object.__new__(FakeMember)
    member._perms = FakePerms(administrator)
    member._roles = [FakeRole(r) for r in role_ids]
    guild = types.SimpleNamespace(id=111) if in_guild else None
    return types.SimpleNamespace(guild=guild, user=member)


def can_manage(interaction):
    return asyncio.run(user_can_manage_bot_settings(interaction))


def is_admin(interaction):
    return asyncio.run(user_is_guild_administrator(interaction))


def test_administrator_can_manage():
    assert can_manage(make_interaction(administrator=True))


def test_admin_role_holder_can_manage():
    assert can_manage(make_interaction(role_ids=[222]))


def test_other_role_cannot_manage():
    assert not can_manage(make_interaction(role_ids=[999]))


def test_plain_member_cannot_manage():
    assert not can_manage(make_interaction())


def test_dm_cannot_manage():
    interaction = make_interaction(administrator=True, in_guild=False)
    assert not can_manage(interaction)


def test_role_from_other_guild_does_not_leak():
    # 別サーバー(333)でだけ副管理者ロールが設定されている状況では、
    # サーバー111で同じロールIDを持っていても管理者扱いにならない
    ss.unset_admin_role_id_for_guild(111)
    ss.set_admin_role_id_for_guild(333, 222)
    assert not can_manage(make_interaction(role_ids=[222]))


def test_is_guild_administrator():
    assert is_admin(make_interaction(administrator=True))
    assert not is_admin(make_interaction(role_ids=[222]))
