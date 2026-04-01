from app.db import init_db
from app.services.catalog_store import ensure_seed_data
from app.routes.search import autocomplete, search


init_db()
ensure_seed_data()


def test_search_exact_match_query_returns_ranked_result() -> None:
    payload = search(q='Tesco Semi Skimmed Milk', limit=20)
    assert payload.results
    assert any('semi skimmed milk' in item.name.lower() for item in payload.results)
    top = payload.results[0]
    assert top.score > 0.6


def test_search_partial_query_returns_results() -> None:
    payload = search(q='semi skimmed', limit=5)
    assert payload.total >= 1
    assert any('semi skimmed' in item.name.lower() for item in payload.results)


def test_search_synonym_query_matches_catalog_terms() -> None:
    payload = search(q='heinz beanz', limit=20)
    assert payload.results
    assert any('beans' in item.name.lower() for item in payload.results)


def test_search_brand_query_returns_brand_matches() -> None:
    payload = search(q='oatly milk', limit=20)
    assert payload.results
    assert any(item.brand.lower() == 'oatly' for item in payload.results)


def test_search_fuzzy_query_handles_typo_like_input() -> None:
    payload = search(q='sem skmmed mlk', limit=20)
    assert payload.results
    assert any('milk' in item.name.lower() for item in payload.results)


def test_autocomplete_returns_short_ranked_suggestions() -> None:
    payload = autocomplete(q='semi skimmed milk', limit=3)
    assert 1 <= payload.total <= 3
    assert payload.suggestions[0].score >= payload.suggestions[-1].score
