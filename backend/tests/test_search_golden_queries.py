from app.db import init_db
from app.routes.search import autocomplete, search
from app.services.catalog_store import ensure_seed_data


init_db()
ensure_seed_data()


def _assert_search_has_expected_signal(query: str, expected_terms: list[str]) -> None:
    payload = search(q=query, limit=10)
    assert payload.total > 0
    names = [item.name.lower() for item in payload.results[:5]]
    joined = " ".join(names)
    assert any(term in joined for term in expected_terms), f"query={query!r} top_names={names!r}"


def _assert_autocomplete_has_expected_signal(query: str, expected_terms: list[str]) -> None:
    payload = autocomplete(q=query, limit=5)
    assert payload.total > 0
    suggestions = [item.suggestion.lower() for item in payload.suggestions]
    joined = " ".join(suggestions)
    assert any(term in joined for term in expected_terms), f"query={query!r} suggestions={suggestions!r}"


def test_golden_queries_search_relevance() -> None:
    checks = [
        ("semi skimmed milk", ["semi skimmed", "milk"]),
        ("oatly milk", ["oatly", "milk"]),
        ("heinz baked beans", ["heinz", "beans"]),
        ("cheddar 400g", ["cheddar", "400g", "400 g"]),
        ("warburtons bread", ["warburtons", "bread"]),
        ("eggs large free range", ["egg", "free range"]),
    ]
    for query, expected_terms in checks:
        _assert_search_has_expected_signal(query, expected_terms)


def test_golden_queries_autocomplete_relevance() -> None:
    checks = [
        ("semi skimmed milk", ["milk", "semi skimmed"]),
        ("oatly milk", ["oatly", "milk"]),
        ("heinz baked beans", ["beans", "heinz"]),
        ("cheddar 400g", ["cheddar"]),
        ("warburtons bread", ["bread", "warburtons"]),
        ("eggs large free range", ["egg", "free range"]),
    ]
    for query, expected_terms in checks:
        _assert_autocomplete_has_expected_signal(query, expected_terms)
