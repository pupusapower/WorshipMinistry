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
    # Sunday 2026-02-08 -> next Sunday 2026-02-15 (code treats same-day as next week)
    fake_date = types.SimpleNamespace(today=lambda: real_date(2026, 2, 8))
    monkeypatch.setattr(SongSelector, 'date', fake_date)
    assert SongSelector.get_next_sunday() == real_date(2026, 2, 15)
