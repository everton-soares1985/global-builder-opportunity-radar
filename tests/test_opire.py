import json

from global_builder_radar.collectors.opire import parse_initial_rewards, resolve_reward_amount


def test_parse_initial_rewards_from_next_flight_chunk() -> None:
    rewards = [
        {
            "id": "01TEST",
            "title": "Build a Python integration",
            "url": "https://github.com/example/project/issues/1",
        }
    ]
    payload = f'c:["$",null,{{"initialRewards":{json.dumps(rewards)},"next":null}}]'
    script = f"self.__next_f.push({json.dumps([1, payload])})"
    assert parse_initial_rewards([script]) == rewards


def test_parse_initial_rewards_returns_empty_for_unrelated_script() -> None:
    assert parse_initial_rewards(["console.log('hello')"]) == []


def test_resolve_reward_amount_prefers_explicit_title_evidence() -> None:
    reward = {
        "title": "[BOUNTY] Kickama #304 - deterministic data seed ($50)",
        "pendingPrice": {"value": 10_010_000, "unit": "USD_CENT"},
    }
    assert resolve_reward_amount(reward) == "USD 50.00"


def test_resolve_reward_amount_uses_pending_price_when_consistent() -> None:
    reward = {
        "title": "Fix pagination loop",
        "pendingPrice": {"value": 13_000, "unit": "USD_CENT"},
    }
    assert resolve_reward_amount(reward) == "USD 130.00"


def test_resolve_reward_amount_unknown_without_evidence() -> None:
    assert resolve_reward_amount({"title": "No amount anywhere"}) is None
