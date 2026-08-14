from global_builder_radar.collectors.base import first_compensation, first_email


def test_extracts_currency_before_or_after_amount() -> None:
    assert first_compensation("Budget: USD 1,500") == "USD 1,500"
    assert first_compensation("Prize 5,000 USDC") == "5,000 USDC"
    assert first_compensation("Full-time | $150K-$210K + equity") == "$150K-$210K"
    assert first_compensation("Salary range AU$120–160k") == "AU$120–160k"


def test_ignores_company_value_and_market_size() -> None:
    assert first_compensation("AI agents for a $1T+ insurance industry") is None
    assert first_compensation("We process $3.5B in annual GMV") is None
    assert first_compensation("Bootstrapped to $1M in contracted revenue") is None
    assert first_compensation("Full-time company serving a $1T industry") is None


def test_accepts_small_explicit_bounty() -> None:
    assert first_compensation("Reward: $3 USDC on merge") == "$3 USDC"


def test_extracts_public_email() -> None:
    assert first_email("Contact jobs@example.com to apply") == "jobs@example.com"
