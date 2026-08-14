from global_builder_radar.models import Opportunity, OpportunityCategory, canonicalize_url


def test_canonicalize_url_removes_tracking_and_fragment() -> None:
    result = canonicalize_url("HTTPS://Example.com/job/?utm_source=x&id=7#apply")
    assert result == "https://example.com/job?id=7"


def test_fingerprint_is_stable_for_same_external_id() -> None:
    first = Opportunity(
        source="test",
        category=OpportunityCategory.BOUNTY,
        external_id="42",
        title="First title",
        url="https://example.com/a",
    )
    second = Opportunity(
        source="test",
        category=OpportunityCategory.BOUNTY,
        external_id="42",
        title="Changed title",
        url="https://example.com/b",
    )
    assert first.fingerprint == second.fingerprint
