import csv
from datetime import date
import pandas as pd
import SongSelector


def write_csv(path, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Song', 'Note', 'Last Date Performed'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def test_load_and_filter(tmp_path):
    csv_path = tmp_path / "songs.csv"
    rows = [
        {'Song': 'A', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
        {'Song': 'B', 'Note': 'Worship', 'Last Date Performed': '2026-02-01'},
        {'Song': 'C', 'Note': 'Praise;Worship', 'Last Date Performed': '2025-12-31'},
    ]
    write_csv(csv_path, rows)

    df = SongSelector.load_songlist(str(csv_path))
    assert 'Last Date Performed' in df.columns

    # reference date 2026-02-15, 6 weeks before is 2026-01-04 -> rows with dates <= 2026-01-04
    filtered = SongSelector.filter_songs_by_weeks(df, weeks=6, reference_date=date(2026, 2, 15))
    # rows A (2025-12-01) and C (2025-12-31) should be included
    assert set(filtered['Song'].tolist()) == {'A', 'C'}


def test_parse_song_categories():
    data = {'Song': ['A','B'], 'Note': ['Praise,Joy','Worship;Praise'], 'Last Date Performed': ['2025-12-01','2025-12-02']}
    df = pd.DataFrame(data)
    categories = SongSelector.parse_song_categories(df)
    # tokens should include Praise, Joy, Worship
    assert 'Praise' in categories
    assert 'Joy' in categories
    assert 'Worship' in categories


def test_sample_by_category(tmp_path):
    # Make deterministic and small dataset
    data = [
        {'Song': 'S1', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
        {'Song': 'S2', 'Note': 'Worship', 'Last Date Performed': '2025-12-01'},
        {'Song': 'S3', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
    ]
    df = pd.DataFrame(data)

    # request 1 Praise and 1 Worship
    counts = {'Praise': 1, 'Worship': 1}
    sampled = SongSelector.sample_by_category(df, counts, random_state=0)
    assert len(sampled) == 2
    notes = sampled['Note'].tolist()
    assert any('Praise' in n for n in notes)
    assert any('Worship' in n for n in notes)
