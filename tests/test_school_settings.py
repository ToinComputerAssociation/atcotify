import pytest

from cogs import school_settings as ss


@pytest.fixture(autouse=True)
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "bot_settings.json"
    monkeypatch.setattr(ss, "BOT_SETTINGS_FILE", path)
    return path


def test_school_roundtrip():
    ss.set_school_for_guild(111, "開成高等学校", "high")
    assert ss.get_school_name_for_guild(111) == "開成高等学校"
    assert ss.get_school_type_for_guild(111) == "high"
    # 別サーバーには影響しない（未設定のサーバーは None）
    assert ss.get_school_name_for_guild(222) is None
    assert ss.get_school_for_guild(111) == ("開成高等学校", "high")
    assert ss.get_school_for_guild(222) is None


def test_unset_school():
    ss.set_school_for_guild(111, "開成高等学校", "high")
    ss.unset_school_name_for_guild(111)
    # 未設定に戻る（デフォルト校には戻らない）
    assert ss.get_school_name_for_guild(111) is None
    assert ss.get_school_type_for_guild(111) is None
    assert ss.get_school_for_guild(111) is None
    assert ss.load_bot_settings() == {}


def test_school_unset_by_default():
    assert ss.get_school_name_for_guild(111) is None
    assert ss.get_school_type_for_guild(111) is None
    assert ss.get_school_for_guild(None) is None


def test_infer_school_type():
    assert ss.infer_school_type("開成高等学校") == "high"
    assert ss.infer_school_type("開成高校") == "high"
    assert ss.infer_school_type("筑波大学附属中学校") == "junior_high"
    # 末尾で判断できない場合は fallback（省略時は中学）
    assert ss.infer_school_type("どこかの学校") == "junior_high"
    assert ss.infer_school_type("どこかの学校", "high") == "high"


def test_admin_role_roundtrip():
    assert ss.get_admin_role_id_for_guild(111) is None
    ss.set_admin_role_id_for_guild(111, 999)
    assert ss.get_admin_role_id_for_guild(111) == 999
    # 文字列で保存されていても int で返る
    assert ss.load_bot_settings()["111"]["admin_role_id"] == "999"
    assert ss.unset_admin_role_id_for_guild(111) is True
    assert ss.get_admin_role_id_for_guild(111) is None
    assert ss.unset_admin_role_id_for_guild(111) is False


def test_admin_role_coexists_with_school():
    ss.set_school_for_guild(111, "開成高等学校", "high")
    ss.set_admin_role_id_for_guild(111, 999)
    assert ss.get_school_name_for_guild(111) == "開成高等学校"
    ss.unset_admin_role_id_for_guild(111)
    # ロールを消しても学校設定は残る
    assert ss.get_school_name_for_guild(111) == "開成高等学校"


def test_normalize_and_format():
    assert ss.normalize_school_type("高校") == "high"
    assert ss.normalize_school_type("high") == "high"
    assert ss.normalize_school_type(None) == "junior_high"
    assert ss.format_school_label("開成", "high") == "開成（高校）"
    assert ss.format_school_label("開成高等学校", "high") == "開成高等学校"
    assert ss.format_school_label("附属中学校", "junior_high") == "附属中学校"


def test_channel_id_roundtrip():
    ss.set_channel_id_for_guild(111, "school_rank_channel_id", 555)
    assert ss.get_channel_id_for_guild(111, "school_rank_channel_id") == "555"
    assert ss.unset_channel_id_for_guild(111, "school_rank_channel_id") is True
    assert ss.get_channel_id_for_guild(111, "school_rank_channel_id") is None
