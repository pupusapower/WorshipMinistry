import datetime
import difflib
import math
import numpy as np
import pandas as pd
import re

from datetime import date, timedelta

file_path = '.\SongList.csv'

MIN_TIME_LAST_PERFORMED_IN_WEEKS = 6
MAX_SONGS = 10
MAX_UINT8 = max_uint8 = np.iinfo(np.uint8).max

def get_next_sunday():
    # Calculates the date of the next Sunday.

    # If today is Sunday, it returns today's date.
    # If you want the following Sunday (next week), add an 'if' condition
    # to check if days_until_sunday is 0, and if so, set it to 7.

    today = date.today()

    # weekday() returns 0 for Monday, 1 for Tuesday, ..., 6 for Sunday
    # We want Sunday, which is weekday 6

    target_weekday = 6
    current_weekday = today.weekday()

    days_until_sunday = target_weekday - current_weekday

    if days_until_sunday == 0:
        days_until_sunday = 7

    next_sunday = today + timedelta(days = days_until_sunday)
    return next_sunday

user_entry = ""

# Loop until valid input is received
while int(user_entry or str(MAX_UINT8)) > MAX_SONGS:
    user_entry = input(f"Enter how many songs you would like, up to {MAX_SONGS}: \n")
#     # Optional: Make input case-insensitive for better user experience
    user_entry = math.floor(int(user_entry))

    if user_entry > MAX_SONGS:
        print("Invalid input. Please try again.\n")

try: 
    df = pd.read_csv(file_path)
    df['Last Date Performed'] = pd.to_datetime(df['Last Date Performed'])

    # full_df = df.to_string()
    full_df = df
    #print(f"Here is the full list: {full_df}\n")

    next_sunday_date = get_next_sunday()

    filtered_df = df.loc[pd.Timestamp(next_sunday_date - timedelta(weeks=MIN_TIME_LAST_PERFORMED_IN_WEEKS)) >= df['Last Date Performed']] 

    #print(f"Here is the filtered list: {filtered_df}\n")

    # random_samples = filtered_df.sample(n=user_entry)

    #Parse the song categories from the 'Note' column
    full_song_categories_list = filtered_df['Note'].tolist()
    concise_song_categories_list = [word for text in full_song_categories_list for word in re.split(r'[,; ]', text)]
    song_categories_dict = dict.fromkeys(concise_song_categories_list)

    print(f"\n\rHere are the song categories: {', '.join(song_categories_dict.keys())}")

    number_key_entry = MAX_UINT8
    allowed_number_key_entry = user_entry

    random_samples = pd.DataFrame()

    for key in song_categories_dict:
        while (number_key_entry > allowed_number_key_entry) and (allowed_number_key_entry > 0):
            number_key_entry = input(f"\n\rHow many songs would you like of category: {key}? \n\rMust be equal to or less than {allowed_number_key_entry}: ")
            # Optional: Make input case-insensitive for better user experience
            number_key_entry = int(number_key_entry)

            if number_key_entry > allowed_number_key_entry:
                print("Invalid input. Please try again.\n")
            
        song_categories_dict[key] = number_key_entry
        allowed_number_key_entry = allowed_number_key_entry - number_key_entry
        number_key_entry = MAX_UINT8

    for key in song_categories_dict:
        if (song_categories_dict[key]) > 0 and (song_categories_dict[key] < user_entry):
            random_samples = pd.concat([random_samples, filtered_df[filtered_df['Note'].str.contains(key, case=False)].sample(n=(song_categories_dict[key]))])
        else:
            pass

    print(f"Proposed Song List for {next_sunday_date}:\n {random_samples}\n")

    # Loop until valid input is received
    allowed_entries = ['Y', 'N']
    allowed_insert_or_random_selection = ['INSERT', 'RANDOM']
    keep_selection = ""

    confirm_change_date = ""

    while keep_selection not in allowed_entries:
        keep_selection = input(f"Do you wish to keep this selection? Type {allowed_entries}: ")
        # Optional: Make input case-insensitive for better user experience
        keep_selection = keep_selection.capitalize() 

        if keep_selection not in allowed_entries:
            print("Invalid input. Please try again.\n")

    while keep_selection != 'Y':
        #Clear the user entry for new prompt since we will ask user to keep or not keep after suggesting a new list
        keep_selection = ""
        insert_or_random_selection = ""
        removal_entry = ""
        allowed_removal_entries = list(map(str, random_samples.index.tolist()))
        allowed_removal_entries.append('A')

        #If entry is empty or the entry is not a part of the allowed list, keep prompting user for valid input
        while not set(removal_entry) or (not set(removal_entry).issubset(set(allowed_removal_entries))):
            removal_entry = input(f"Enter in the indices for the songs you wish to swap out: {random_samples.index.tolist()}.\n\rOr type 'a' for all: ")
            # Optional: Make input case-insensitive for better user experience
            removal_entry = removal_entry.capitalize()
            removal_entry = re.split(r'[,;\s]+', removal_entry)

            if not set(removal_entry).issubset(set(allowed_removal_entries)):
                print("Invalid input. Please try again.\n")
        
        if ("".join(removal_entry)) == 'A':
            #Remove all indices from the data frame for the songs
            filtered_df = filtered_df.drop(index=list(map(int, random_samples.index.tolist())))
        else:
            #Remove the indices from the data frame for the songs the user indicated they wish to remove
            filtered_df = filtered_df.drop(index=list(map(int, removal_entry)))

        while insert_or_random_selection not in allowed_insert_or_random_selection:
            insert_or_random_selection = input(f"\n\rFor the songs you desire to swap out, do you wish to insert your own songs or have them be chosen at random? Type {allowed_insert_or_random_selection}: ")
            # Optional: Make input case-insensitive for better user experience
            insert_or_random_selection = insert_or_random_selection.upper()

            if insert_or_random_selection not in allowed_insert_or_random_selection:
                print("Invalid input. Please try again.\n")
        
        #Insert user selected songs
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
                    insert_song_entry = input(f"Enter the name of the song you wish to insert, for song number {replacement_index + 1}/{len(removal_entry)}: ")
                    closest_song_match = difflib.get_close_matches(insert_song_entry, song_titles, n=1, cutoff=0.4)

                    while keep_song_insertion not in allowed_entries:
                        keep_song_insertion = input(f"Did you mean {closest_song_match}? Type {allowed_entries}: ")
                        # Optional: Make input case-insensitive for better user experience
                        keep_song_insertion = keep_song_insertion.capitalize() 

                        if keep_song_insertion not in keep_song_insertion:
                            print("Invalid input. Please try again.\n")
                
                random_samples = pd.concat([random_samples, filtered_df[filtered_df['Song'].isin(closest_song_match)]])

        #Randomly choose new songs, but respect user's specified number of songs per category
        else:
            if ("".join(removal_entry)) == 'A':

                removal_entry_category_series = random_samples['Note'].value_counts()
                replacement_random_samples = pd.DataFrame()
                for index, value in removal_entry_category_series.items():

                    modified_random_samples = filtered_df[(~filtered_df['Song'].isin(random_samples['Song'].tolist())) & (filtered_df['Note'].str.contains(index, case=False))].sample(n=value)
                    replacement_random_samples = pd.concat([replacement_random_samples, modified_random_samples])
                
                random_samples = replacement_random_samples

            else:
                #First, understand the quantity of the song category from the list user desires to remove. We will use this to select the correct number of songs from each category
                removal_entry_category_series = random_samples.loc[list(map(int, removal_entry)), 'Note'].value_counts()
                random_samples = random_samples.drop(index=list(map(int, removal_entry)))
                #for all the songs which are not already in your filered list, randomly select new songs and concatenate them to the previously selected songs to form a new list
                for index, value in removal_entry_category_series.items():

                    modified_random_samples = filtered_df[(~filtered_df['Song'].isin(random_samples['Song'].tolist())) & (filtered_df['Note'].str.contains(index, case=False))].sample(n=value)
                    random_samples = pd.concat([random_samples, modified_random_samples])
                
        print(f"Proposed Song List for {next_sunday_date}:\n {random_samples}\n")

        while keep_selection not in allowed_entries:
            keep_selection = input(f"Do you wish to keep this selection? Type {allowed_entries}: ")
            # Optional: Make input case-insensitive for better user experience
            keep_selection = keep_selection.capitalize()

            if keep_selection not in allowed_entries:
                print("Invalid input. Please try again.\n")
    
    while confirm_change_date not in ['Y','N']:
        confirm_change_date = input(f"Please confirm dates for last performed will be changed for songs above to {next_sunday_date}. Type {allowed_entries}: \n")
        # Optional: Make input case-insensitive for better user experience
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