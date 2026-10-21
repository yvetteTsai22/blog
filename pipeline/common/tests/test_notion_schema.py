from common import notion_schema as ns


def test_every_select_has_options_and_is_a_select():
    for prop, options in ns.SELECT_OPTIONS.items():
        assert ns.ADDED_PROPERTIES[prop] == "select"
        assert options and len(set(options)) == len(options)
    selects = {p for p, t in ns.ADDED_PROPERTIES.items() if t == "select"}
    assert selects == set(ns.SELECT_OPTIONS)


def test_spec_section_2_values():
    assert ns.PICK_STATUS_OPTIONS == ("未推薦", "推薦過", "挑中", "放棄")
    assert ns.MARKET_STATUS_OPTIONS == ("b", "a+b", "insufficient")
    assert ns.BLOG_STATUS_OPTIONS == ("寫作中", "已發表", "放棄")
    assert ns.SOURCE_OPTIONS == ("manual", "agent-session")
    assert set(ns.PICK_POOL_STATES) <= set(ns.PICK_STATUS_OPTIONS)


def test_added_property_names_do_not_clash_with_existing():
    existing = {ns.TITLE, ns.NOTE_TYPE, ns.STATUS, ns.PARENT_ITEM, ns.CREATE_DATE}
    assert not existing & set(ns.ADDED_PROPERTIES)
    assert len(ns.ADDED_PROPERTIES) == 30
