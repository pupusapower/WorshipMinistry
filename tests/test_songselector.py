import types
from datetime import date as real_date
import importlib

import SongSelector


def test_importable():
    importlib.reload(SongSelector)
    assert hasattr(SongSelector, 'get_next_sunday')


def test_get_next_sunday_monday(monkeypatch):
    # Monday 2026-02-02 -> next Sunday 2026-02-08
    fake_date = types.SimpleNamespace(today=lambda: real_date(2026, 2, 2))
    monkeypatch.setattr(SongSelector, 'date', fake_date)
    assert SongSelector.get_next_sunday() == real_date(2026, 2, 8)


def test_get_next_sunday_sunday(monkeypatch):
    # Sunday 2026-02-08 -> prompt user to choose 1 for today or 2 for next Sunday
    fake_date = types.SimpleNamespace(today=lambda: real_date(2026, 2, 8))
    monkeypatch.setattr(SongSelector, 'date', fake_date)
    assert SongSelector.get_next_sunday(input_func=lambda prompt: '2') == real_date(2026, 2, 15)
