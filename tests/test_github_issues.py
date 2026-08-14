from global_builder_radar.github_issues import (
    github_issue_api_url,
    is_zero_bounty,
    verdict_from_payload,
)


def test_github_issue_url_maps_to_public_api():
    url = "https://github.com/qtop/qtop/issues/433"
    assert github_issue_api_url(url) == "https://api.github.com/repos/qtop/qtop/issues/433"


def test_github_issue_url_accepts_www_and_trailing_slash():
    assert (
        github_issue_api_url("https://www.github.com/owner/repo/issues/7/")
        == "https://api.github.com/repos/owner/repo/issues/7"
    )


def test_non_issue_urls_are_not_mapped():
    assert github_issue_api_url("https://github.com/owner/repo/pull/12") is None
    assert github_issue_api_url("https://github.com/owner/repo") is None
    assert github_issue_api_url("https://reddit.com/r/forhire") is None
    assert github_issue_api_url("https://github.com/owner/repo/issues") is None


def test_zero_bounty_label_is_detected():
    assert is_zero_bounty([{"name": "zero-bounty"}, {"name": "ready"}])
    assert is_zero_bounty([{"name": "Zero Bounty"}])
    assert not is_zero_bounty([{"name": "bounty"}, {"name": "good first issue"}])
    assert not is_zero_bounty([])
    assert not is_zero_bounty([{"other": "shape"}])


def test_verdict_reads_state_and_labels():
    closed, zero = verdict_from_payload({"state": "closed", "labels": []})
    assert closed and not zero
    closed, zero = verdict_from_payload(
        {"state": "open", "labels": [{"name": "zero-bounty"}]}
    )
    assert not closed and zero
    closed, zero = verdict_from_payload({"state": "open", "labels": "unexpected"})
    assert not closed and not zero
