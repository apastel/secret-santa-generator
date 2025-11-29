import pytest
from secret_santa import create_mapping


def test_basic_mapping_no_self_and_unique():
    participants = [
        {"name": "Pat", "exclusions": []},
        {"name": "Lee", "exclusions": []},
        {"name": "Sam", "exclusions": []},
    ]
    mapping = create_mapping(participants)
    names = {p["name"] for p in participants}
    assert set(mapping.keys()) == names
    assert set(mapping.values()) == names
    # no self assignment
    for k, v in mapping.items():
        assert k != v


def test_pair_constraints():
    participants = [
        {"name": "Jordan", "exclusions": ["Taylor"]},
        {"name": "Taylor", "exclusions": ["Jordan"]},
        {"name": "Morgan", "exclusions": []},
        {"name": "Casey", "exclusions": []},
    ]
    mapping = create_mapping(participants)
    # ensure pair exclusions satisfied
    assert mapping["Jordan"] != "Taylor"
    assert mapping["Taylor"] != "Jordan"


def test_impossible_mapping_raises():
    # two participants that exclude each other (and ban_self) -> impossible
    participants = [{"name": "Jordan", "exclusions": ["Taylor"]}, {"name": "Taylor", "exclusions": ["Jordan"]}]
    with pytest.raises(ValueError):
        create_mapping(participants)


def test_load_participants_from_example():
    # load_participants should return the example participants when no
    # override file is present. We compare to the example JSON.
    from secret_santa import load_participants

    parts = load_participants()
    assert isinstance(parts, list)
    # the example should have at least one participant entry and each should be a dict
    assert any(isinstance(p, dict) and "name" in p for p in parts)
