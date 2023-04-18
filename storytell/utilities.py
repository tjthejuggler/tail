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

def replace_names_with_character_numbers(text, story_seed_file):
    print("replace_names_with_character_numbers1", text)
    story_seed_dir = os.path.expanduser('~/projects/tail/storytell/story_seeds/' + story_seed_file)
    print("story_seed_dir", story_seed_dir)
    with open(story_seed_dir, 'r') as f:
        story_seed = json.load(f)
    print('story_seed', story_seed)
    for bot in story_seed["characters"]["individuals"].keys():
        print('bot', bot)
        text = case_insensitive_replace(text, story_seed["characters"]["individuals"][bot]["name"], "Character"+bot)
    print("replace_names_with_character_numbers2", text)
    return text

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

def replace_character_nums_with_names(text, user_character_labels):
    print("replace_character_nums_with_names1", text)
    for i in range(len(user_character_labels)):
        text = case_insensitive_replace(text, "Character"+str(i), user_character_labels[i])
    print("replace_character_nums_with_names2", text)
    return text

def convert_to_third_person(character_name, gender, action):
    third_person_action, tokens = chatgpt_req.send_request([{"role": "user", "content":"Convert this first person sentence to a third person sentence about someone named '"+character_name+"'. Remove any information that would not be outwardly apparent. Their gender is "+gender+". It is very important that you use the exact name '"+character_name+"'.\n"+action+"\nRespond only with the third person sentence."}])
    print("convert_to_third")
    print("tokens", tokens)
    return(third_person_action, tokens)

def is_null_or_empty(string):
    return not string or string.isspace()

def get_color_tag(bot_num):
    colors = ['crimson', 'coral', 'dodger blue', 'pink', 'goldenrod', 'peach', 'khaki', 'olive', 'turquoise', 'orchid' ]
    if bot_num >= 0 and bot_num <= len(colors):
        color_tag = get_color_code(colors[bot_num]) #SET UP THIS WITH THE NEW FUNCTION BELOW, ALSO CHANGE GREEN IN THE MAIN FUNCTION
    else:
        color_tag = get_color_code("gray")
    return color_tag

def get_color_code(color_name):
    switcher = {
        "white": "#FFFFFF",
        "yellow": "#FFFF00",
        "orange": "#FFA500",
        "pink": "#FF69B4",
        "lime green": "#00FF00",
        "cyan": "#00FFFF",
        "green yellow": "#ADFF2F",
        "blue violet": "#8A2BE2",
        "magenta": "#FF00FF",
        "dodger blue": "#1E90FF",
        "gray": "#808080",
        "silver": "#C0C0C0",
        "maroon": "#800000",
        "olive": "#808000",
        "yellow": "#FFFF00",
        "green": "#008000",
        "teal": "#008080",
        "navy blue": "#000080",
        "blue": "#0000FF",
        "purple": "#800080",
        "peach": "#FFDAB9",
        "coral": "#FF7F50",
        "turquoise": "#40E0D0",
        "khaki": "#F0E68C",
        "goldenrod": "#DAA520",
        "indigo": "#4B0082",
        "orchid": "#DA70D6",
        "salmon": "#FA8072",
        "crimson": "#DC143C"
    }
    return switcher.get(color_name.lower(), "#FFFFFF")

def update_full_text_record(text):
    with open(cwd+'/storytell/backups/full_text.txt', 'a') as file:
        file.write('\n')
        file.write(text)

def empty_full_text_record():
    with open(cwd+'/storytell/backups/full_text.txt', 'w') as file:
        file.write('')

def create_history_file(total_tokens, story_seed_file, character_memories, universe_memory, user_character_labels):
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

    #read full_text_record
    with open(cwd+'/storytell/backups/full_text.txt', 'r') as file:
        full_text_record = file.read()

    with open(os.path.join(path, filename), 'a') as file:
        file.write("\nFull Text Record:\n")
        file.write(full_text_record)
        file.write("Total characters in full_text_record: ", len(full_text_record))
        file.write(f"Total tokens: {total_tokens} ${total_tokens*0.000002:.2f}")
        file.write("tokens per character: ", total_tokens/len(full_text_record))
    #print(f"History file created: {os.path.join(path, filename)}")








#print(case_insensitive_replace("character1 says, \"Hi John! It's great to finally meet you. My day has been good, thanks for asking. How about yours?\".Character1 smiles and reaches out to shake his hand confidently.", "character1", "Julie"))