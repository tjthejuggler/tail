import requests
import json
import datetime
import time

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

def get_reviewed_cards(deck_name, target_date):
    note_ids = invoke('findNotes', query=f'deck:{deck_name}')
    start_time, end_time = unix_time_range(target_date)
    reviewed_notes = []
    note_ids = [num for num in note_ids if start_time <= num // 1000 <= end_time]
    for note_id in note_ids:
        note_timestamp = note_id // 1000
        if note_timestamp >= start_time and note_timestamp <= end_time:
            note_info = invoke("notesInfo", notes=[note_id])
            front = note_info[0]["fields"]["Front"]["value"]
            back = note_info[0]["fields"]["Back"]["value"]
            reviewed_notes.append((front, back))    
    return reviewed_notes

def unix_time_range(date):
    start_of_day = int(time.mktime(time.strptime(date, '%Y-%m-%d')))
    end_of_day = start_of_day + 86399 # 86399 seconds = 23 hours, 59 minutes, and 59 seconds
    return start_of_day, end_of_day

if __name__ == '__main__':
    deck_name = '...MyDiscoveries'
    target_date = '2023-03-29'
    print(target_date)
    reviewed_cards = get_reviewed_cards(deck_name, target_date)
    print(reviewed_cards)

