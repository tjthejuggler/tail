from bot_memory import *
import json
from utilities import *

def handle_tokens(tokens, total_tokens, token_label):
    if tokens > 0:
        total_tokens += tokens
        token_label.config(text=f"Total tokens: {total_tokens} ${total_tokens*0.000002:.2f}")
        print("total tokens", total_tokens, '$'+str(total_tokens*0.000002))
    return total_tokens, token_label

def initialize_story(story_seed_file):
    story_seed_dir = os.path.expanduser('~/projects/tail/storytell/story_seeds/' + story_seed_file)
    with open(story_seed_dir, 'r') as f:
        story_seed = json.load(f)
    character_memories, user_character_labels = initialize_character_memories(story_seed["reader_known_names"], story_seed["characters"])
    universe_memory = None
    if story_seed["universe"].lower() != "none":
        print("universe", story_seed["universe"].lower())
        universe_memory = initialize_universe_memory(story_seed["universe"])
    return character_memories, universe_memory, user_character_labels

def parse_character_response(bot, response, user_character_labels, gender):
    print("parse_character_response response", response)
    response = json.loads(response)
    print("parse_character_response1")
    inner_dialog = ""
    outer_information_bot_format = ""
    outer_information_user_format = ""
    tokens = 0
    if 'inner' in response:
        print("parse_character_response2")
        inner_dialog = response['inner']
    if 'speak' in response and not is_null_or_empty(response['speak']):
        print("parse_character_response3")
        speak_response = response['speak'].replace('"','')
        outer_information_bot_format = 'character'+str(bot)+' says, "'+speak_response+ '".'
        print("parse_character_response4")
        outer_information_user_format = user_character_labels[bot]+' says: "'+speak_response + '"\n'
    if 'action' in response and not is_null_or_empty(response['action']):
        print("parse_character_response5")
        third_person_action, tokens = convert_to_third_person("character"+str(bot), gender, response['action'])
        print("third person action", third_person_action)
        outer_information_bot_format += third_person_action
        print("parse_character_response6")
        outer_information_user_format += case_insensitive_replace(third_person_action, "character"+str(bot), user_character_labels[bot]) +"\n"
    if 'label' in response:
        print(response["label"])
    if outer_information_bot_format == "":
        print("parse_character_response7")
        outer_information_bot_format, outer_information_user_format = "A small amount of time goes by."
    return inner_dialog, outer_information_bot_format, outer_information_user_format, tokens