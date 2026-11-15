import pandas as pd
from datetime import date
import SongSelector


def test_collect_category_counts_with_mock_input():
    """Test collect_category_counts with mocked input_func."""
    categories = {'Praise': 0, 'Worship': 0}
    user_entry = 3
    
    # Mock input that responds: 2 for Praise, 1 for Worship
    responses = iter(['2', '1'])
    mock_input = lambda prompt='': next(responses)
    
    result = SongSelector.collect_category_counts(categories, user_entry, input_func=mock_input)
    
    assert result['Praise'] == 2
    assert result['Worship'] == 1


def test_collect_category_counts_exhausts_allowance():
    """Test that remaining categories get 0 when allowance is exhausted."""
    categories = {'Praise': 0, 'Worship': 0, 'Joy': 0}
    user_entry = 2
    
    # User requests 2 for Praise, leaving 0 for remaining
    responses = iter(['2', '0', '0'])
    mock_input = lambda prompt='': next(responses)
    
    result = SongSelector.collect_category_counts(categories, user_entry, input_func=mock_input)
    
    assert result['Praise'] == 2
    assert result['Worship'] == 0
    assert result['Joy'] == 0


def test_handle_song_replacement_accept_no_changes():
    """Test handle_song_replacement when user accepts initial selection."""
    data = [
        {'Song': 'S1', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
        {'Song': 'S2', 'Note': 'Worship', 'Last Date Performed': '2025-12-01'},
    ]
    filtered_df = pd.DataFrame(data)
    random_samples = pd.DataFrame(data[:1])
    
    # User answers 'Y' to accept
    mock_input = lambda prompt='': 'Y'
    
    result_samples, result_filtered = SongSelector.handle_song_replacement(
        filtered_df, random_samples, date(2026, 2, 8), input_func=mock_input
    )
    
    assert len(result_samples) == 1
    assert result_samples.iloc[0]['Song'] == 'S1'


def test_handle_song_replacement_leaves_exhausted_category_unselected():
    data = [
        {'Song': 'S1', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
        {'Song': 'S2', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
    ]
    filtered_df = pd.DataFrame(data)
    random_samples = filtered_df.iloc[[0]]
    responses = iter(['N', '0', 'RANDOM', 'N', '1', 'RANDOM', '2'])

    result_samples, _ = SongSelector.handle_song_replacement(
        filtered_df, random_samples, date(2026, 2, 8), input_func=lambda prompt='': next(responses)
    )

    assert result_samples.empty


def test_handle_song_replacement_option_two_preserves_other_selected_songs():
    data = [
        {'Song': 'S1', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
        {'Song': 'S2', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
        {'Song': 'S3', 'Note': 'Worship', 'Last Date Performed': '2025-12-01'},
    ]
    filtered_df = pd.DataFrame(data)
    random_samples = filtered_df.iloc[[0, 2]]
    responses = iter(['N', '0', 'RANDOM', 'N', '1', 'RANDOM', '2'])

    result_samples, _ = SongSelector.handle_song_replacement(
        filtered_df, random_samples, date(2026, 2, 8), input_func=lambda prompt='': next(responses)
    )

    assert result_samples['Song'].tolist() == ['S3']


def test_handle_song_replacement_switches_exhausted_category():
    data = [
        {'Song': 'S1', 'Note': 'Praise', 'Last Date Performed': '2025-12-01'},
        {'Song': 'S2', 'Note': 'Worship', 'Last Date Performed': '2025-12-01'},
    ]
    filtered_df = pd.DataFrame(data)
    random_samples = filtered_df.iloc[[0]]
    responses = iter(['N', '0', 'RANDOM', '1', '1', 'Y'])

    result_samples, _ = SongSelector.handle_song_replacement(
        filtered_df, random_samples, date(2026, 2, 8), input_func=lambda prompt='': next(responses)
    )

    assert result_samples['Song'].tolist() == ['S2']
