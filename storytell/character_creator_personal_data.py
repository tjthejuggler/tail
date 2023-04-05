import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'anki_history'))
import json
import chatgpt_req
import anki_history
import os

num_characters = 1

def make_json(directory):
    directory = os.path.expanduser(directory)
    with open(directory, 'r') as f:
        my_json = json.load(f)
    return my_json

#def get_available_dates():
personal_records_dict = make_json('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/personal_records.txt')
apnea_records_dict = make_json('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/apnea_records.txt')
todo_items_dict = make_json('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/tododb.txt')
unusual_experiences_dict = make_json('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/unusual_experiences.txt')
podcast_descriptions_dict = make_json('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/podcasts_history.txt')

def extract_dates_from_nested_dict(data):
    dates = set()
    for item in data.values():
        for date in item["records"]:
            dates.add(date)
    return list(dates)

def extract_dates_from_dict(data):
    dates = set()
    for date in data.keys():
        dates.add(date.split(" ")[0])
    return list(dates)

def is_nested_dict(data):
    if isinstance(data, dict) and any(isinstance(value, dict) for value in data.values()):
        return True
    return False

def combine_dates_from_multiple_sources(*sources):
    combined_dates = set()
    for source in sources:
        if isinstance(source, list):
            for date in source:
                combined_dates.add(date)
        elif isinstance(source, dict):
            if is_nested_dict(source):
                dates = extract_dates_from_nested_dict(source)
            else:
                dates = extract_dates_from_dict(source)
            combined_dates.update(dates)
    return sorted(list(combined_dates))

def get_list_of_available_dates():
    anki_date_list = anki_history.get_all_dates_notes_were_created('...MyDiscoveries')
    full_date_list = combine_dates_from_multiple_sources(todo_items_dict, apnea_records_dict, todo_items_dict, unusual_experiences_dict, podcast_descriptions_dict, anki_date_list)
    print(full_date_list)

#personal records /home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/personal_records.txt
def get_data_from_records_dict(dict, date):
    result = []
    for name, content in dict.items():
        if date in content['records']:
            result.append({
                'name': name,
                'description': content['description'],
                'record': content['records'][date]
            })
    return result

def get_data_from_simple_dict(dict, date):
    result = []
    for key in dict.keys():
        if date in key:
            result.append(dict[key])
    return result


# clipboard_items = get_data_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/clipboard/clipboarddb.txt', target_date)
# #remove duplicates from clipboard items
# clipboard_items = list(dict.fromkeys(clipboard_items))

# print("CLIPBOARD ITEMS\n" + "\n".join(clipboard_items) + "\n")

def create_character(target_date):

    deck_name = '...MyDiscoveries'
    anki_history_data = "\n".join(anki_history.get_reviewed_cards(deck_name, target_date))
    print("\nANKI\n" + anki_history_data + "\n")

    personal_records_date_data = get_data_from_records_dict(personal_records_dict, target_date)
    print("PERSONAL RECORDS")
    for personal_record in personal_records_date_data:
        print(f"{personal_record['name']}: {personal_record['description']} - Record: {personal_record['record']}")

    apnea_records_date_data = get_data_from_records_dict(apnea_records_dict, target_date)
    print("APNEA RECORDS")
    for apnea_record in apnea_records_date_data:
        print(f"{apnea_record['name']}: {apnea_record['description']} - Record: {apnea_record['record']}")

    todo_items_date_data = get_data_from_simple_dict(todo_items_dict, target_date)
    print("TODO ITEMS\n" + "\n".join(todo_items_date_data) + "\n")

    unusual_experiences_date_data = get_data_from_simple_dict(unusual_experiences_dict, target_date)
    print("UNUSUAL EXPERIENCES\n" + "\n".join(unusual_experiences_date_data) + "\n")

    podcast_descriptions_date_data = get_data_from_simple_dict(podcast_descriptions_dict, target_date)
    print("PODCAST DESCRIPTIONS\n" + "\n".join(podcast_descriptions_date_data) + "\n")


    
    anki_prompt = "Here are some questions that they have recently researched: \n"+ anki_history_data +"\n" if anki_history_data else ""
    todo_prompt = "These are the types of things that they are proud of accomplishing recently: \n" + "\n".join(todo_items_date_data) + "\n" if todo_items_date_data else ""
    unusual_prompt = "Here are some noteworthy experiences they have had recently: \n" + "\n".join(unusual_experiences_date_data) + "\n" if unusual_experiences_date_data else ""
    podcast_prompt = "Subjects that they find very interesting: \n" + "\n".join(podcast_descriptions_date_data) + "\n" if podcast_descriptions_date_data else ""
    personal_records_prompt = "Here are some things that they are especially good at: \n"+ "\n".join(personal_records_date_data)+ "\n" if personal_records_date_data else ""

    initial_prompt = "You are developing a character for a story. It is your job to decide their age, gender, name, personality, their goals, their motivations, history, and any other information you would like. You have the following information to pull inspiration from:\n"+ anki_prompt + todo_prompt + unusual_prompt + podcast_prompt + personal_records_prompt + ". Create a JSON file with the following keys and the matching information for this character: 'name', 'age', 'gender', 'relationship status', 'family status'(any information on parents, siblings, children), 'hobbies', 'education history', 'occupation', 'physical description'(a single short sentence), 'personality'(no more than 3 ro 4 sentences), 'goals and motivations'(no more than 3 or 4 sentences)', 'shadow self'(this is the characters dark side they don't outwardly share, no more than 3 or 4 sentences), 'history'(no more than 3 or 4 sentences), 'other'(any other information you would like to include about this character)."

    response, tokens = chatgpt_req.send_request([{"role": "user", "content":initial_prompt}])

    print("response: ", response, "\ntokens: ", tokens)

def create_story_seed():
    #this takes in a storyline and creates a seed for it for a single story


    #decide if we will use new characters or already existing characters 

    for i in range(num_characters):
        #choose random date for this character
        create_character('2022-09-03')
        #create a character
        #make a directory for this character
        #we should keep track of interactions that characters have with each other for when they meet again later

#create_story_seed()
get_list_of_available_dates()

    #choose time period?
    #choose location
    #covertly inject problems into the story based on habits that have long anti-streaks, or even short streaks
    #   if the used is able to detect the associated habit and fix it then some help is provided and a new problem is introduced based on a different habit
    #create a universe


#Punishment for ignoring covert warnings for too long can be that a character dies, maybe first someone gets hurt or sick or something as a warning, maybe a harsher warning can be someone getting permenantly disfigured. The potential of someone dying has that thing built into it where money and potential will be burnt



#todo

#maybe we want to sometimes have it make a "completely opposite" character to get new ideas into the story

#maybe look up info on making believable characters

#turn this all into a function that takes in a date and returns a character

#make a seperate function that creates a complete story_seed, it needs to be told how many characetrs, and it also needs to create a universe

#i think i should either get more information about the character or limit the amount of information that i give the ai

#maybe I want to not take clipboard items from inside VSCode, or maybe just take some of them. Maybe i could just get rid of anything that has too high of a character:special character ratio?

#i should probably remove anything that is a duplicate?