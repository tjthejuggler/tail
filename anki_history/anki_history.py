import requests
import json
import time
import re

def invoke(action, **params):
    request_data = {'action': action, 'params': params, 'version': 6}
    response = requests.post('http://localhost:8765', data=json.dumps(request_data)).json()

    if "result" in response:
        return response["result"]
    else:
        raise Exception("An error occurred: {}".format(response["error"]))

def get_all_deck_names():
    deck_names = invoke('deckNames')#['result']
    return deck_names

def get_note_id_from_card_id(card_id):
    card_info = invoke("cardsInfo", {"cards": [card_id]})
    if card_info and len(card_info) == 1:
        note_id = card_info[0]["note"]
        return note_id
    else:
        print("Card not found.")
        return None

def remove_images_and_hyperlinks(text):
    img_pattern = r'<img src="img\d+\.jpg">'
    hyperlink_pattern = r'<a href="https?://[^"]+">[^<]+</a>'
    text = re.sub(img_pattern, '', text)
    text = re.sub(hyperlink_pattern, '', text)
    return text

def get_reviewed_cards(deck_name, target_date):
    note_ids = invoke('findNotes', query=f'deck:{deck_name}')
    start_time, end_time = unix_time_range(target_date)
    reviewed_notes = []
    note_ids = [num for num in note_ids if start_time <= num // 1000 <= end_time]
    #print(note_ids)
    for note_id in note_ids:
        note_timestamp = note_id // 1000
        if note_timestamp >= start_time and note_timestamp <= end_time:
            note_info = invoke("notesInfo", notes=[note_id])
            #print(note_info[0]["fields"])
            note_text = None
            if "Front" in note_info[0]["fields"]:
                note_text = remove_images_and_hyperlinks(note_info[0]["fields"]["Front"]["value"] + " " + note_info[0]["fields"]["Back"]["value"])
            elif "Text" in note_info[0]["fields"]:
                note_text = note_info[0]["fields"]["Text"]["value"].replace("{{c1::", "").replace("}}", "")
            if note_text:
                reviewed_notes.append(note_text.replace('<br>',''))    
    return reviewed_notes

def unix_time_range(date):
    start_of_day = int(time.mktime(time.strptime(date, '%Y-%m-%d')))
    end_of_day = start_of_day + 86399 # 86399 seconds = 23 hours, 59 minutes, and 59 seconds
    return start_of_day, end_of_day



