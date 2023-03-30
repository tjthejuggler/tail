from bot_memory import BotMemory
import chatgpt_req
import json
import tkinter as tk
from tkinter import scrolledtext
from utilities import *
import os

num_bots = 1
narrator = True
story_seed_file = 'dinner_date2c0.txt'

def tell_bot(memory, request_message):
    if request_message:
        memory.append(["user",request_message+"\nRespond with a single JSON object."])

    print("memory.read()", memory.read())
    response, tokens = chatgpt_req.send_request(memory.read())
    memory.append(["assistant",response])
    return(memory, memory.read()[-1]['content'], tokens)

def initialize_character_memories(characters_user_knows, character_seed):
    character_memories = []
    user_character_labels = []
    for bot in character_seed["individuals"].keys():
        indiv_sum = BotMemory(bot)
        character_memories.append(indiv_sum)
        self_gender = character_seed["individuals"][bot]["gender"]
        character_memories[int(bot)].append([
            "system", 
            character_seed["instruction"] + 
            "Your name is " + character_seed["individuals"][bot]["name"] + ". " +
            "Your gender is " + self_gender + ". " +
            "Your physical description is " + character_seed["individuals"][bot]["physical_description"] + ". " +
            character_seed["individuals"][bot]["mentality"]])
        character_memories[int(bot)].gender = self_gender
        for other_bot in character_seed["individuals"].keys():
            if bot != other_bot:
                if int(other_bot) in character_seed["individuals"][bot]["known_character_names"]:
                    label_to_use = character_seed["individuals"][other_bot]["name"]
                else:
                    label_to_use = character_seed["individuals"][other_bot]["physical_description"]
                character_memories[int(bot)].other_character_labels["Character"+other_bot] = label_to_use
            #character_memories[int(bot)]["other_character_labels"] = character_seed["individuals"][bot]["name"], other_bot
        if int(bot) in characters_user_knows:
            user_character_labels.append(character_seed["individuals"][bot]["name"])
        else:
            user_character_labels.append(character_seed["individuals"][bot]["physical_description"])
    return character_memories, user_character_labels

def initialize_universe_memory(universe_seed):
    print('universe seed', universe_seed)
    universe_history = BotMemory(99)
    universe_history.append(["system", universe_seed])

def is_null_or_empty(string):
    return not string or string.isspace()

def parse_response(bot, response, user_character_labels, gender):
    print("response", response)
    response = json.loads(response)
    print("parse_response1")
    inner_dialog = ""
    outer_information_bot_format = ""
    outer_information_user_format = ""
    if 'inner' in response:
        print("parse_response2")
        inner_dialog = response['inner']
    if 'speak' in response and not is_null_or_empty(response['speak']):
        print("parse_response3")
        speak_response = response['speak'].replace('"','')
        outer_information_bot_format = 'character'+str(bot)+' says, "'+speak_response+ '".'
        print("parse_response4")
        outer_information_user_format = user_character_labels[bot]+' says: "'+speak_response + '"\n'
    if 'action' in response and not is_null_or_empty(response['action']):
        print("parse_response5")
        third_person_action, tokens = convert_to_third_person("character"+str(bot), gender, response['action'])
        print("third person action", third_person_action)
        outer_information_bot_format += third_person_action
        print("parse_response6")
        outer_information_user_format += case_insensitive_replace(third_person_action, "character"+str(bot), user_character_labels[bot]) +"\n"
    if 'label' in response:
        print(response["label"])
        #this needs set up, maybe tell the bot to put (the current label, the new label)
        # we may need some AI to distinguish which one it is, or maybe even make a follow up question to the bot the clarify
    if outer_information_bot_format == "":
        print("parse_response7")
        outer_information_bot_format, outer_information_user_format = "A small amount of time goes by."
    return inner_dialog, outer_information_bot_format, outer_information_user_format, tokens

def setup_gui(num_bots):
    root = tk.Tk()
    root.title("ChatGPT Terminal")
    inner_frame = tk.Frame(root)
    inner_frame.pack(side=tk.LEFT)
    
    outer_frame = tk.Frame(root)
    outer_frame.pack(side=tk.RIGHT)

    text_boxes = []
    for i in range(num_bots):
        text_box = scrolledtext.ScrolledText(inner_frame, wrap=tk.WORD, width=40, height=20)
        text_box.grid(row=i, column=0, padx=5, pady=5)
        text_boxes.append(text_box)

    outer_text_box = scrolledtext.ScrolledText(outer_frame, wrap=tk.WORD, width=80, height=40)
    outer_text_box.pack(padx=5, pady=5)

    token_label = tk.Label(outer_frame, text="Total tokens: 0")
    token_label.pack(padx=5, pady=5)

    return root, text_boxes, outer_text_box, token_label


def quit(root):
    root.quit()
    root.destroy()

def handle_tokens(tokens, total_tokens, token_label):
    if tokens > 0:
        total_tokens += tokens
        token_label.config(text=f"Total tokens: {total_tokens} ${total_tokens*0.000002:.2f}")
        print("total tokens", total_tokens, '$'+str(total_tokens*0.000002))
    return total_tokens, token_label

def replace_bot_known_labels(outer_information_bot_format, bot_memory):
    for label in bot_memory.other_character_labels.keys():
        case_insensitive_replace(outer_information_bot_format, label, bot_memory.other_character_labels[label])
    return outer_information_bot_format

def run_loop(root, text_boxes, outer_text_box, token_label, character_memories, universe_memory, user_character_labels):
    print(character_memories, universe_memory)
    inner_dialog, outer_information_bot_format, outer_information_user_format = "","",""
    total_tokens = 0

    for cycle in range(3):
        for bot_num, bot_memory in enumerate(character_memories):
            try:
                outer_information_bot_format = replace_bot_known_labels(outer_information_bot_format, bot_memory)
                if cycle == 0 and bot_num == 0:
                    bot_memory, response, new_tokens = tell_bot(bot_memory, "Begin role-playing")
                else:
                    bot_memory, response, new_tokens = tell_bot(bot_memory, outer_information_bot_format)
                print("debug1")             
                inner_dialog, outer_information_bot_format, outer_information_user_format, parse_tokens = parse_response(bot_num, response, user_character_labels, bot_memory.gender)
                print("debug2")             
                total_tokens, token_label = handle_tokens(new_tokens+parse_tokens, total_tokens, token_label)
                print("debug3")             
                text_boxes[bot_num].insert(tk.END, inner_dialog + "\n")
                text_boxes[bot_num].see(tk.END)

                position = outer_text_box.index(tk.END + "-1c")
                outer_text_box.insert(tk.END, inner_dialog + "\n")
                color_tag = "blue" if bot_num == 0 else "red"
                outer_text_box.tag_add(color_tag, position, outer_text_box.index(tk.END + "-1c"))
                outer_text_box.tag_config(color_tag, foreground=color_tag)
                outer_text_box.insert(tk.END, outer_information_user_format)
                outer_text_box.see(tk.END)

                root.update_idletasks()
                root.update()
            except Exception as e:
                print("Error:", e)
                break

def main():
    story_seed_dir = '~/projects/tail/storytell/story_seeds/'+story_seed_file
    story_seed_dir = os.path.expanduser(story_seed_dir)
    with open(story_seed_dir, 'r') as f:
        story_seed = json.load(f)
    character_memories, user_character_labels = initialize_character_memories(story_seed["reader_known_names"], story_seed["characters"])
    universe_memory = None
    if story_seed["universe"].lower() != "none":
        print("universe", story_seed["universe"].lower())
        universe_memory = initialize_universe_memory(story_seed["universe"])
    root, text_boxes, outer_text_box, token_label = setup_gui(len(character_memories))
    run_loop(root, text_boxes, outer_text_box, token_label, character_memories, universe_memory, user_character_labels)
    root.mainloop()

if __name__ == "__main__":
    main()

