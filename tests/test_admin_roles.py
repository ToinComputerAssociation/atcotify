import types

from cogs.admin_roles import is_assignable_admin_role


def fake_role(is_default):
    return types.SimpleNamespace(is_default=lambda: is_default)


def test_everyone_role_is_not_assignable():
    assert not is_assignable_admin_role(fake_role(True))


def test_normal_role_is_assignable():
    assert is_assignable_admin_role(fake_role(False))
