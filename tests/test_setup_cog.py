from cogs.setup import build_next_steps, describe_setup_state


def test_describe_setup_state_when_set():
    state = describe_setup_state("筑波大学附属中学校", "junior_high", 999)
    assert state["school"] == "筑波大学附属中学校"
    assert state["admin_role"] == "<@&999>"


def test_describe_setup_state_when_unset():
    state = describe_setup_state(None, None, None)
    assert state["school"] == "未設定"
    assert state["admin_role"] == "未設定"


def test_next_steps_prompt_school_when_unset():
    steps = build_next_steps(school_is_set=False)
    assert any("/setup" in step for step in steps)
    assert any("/admin_role_set" in step for step in steps)


def test_next_steps_skip_school_when_set():
    steps = build_next_steps(school_is_set=True)
    assert not any(step.startswith("`/setup 学校名`") for step in steps)
    assert any("/admin_role_set" in step for step in steps)
