import sys
from pathlib import Path
import json
import chatgpt_req

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'anki_history'))

import anki_history

target_date = '2023-03-03'

#personal records /home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/personal_records.txt
def get_data_from_records_dict(file, date):
    with open(file, 'r') as f:
        data = json.load(f)
    result = []
    for name, content in data.items():
        if date in content['records']:
            result.append({
                'name': name,
                'description': content['description'],
                'record': content['records'][date]
            })
    return result

#completed todos /home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/tododb.txt 
def get_data_from_simple_dict(file, date):
    result = []
    with open(file, 'r') as f:
        data = json.load(f)
    for key in data.keys():
        if date in key:
            result.append(data[key])
    return result

#anki cards made
deck_name = '...MyDiscoveries'
print("\nANKI\n" + "\n".join(anki_history.get_reviewed_cards(deck_name, target_date)) + "\n")

personal_records = get_data_from_records_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/personal_records.txt', target_date)
print("PERSONAL RECORDS")
for personal_record in personal_records:
    print(f"{personal_record['name']}: {personal_record['description']} - Record: {personal_record['record']}")

apnea_records = get_data_from_records_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/apnea_records.txt', target_date)
print("APNEA RECORDS")
for apnea_record in apnea_records:
    print(f"{apnea_record['name']}: {apnea_record['description']} - Record: {apnea_record['record']}")

todo_items = get_data_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/tododb.txt', target_date)
print("TODO ITEMS\n" + "\n".join(todo_items) + "\n")

unusual_experiences = get_data_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/unusual_experiences.txt', target_date)
print("UNUSUAL EXPERIENCES\n" + "\n".join(unusual_experiences) + "\n")

podcast_descriptions = get_data_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/podcasts_history.txt', target_date)
print("PODCAST DESCRIPTIONS\n" + "\n".join(podcast_descriptions) + "\n")

# clipboard_items = get_data_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/clipboard/clipboarddb.txt', target_date)
# #remove duplicates from clipboard items
# clipboard_items = list(dict.fromkeys(clipboard_items))

# print("CLIPBOARD ITEMS\n" + "\n".join(clipboard_items) + "\n")

def create_character(personal_records, apnea_records, todo_items, unusual_experiences, podcast_descriptions):

    anki_history_data = "\n".join(anki_history.get_reviewed_cards(deck_name, target_date))
    anki_prompt = "Here are some questions that they have recently researched: \n"+ anki_history_data +"\n" if anki_history_data else ""
    todo_prompt = "These are the types of things that they are proud of accomplishing recently: \n" + "\n".join(todo_items) + "\n" if todo_items else ""
    unusual_prompt = "Here are some noteworthy experiences they have had recently: \n" + "\n".join(unusual_experiences) + "\n" if unusual_experiences else ""
    podcast_prompt = "Subjects that they find very interesting: \n" + "\n".join(podcast_descriptions) + "\n" if podcast_descriptions else ""
    personal_records_prompt = "Here are some things that they are especially good at: \n"+ "\n".join(personal_records)+ "\n" if personal_records else ""

    initial_prompt = "You are developing a character for a story. It is your job to decide their age, gender, name, personality, their goals, their motivations, history, and any other information you would like. You have the following information to pull inspiration from: "+ anki_prompt + todo_prompt + unusual_prompt + podcast_prompt + personal_records_prompt + ". Create a JSON file with the following keys and the matching information for this character: 'name', 'age', 'gender', 'physical description'(a single short sentence), 'personality'(no more than 3 ro 4 sentences), 'goals and motivations'(no more than 3 or 4 sentences)', 'shadow self'(this is the characters dark side they don't outwardly share, no more than 3 or 4 sentences), 'history'(no more than 3 or 4 sentences), 'other'(any other information you would like to include about this character)."

    response, tokens = chatgpt_req.send_request([{"role": "user", "content":initial_prompt}])

    print("response: ", response, "\ntokens: ", tokens)




    #adjust this prompt so it only shows things if we have stuff from that day
    #after this message is given, ask the ai to give the specific things we need about the character
    #also ask it to give a motivation or goal that it is working on, and maybe a storyline to get it started on an adventure
    #we need to figure out a way to work in some clipboard items, but not all of them(there are so many)
create_character(personal_records, apnea_records, todo_items, unusual_experiences, podcast_descriptions)



#habits /home/lunkwill/Documents/obsidian_note_vault/noteVault/habitsdb.txt
#location


#todo

#maybe we want to sometimes have it make a "completely opposite" character to get new ideas into the story

#maybe look up info on making believable characters

#add things like education, employment, family status

#turn this all into a function that takes in a date and returns a character

#make a seperate function that creates a complete story_seed, it needs to be told how many characetrs, and it also needs to create a universe

#i think i should either get more information about the character or limit the amount of information that i give the ai

#maybe I want to not take clipboard items from inside VSCode, or maybe just take some of them. Maybe i could just get rid of anything that has too high of a character:special character ratio?

#i should probably remove anything that is a duplicate?