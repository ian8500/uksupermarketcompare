from app.services.matching import _confidence


def test_confidence_exact():
    label, note = _confidence(95, True, False)
    assert label == "exact"
    assert note is None


def test_confidence_substitute():
    label, note = _confidence(60, False, True)
    assert label == "substitute"
    assert "uncertainty" in note.lower()
