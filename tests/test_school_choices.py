import pandas as pd

from cogs.school_rank import collect_school_names, filter_school_choices

SCHOOLS = [
    ("開成高等学校", "high"),
    ("開成中学校", "junior_high"),
    ("筑波大学附属中学校", "junior_high"),
    ("筑波大学附属高等学校", "high"),
]


def fake_tables():
    junior = pd.DataFrame({"学校名": ["筑波大学附属中学校", "開成中学校", "筑波大学附属中学校"]})
    high = pd.DataFrame({"学校名": ["筑波大学附属高等学校", "開成高等学校"]})
    return {
        "junior_high": ({"1年": junior}, {}),
        "high": ({"1年": high}, {}),
    }


def test_collect_school_names_dedupes_and_sorts():
    schools = collect_school_names(fake_tables())
    assert schools == sorted(SCHOOLS)
    assert len(schools) == len(set(schools))


def test_filter_empty_query_returns_first_page():
    assert filter_school_choices(SCHOOLS, "") == SCHOOLS
    assert filter_school_choices(SCHOOLS, "", limit=2) == SCHOOLS[:2]


def test_filter_by_partial_name():
    assert filter_school_choices(SCHOOLS, "開成") == [
        ("開成高等学校", "high"),
        ("開成中学校", "junior_high"),
    ]


def test_filter_by_abbreviation():
    # asset/school_abbreviations.yaml の略称（筑附）でも検索できる
    assert filter_school_choices(SCHOOLS, "筑附") == [
        ("筑波大学附属中学校", "junior_high"),
        ("筑波大学附属高等学校", "high"),
    ]
