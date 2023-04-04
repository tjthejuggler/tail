import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'anki_history'))

import anki_history

target_date = '2023-03-19'

#personal records /home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/personal_records.txt
def find_records_on_date(date):
    with open('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/personal_records.txt', 'r') as f:
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
def get_date_from_simple_dict(file, date):
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

records = find_records_on_date(target_date)
print("PERSONAL RECORDS")
for record in records:
    print(f"{record['name']}: {record['description']} - Record: {record['record']}")

todo_items = get_date_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/tododb.txt', target_date)
print("TODO ITEMS\n" + "\n".join(todo_items) + "\n")

unusual_experiences = get_date_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/unusual_experiences.txt', target_date)
print("UNUSUAL EXPERIENCES\n" + "\n".join(unusual_experiences) + "\n")

podcast_descriptions = get_date_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/podcasts_history.txt', target_date)
print("PODCAST DESCRIPTIONS\n" + "\n".join(podcast_descriptions) + "\n")

clipboard_items = get_date_from_simple_dict('/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail/clipboard/clipboarddb.txt', target_date)
print("CLIPBOARD ITEMS\n" + "\n".join(clipboard_items) + "\n")


#habits /home/lunkwill/Documents/obsidian_note_vault/noteVault/habitsdb.txt
#location


#todo
#maybe I want to not take clipboard items from inside VSCode, or maybe just take some of them. Maybe i could just get rid of anything that has too high of a character:special character ratio?

#i should probably remove anything that is a duplicate?