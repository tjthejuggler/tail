import chatgpt_req
import json
from datetime import datetime
import os
cwd = os.getcwd()

def replace_bot_known_labels(outer_information_bot_format, bot_memory):
    print("other_bot_num2", bot_memory)
    print("bot_memory.other_character_labels", bot_memory.other_character_labels)
    for label in bot_memory.other_character_labels.keys():
        print("case_insensitive_replace(outer_information_bot_format, label, bot_memory.other_character_labels[label])", outer_information_bot_format, label, bot_memory.other_character_labels[label])
        outer_information_bot_format = case_insensitive_replace(outer_information_bot_format, label, bot_memory.other_character_labels[label])
    return outer_information_bot_format

def case_insensitive_replace(my_string, target, replacement):
    s_lower = my_string.lower()
    target_lower = target.lower()    
    index = 0
    result = []
    while index < len(my_string):
        pos = s_lower.find(target_lower, index)
        if pos == -1:
            break
        result.append(my_string[:pos] + replacement)
        my_string = my_string[pos + len(target):]
        s_lower = s_lower[pos + len(target):]
        index = pos + len(replacement)
    result.append(my_string)
    return ''.join(result)

def convert_to_third_person(character_name, gender, action):
    third_person_action, tokens = chatgpt_req.send_request([{"role": "user", "content":"Convert this first person sentence to a third person sentence about someone named '"+character_name+"'. Remove any information that would not be outwardly apparent. Their gender is "+gender+". It is very important that you use the exact name '"+character_name+"'.\n"+action+"\nRespond only with the third person sentence."}])
    print("convert_to_third")
    print("tokens", tokens)
    return(third_person_action, tokens)

def is_null_or_empty(string):
    return not string or string.isspace()

def get_color_tag(bot_num):
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'pink']
    if bot_num >= 0 and bot_num <= len(colors):
        color_tag = colors[bot_num]
    else:
        color_tag = 'gray'
    return color_tag

def update_full_text_record(text):
    with open(cwd+'/storytell/backups/full_text.txt', 'a') as file:
        file.write('\n')
        file.write(text)


def create_history_file(story_seed_file, character_memories, universe_memory, user_character_labels):
    # create a dictionary containing all the necessary data
    history_data = {
        **{f"{user_character_labels[i]}_memory": memory.read() for i, memory in enumerate(character_memories)},
        "universe_memory": universe_memory.read() if universe_memory else None,
        "user_character_labels": user_character_labels
    }

    # get today's date and time and use it to create a unique file name
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
    story_seed_file_name = os.path.splitext(story_seed_file)[0]
    filename = f"{story_seed_file_name}_{dt_string}.txt"
    path = "storytell/histories/"

    # create the histories folder if it doesn't exist
    os.makedirs(path, exist_ok=True)

    # write the data to a file in the histories folder
    with open(os.path.join(path, filename), "w") as f:
        json.dump(history_data, f, indent=4)

    print(f"History file created: {os.path.join(path, filename)}")







#print(case_insensitive_replace("character1 says, \"Hi John! It's great to finally meet you. My day has been good, thanks for asking. How about yours?\".Character1 smiles and reaches out to shake his hand confidently.", "character1", "Julie"))