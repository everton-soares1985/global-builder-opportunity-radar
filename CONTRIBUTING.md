# Contributing

Contributions are welcome when they keep sources isolated and preserve evidence.

1. Create a focused branch.
2. Add or update an offline fixture for every parser change.
3. Run `python -X utf8 -m pytest`.
4. Run `python -X utf8 -m ruff check .`.
5. Describe the source, access method, and known limitations in `docs/sources.md`.

Do not commit credentials, session cookies, personal data, or scraped datasets.
