"""Collector registry.

Configuration:
- Collector names are stable configuration identifiers.
"""

from __future__ import annotations

from global_builder_radar.collectors.apify_actor import ApifyActorCollector
from global_builder_radar.collectors.base import Collector
from global_builder_radar.collectors.github_bounties import GitHubBountySearchCollector
from global_builder_radar.collectors.hackernews import HackerNewsHiringCollector
from global_builder_radar.collectors.opire import OpireNextDataCollector
from global_builder_radar.collectors.reddit import RedditRssCollector
from global_builder_radar.collectors.scrapling_links import ScraplingLinkCollector
from global_builder_radar.models import SourceConfig

COLLECTORS: dict[str, type[Collector]] = {
    "apify_actor": ApifyActorCollector,
    "github_bounty_search": GitHubBountySearchCollector,
    "hackernews_hiring": HackerNewsHiringCollector,
    "opire_next_data": OpireNextDataCollector,
    "reddit_rss": RedditRssCollector,
    "scrapling_links": ScraplingLinkCollector,
}


def build_collector(source: SourceConfig) -> Collector:
    try:
        collector_type = COLLECTORS[source.collector]
    except KeyError as exc:
        raise ValueError(f"Unknown collector type: {source.collector}") from exc
    return collector_type(source)
