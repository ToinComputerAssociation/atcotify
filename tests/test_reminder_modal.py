import asyncio
import types

import discord
import pytest

from cogs import school_settings as ss
from cogs.reminder import CustomTimeModal


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


class FakeResponse:
    def __init__(self):
        self.messages = []

    def is_done(self):
        return False

    async def send_message(self, message, ephemeral=False):
        self.messages.append(message)


def make_interaction(*, administrator=False, role_ids=()):
    member = object.__new__(FakeMember)
    member._perms = FakePerms(administrator)
    member._roles = [FakeRole(r) for r in role_ids]
    return types.SimpleNamespace(
        guild=types.SimpleNamespace(id=111),
        user=member,
        response=FakeResponse(),
    )


def make_modal():
    return object.__new__(CustomTimeModal)


def test_modal_rejects_member_without_permission():
    modal = make_modal()
    interaction = make_interaction()
    assert not asyncio.run(modal.interaction_check(interaction))
    assert interaction.response.messages  # 拒否メッセージが送られている


def test_modal_accepts_administrator():
    modal = make_modal()
    interaction = make_interaction(administrator=True)
    assert asyncio.run(modal.interaction_check(interaction))


def test_modal_accepts_admin_role_holder():
    modal = make_modal()
    interaction = make_interaction(role_ids=[222])
    assert asyncio.run(modal.interaction_check(interaction))
