from bot_memory import *
import json
from utilities import *

# def handle_tokens(tokens, total_tokens, token_label):
#     if tokens > 0:
#         total_tokens += tokens
#         token_label.config(text=f"Total tokens: {total_tokens} ${total_tokens*0.000002:.2f}")
#         print("total tokens", total_tokens, '$'+str(total_tokens*0.000002))
#     return total_tokens, token_label

def handle_tokens(tokens, total_tokens, token_label_var):
    if tokens > 0:
        total_tokens += tokens
        token_label_var.set(f"Total tokens: {total_tokens} ${total_tokens * 0.000002:.2f}")
        print("total tokens", total_tokens, '$'+str(total_tokens * 0.000002))
    return total_tokens

def initialize_story(story_seed_file):
    story_seed_dir = os.path.expanduser('~/projects/tail/storytell/story_seeds/' + story_seed_file)
    with open(story_seed_dir, 'r') as f:
        story_seed = json.load(f)
    character_memories, user_character_labels = initialize_character_memories(story_seed["reader_known_names"], story_seed["characters"])
    universe_memory = None
    print('story_seed["universe"].lower()', story_seed["universe"].lower())
    if story_seed["universe"].lower() != "none":
        print("universe", story_seed["universe"].lower())
        universe_memory = initialize_universe_memory(story_seed)
    print("initialize_story char_mem", character_memories)
    print("initialize_story uni_mem", universe_memory)
    return character_memories, universe_memory, user_character_labels

def check_for_universe_response(third_person_action, universe_memory, total_tokens, story_seed_file):
    universe_response, universe_tokens = None, 0
    universe_assistants_response, assistant_tokens = chatgpt_req.ask_universe_assistant(third_person_action)
    if "yes" in universe_assistants_response.lower():
        print("universe_assistants_response", universe_assistants_response)
        universe_memory, universe_response, universe_tokens = chatgpt_req.tell_universe(universe_memory, third_person_action, story_seed_file)
    total_tokens = total_tokens + assistant_tokens + universe_tokens        
    return universe_memory, universe_response, total_tokens

def parse_character_response(bot, response, user_character_labels, gender, universe_memory, bot_memory, story_seed_file):
    if not isinstance(response, dict):
        response = json.loads(response)
    print("parse_character_response response", response)
    print("parse_character_response1")
    inner_dialog = ""
    outer_information_bot_format = ""
    outer_information_user_format = ""
    total_tokens = 0
    universe_response = None
    if 'inner' in response:
        print("parse_character_response2")
        inner_dialog = response['inner']
    if 'speak' in response and not is_null_or_empty(response['speak']):
        print("parse_character_response3")
        speak_response = response['speak'].replace('"','')
        outer_information_bot_format = 'character'+str(bot)+' says, "'+speak_response+ '".\n'
        print("parse_character_response4")
        outer_information_user_format = user_character_labels[bot]+' says: "'+speak_response + '"\n'
    if 'action' in response and not is_null_or_empty(response['action']):
        print("parse_character_response5")
        third_person_action, total_tokens = convert_to_third_person("character"+str(bot), gender, response['action'])
        #we may want to tell the character if they go beyond their rights so far as consequences of their actions goes
        print("universe memory_before", universe_memory)
        if universe_memory:
            print("universe memory", universe_memory.read())
            universe_memory, universe_response, total_tokens = check_for_universe_response(third_person_action, universe_memory, total_tokens, story_seed_file)
        print("third person action", third_person_action)
        if universe_response:
            print("if universe response", universe_response)
            outer_information_bot_format += third_person_action + universe_response
            universe_response = replace_character_nums_with_names(universe_response,user_character_labels) + "\n"
        else:
            outer_information_bot_format += third_person_action 
        print("parse_character_response6")
        outer_information_user_format += replace_character_nums_with_names(third_person_action, user_character_labels) + "\n"       
    if 'label' in response:
        print(response["label"])
    if outer_information_bot_format == "":
        print("parse_character_response7")
        outer_information_bot_format = outer_information_user_format = "A small amount of time goes by.\n"
        bot_memory.append_to_last_user("A small amount of time goes by.")
    return inner_dialog, outer_information_bot_format, outer_information_user_format, total_tokens, universe_response, universe_memory, bot_memory