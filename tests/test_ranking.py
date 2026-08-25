from services.ranking_service import highlight, normalize_query


def test_query_is_bounded_and_normalized():
    assert normalize_query("  python   search ") == "python search"
    assert len(normalize_query("x" * 500)) == 300


def test_highlight_marks_terms():
    assert "<mark>Python</mark>" in highlight("Python makes tools", "python")
