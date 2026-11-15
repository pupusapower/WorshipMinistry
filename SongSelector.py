import datetime
import difflib
import math
import numpy as np
import pandas as pd
import re

from datetime import date, timedelta

# Use a forward-slash path to avoid invalid escape sequence warnings on Windows
file_path = './SongList.csv'

MIN_TIME_LAST_PERFORMED_IN_WEEKS = 6
MAX_SONGS = 10
MAX_UINT8 = max_uint8 = np.iinfo(np.uint8).max

def get_next_sunday(input_func=input):
    """Return the chosen Sunday date.

    - Monday through Saturday: return the upcoming Sunday.
    - Sunday: prompt the user to choose between today and the following Sunday.
    """
    today = date.today()

    if today.weekday() == 6:
        while True:
            choice = input_func("\n\rIt is Sunday. Select which Sunday to use:\n1. This Sunday (today)\n2. Following Sunday\nEnter 1 or 2: ")
            choice = str(choice).strip()

            if choice == '1':
                return today
            if choice == '2':
                return today + timedelta(days=7)

            print("Invalid input. Please enter 1 or 2.\n")

    days_until_sunday = (6 - today.weekday()) % 7
    return today + timedelta(days=days_until_sunday)


def load_songlist(path: str) -> pd.DataFrame:
    """Load songs CSV and ensure 'Last Date Performed' is datetime."""
    df = pd.read_csv(path)
    df['Last Date Performed'] = pd.to_datetime(df['Last Date Performed'])
    return df


def filter_songs_by_weeks(df: pd.DataFrame, weeks: int, reference_date: datetime.date) -> pd.DataFrame:
    """Return rows whose 'Last Date Performed' is at least `weeks` before `reference_date`.

    Semantics match the original script: include songs where
    Last Date Performed <= reference_date - weeks.
    """
    cutoff = pd.Timestamp(reference_date - timedelta(weeks=weeks))
    return df.loc[cutoff >= df['Last Date Performed']]


def parse_song_categories(filtered_df: pd.DataFrame) -> dict:
    """Parse categories from the 'Note' column and return a dict with keys for each token."""
    full_song_categories_list = filtered_df['Note'].astype(str).tolist()
    concise_song_categories_list = [word for text in full_song_categories_list for word in re.split(r'[,; ]', text)]
    concise_song_categories_list = [w for w in concise_song_categories_list if w]
    return dict.fromkeys(concise_song_categories_list)


def sample_by_category(filtered_df: pd.DataFrame, category_counts: dict, random_state=None) -> pd.DataFrame:
    """Sample `n` rows per category key from `filtered_df`.

    `category_counts` is a mapping of category -> n. Returns concatenated DataFrame.
    """
    random_samples = pd.DataFrame()
    for key, n in category_counts.items():
        if not n or n <= 0:
            continue
        subset = filtered_df[filtered_df['Note'].str.contains(key, case=False)]
        if n > len(subset):
            raise ValueError(f"Requested {n} samples for category '{key}' but only {len(subset)} available")
        sampled = subset.sample(n=n, random_state=random_state)
        random_samples = pd.concat([random_samples, sampled])
    return random_samples


def collect_category_counts(song_categories_dict: dict, user_entry: int, input_func=None) -> dict:
    """Prompt user for per-category song counts. Returns filled dict with counts."""
    if input_func is None:
        input_func = input

    number_key_entry = MAX_UINT8
    allowed_number_key_entry = user_entry

    for key in song_categories_dict:
        while (number_key_entry > allowed_number_key_entry) and (allowed_number_key_entry > 0):
            number_key_entry = input_func(f"\n\rHow many songs would you like of category: {key}? \n\rMust be equal to or less than {allowed_number_key_entry}: ")
            number_key_entry = int(number_key_entry)

            if number_key_entry > allowed_number_key_entry:
                print("Invalid input. Please try again.\n")

        chosen = number_key_entry if allowed_number_key_entry > 0 else 0
        chosen = min(chosen, max(0, allowed_number_key_entry))
        song_categories_dict[key] = chosen
        allowed_number_key_entry = allowed_number_key_entry - chosen
        number_key_entry = MAX_UINT8

    return song_categories_dict


def handle_song_replacement(filtered_df: pd.DataFrame, random_samples: pd.DataFrame, next_sunday_date: datetime.date, input_func=None) -> tuple:
    """Handle user interaction for removing/replacing songs. Returns (updated random_samples, updated filtered_df)."""
    if input_func is None:
        input_func = input

    allowed_entries = ['Y', 'N']
    allowed_insert_or_random_selection = ['INSERT', 'RANDOM']
    keep_selection = ""

    while keep_selection not in allowed_entries:
        keep_selection = input_func(f"Do you wish to keep this selection? Type {allowed_entries}: ")
        keep_selection = keep_selection.capitalize()
        if keep_selection not in allowed_entries:
            print("Invalid input. Please try again.\n")

    while keep_selection != 'Y':
        keep_selection = ""
        insert_or_random_selection = ""
        removal_entry = ""
        allowed_removal_entries = list(map(str, random_samples.index.tolist()))
        allowed_removal_entries.append('A')

        while not set(removal_entry) or (not set(removal_entry).issubset(set(allowed_removal_entries))):
            removal_entry = input_func(f"Enter in the indices for the songs you wish to swap out: {random_samples.index.tolist()}.\n\rOr type 'a' for all: ")
            removal_entry = removal_entry.capitalize()
            removal_entry = re.split(r'[,;\s]+', removal_entry)

            if not set(removal_entry).issubset(set(allowed_removal_entries)):
                print("Invalid input. Please try again.\n")

        if ("".join(removal_entry)) == 'A':
            removed_samples = random_samples.copy()
            filtered_df = filtered_df.drop(index=list(map(int, random_samples.index.tolist())))
        else:
            removed_samples = random_samples.loc[list(map(int, removal_entry))]
            filtered_df = filtered_df.drop(index=list(map(int, removal_entry)))

        while insert_or_random_selection not in allowed_insert_or_random_selection:
            insert_or_random_selection = input_func(f"\n\rFor the songs you desire to swap out, do you wish to insert your own songs or have them be chosen at random? Type {allowed_insert_or_random_selection}: ")
            insert_or_random_selection = insert_or_random_selection.upper()

            if insert_or_random_selection not in allowed_insert_or_random_selection:
                print("Invalid input. Please try again.\n")

        if insert_or_random_selection == 'INSERT':
            song_titles = filtered_df['Song'].tolist()

            if ("".join(removal_entry)) == 'A':
                removal_entry = list(map(int, random_samples.index.tolist()))

            random_samples = random_samples.drop(index=list(map(int, removal_entry)))

            for replacement_index in range(len(removal_entry)):
                insert_song_entry = ""
                keep_song_insertion = ""
                while keep_song_insertion != 'Y':
                    keep_song_insertion = ""
                    insert_song_entry = input_func(f"Enter the name of the song you wish to insert, for song number {replacement_index + 1}/{len(removal_entry)}: ")
                    closest_song_match = difflib.get_close_matches(insert_song_entry, song_titles, n=1, cutoff=0.4)

                    while keep_song_insertion not in allowed_entries:
                        keep_song_insertion = input_func(f"Did you mean {closest_song_match}? Type {allowed_entries}: ")
                        keep_song_insertion = keep_song_insertion.capitalize()

                        if keep_song_insertion not in allowed_entries:
                            print("Invalid input. Please try again.\n")

                    random_samples = pd.concat([random_samples, filtered_df[filtered_df['Song'].isin(closest_song_match)]])
        else:
            random_samples = random_samples.drop(index=removed_samples.index)

            def category_candidates(category):
                category_mask = filtered_df['Note'].astype(str).apply(
                    lambda note: category.lower() in [
                        item.lower() for item in re.split(r'[,; ]+', note) if item
                    ]
                )
                not_selected = ~filtered_df['Song'].isin(random_samples['Song'].tolist())
                return filtered_df[category_mask & not_selected]

            for _, removed_song in removed_samples.iterrows():
                original_categories = [
                    item for item in re.split(r'[,; ]+', str(removed_song['Note'])) if item
                ]
                category = original_categories[0] if original_categories else ''
                candidates = category_candidates(category)

                if candidates.empty:
                    print(
                        "No more songs to choose from in this category. For the remaining songs in this category, "
                        "would you like to switch it out for a different song category? Or would you like to leave "
                        "the remaining songs in this category unselected?"
                    )
                    choice = ''
                    while choice not in ('1', '2'):
                        choice = str(input_func(
                            'Select 1 - Switch the remaining songs for a different song category. '
                            'Select 2 - Leave the remaining songs as unselected. '
                        )).strip()
                        if choice not in ('1', '2'):
                            print("Invalid input. Please enter 1 or 2.\n")

                    if choice == '2':
                        continue

                    available_categories = []
                    for note in filtered_df['Note'].astype(str):
                        for available_category in re.split(r'[,; ]+', note):
                            if available_category and available_category not in available_categories:
                                if not category_candidates(available_category).empty:
                                    available_categories.append(available_category)

                    if not available_categories:
                        print("No songs are available in any other category. This song will remain unselected.\n")
                        continue

                    print("Available song categories:")
                    for category_index, available_category in enumerate(available_categories, start=1):
                        print(f"{category_index}. {available_category}")

                    category_choice = ''
                    while not category_choice.isdigit() or not 1 <= int(category_choice) <= len(available_categories):
                        category_choice = str(input_func('Select a category by number: ')).strip()
                        if not category_choice.isdigit() or not 1 <= int(category_choice) <= len(available_categories):
                            print("Invalid input. Please select an available category number.\n")

                    category = available_categories[int(category_choice) - 1]
                    candidates = category_candidates(category)

                random_samples = pd.concat([random_samples, candidates.sample(n=1)])

        print(f"Proposed Song List for {next_sunday_date}:\n {random_samples}\n")

        while keep_selection not in allowed_entries:
            keep_selection = input_func(f"Do you wish to keep this selection? Type {allowed_entries}: ")
            keep_selection = keep_selection.capitalize()
            if keep_selection not in allowed_entries:
                print("Invalid input. Please try again.\n")

    return random_samples, filtered_df


def main():
    user_entry = ""

    # Loop until valid input is received
    while int(user_entry or str(MAX_UINT8)) > MAX_SONGS:
        user_entry = input(f"Enter how many songs you would like, up to {MAX_SONGS}: \n")
    #     # Optional: Make input case-insensitive for better user experience
        user_entry = math.floor(int(user_entry))

        if user_entry > MAX_SONGS:
            print("Invalid input. Please try again.\n")

    try: 
        # Use helper to load CSV (keeps single responsibility)
        df = load_songlist(file_path)

        # full_df = df.to_string()
        full_df = df

        next_sunday_date = get_next_sunday()

        print(f"\n\rDate selected: {next_sunday_date}")

        # Use helper for filtering by weeks
        filtered_df = filter_songs_by_weeks(df, MIN_TIME_LAST_PERFORMED_IN_WEEKS, next_sunday_date)

        #print(f"Here is the filtered list: {filtered_df}\n")

        # random_samples = filtered_df.sample(n=user_entry)

        # Parse the song categories from the 'Note' column using helper
        song_categories_dict = parse_song_categories(filtered_df)

        print(f"\n\rHere are the song categories: {', '.join(song_categories_dict.keys())}")

        # Collect per-category counts from user
        song_categories_dict = collect_category_counts(song_categories_dict, user_entry)

        # Use the helper to sample per-category
        try:
            random_samples = sample_by_category(filtered_df, song_categories_dict)
        except ValueError as e:
            print(f"Sampling error: {e}")
            random_samples = pd.DataFrame()

        print(f"Proposed Song List for {next_sunday_date}:\n {random_samples}\n")

        # Handle user confirmation and song replacement
        random_samples, filtered_df = handle_song_replacement(filtered_df, random_samples, next_sunday_date)

        # define allowed responses and initialize variable before use
        allowed_entries = ['Y', 'N']
        confirm_change_date = ""

        while confirm_change_date not in allowed_entries:
            confirm_change_date = input(f"Please confirm dates for last performed will be changed for songs above to {next_sunday_date}. Type {allowed_entries}: \n")
            confirm_change_date = confirm_change_date.capitalize()

            if confirm_change_date not in allowed_entries:
                print("Invalid input. Please try again.\n")

        if confirm_change_date == 'Y':
            full_df.loc[full_df['Song'].isin(random_samples['Song'].tolist()), 'Last Date Performed'] = pd.Timestamp(next_sunday_date)

            print(f"Saving these changes to csv: {full_df}\n")
            full_df.to_csv(file_path, index=False)
        else:
            print(f"Not saving changes to csv.\n")
            pass


    except FileNotFoundError:
        print(f"File named {file_path} not found.")
    except Exception as e:
        print(f"An error has occurred: {e}")


if __name__ == '__main__':
    main()