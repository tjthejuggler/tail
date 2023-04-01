from bot_memory import *
import chatgpt_req
import json
import tkinter as tk
from utilities import *
import os
from tkinter import ttk, filedialog, scrolledtext
from story_helper import *

story_seed_file = 'dinner_date2c0.txt'

def get_story_seed_files():
    story_seed_path = os.path.expanduser('~/projects/tail/storytell/story_seeds/')
    return [f for f in os.listdir(story_seed_path) if os.path.isfile(os.path.join(story_seed_path, f))]

def on_dropdown_selected(event):
    global story_seed_file
    story_seed_file = event.widget.get()

#def start_story(root, text_boxes, outer_text_box, token_label):
def start_story(root, outer_text_box, token_label):    
    character_memories, universe_memory, user_character_labels = initialize_story(story_seed_file)
    #run_loop(root, text_boxes, outer_text_box, token_label, character_memories, universe_memory, user_character_labels)
    run_loop(root, outer_text_box, token_label, character_memories, universe_memory, user_character_labels)

def setup_gui(num_bots):
    root = tk.Tk()
    root.title("ChatGPT Terminal")
    inner_frame = tk.Frame(root)
    inner_frame.pack(side=tk.LEFT)    
    outer_frame = tk.Frame(root)
    outer_frame.pack(side=tk.RIGHT)
    label = tk.Label(outer_frame, text="Select a story seed:")
    label.pack(padx=5, pady=5)    
    combo_var = tk.StringVar()
    combo_var.set(story_seed_file)
    combo = ttk.Combobox(outer_frame, textvariable=combo_var)
    combo["values"] = get_story_seed_files()
    combo.bind("<<ComboboxSelected>>", on_dropdown_selected)
    combo.pack(padx=5, pady=5)
    #start_button = tk.Button(outer_frame, text="Start", command=lambda: start_story(root, text_boxes, outer_text_box, token_label))
    start_button = tk.Button(outer_frame, text="Start", command=lambda: start_story(root, outer_text_box, token_label))
    start_button.pack(padx=5, pady=5)
    # text_boxes = []
    # for i in range(num_bots):
    #     text_box = scrolledtext.ScrolledText(inner_frame, wrap=tk.WORD, width=40, height=20)
    #     text_box.grid(row=i, column=0, padx=5, pady=5)
    #     text_boxes.append(text_box)
    outer_text_box = scrolledtext.ScrolledText(outer_frame, wrap=tk.WORD, width=80, height=40)
    outer_text_box.pack(padx=5, pady=5)
    token_label = tk.Label(outer_frame, text="Total tokens: 0")
    token_label.pack(padx=5, pady=5)
    #return root, text_boxes, outer_text_box, token_label
    return root, outer_text_box, token_label

def quit(root):
    root.quit()
    root.destroy()

#def run_loop(root, text_boxes, outer_text_box, token_label, character_memories, universe_memory, user_character_labels):
def run_loop(root, outer_text_box, token_label, character_memories, universe_memory, user_character_labels):
    print("run_loop", character_memories, universe_memory)
    inner_dialog, outer_information_bot_format, outer_information_user_format = "","",""
    total_tokens = 0
    for cycle in range(2):
        for bot_num, bot_memory in enumerate(character_memories):
            try:
                
                if cycle == 0 and bot_num == 0:
                    bot_memory, response, new_tokens = chatgpt_req.tell_bot(bot_memory, "Begin role-playing")
                else:
                    bot_memory, response, new_tokens = chatgpt_req.tell_bot(bot_memory, None)
                print("debug1")             
                inner_dialog, outer_information_bot_format, outer_information_user_format, parse_tokens = parse_character_response(bot_num, response, user_character_labels, bot_memory.gender)
                #WE WANT TO CHECK TO SEE IF THERE IS AN ACTION, THEN WE WANT TO ASK A DUMMY AI IF THIS IS SOMETHONE THE GAME MASTER SHOULD RESPOND TO
                for other_bot_num, other_bot_memory in enumerate(character_memories):
                    if other_bot_num != bot_num:
                        print("other_bot_num", other_bot_num, other_bot_memory)
                        outer_information_bot_format_for_this_other_bot = replace_bot_known_labels(outer_information_bot_format, other_bot_memory)
                        other_bot_memory.append_to_last_user(outer_information_bot_format_for_this_other_bot)
                print("debug2")             
                total_tokens, token_label = handle_tokens(new_tokens+parse_tokens, total_tokens, token_label)
                print("debug3")             
                # text_boxes[bot_num].insert(tk.END, inner_dialog + "\n")
                # text_boxes[bot_num].see(tk.END)
                position = outer_text_box.index(tk.END + "-1c")
                outer_text_box.insert(tk.END, inner_dialog + "\n")
                color_tag = get_color_tag(bot_num)
                outer_text_box.tag_add(color_tag, position, outer_text_box.index(tk.END + "-1c"))
                outer_text_box.tag_config(color_tag, foreground=color_tag)
                outer_text_box.insert(tk.END, outer_information_user_format)
                outer_text_box.see(tk.END)
                root.update_idletasks()
                root.update()
            except Exception as e:
                print("Error:", e)
                break

    #create_narrative_story()

    create_history_file(story_seed_file, character_memories, universe_memory, user_character_labels)

def main():
    global story_seed_file
    story_seed_file = 'dinner_date2c0.txt'
    story_seed_dir = '~/projects/tail/storytell/story_seeds/'+story_seed_file
    story_seed_dir = os.path.expanduser(story_seed_dir)
    with open(story_seed_dir, 'r') as f:
        story_seed = json.load(f)
    character_memories, user_character_labels = initialize_character_memories(story_seed["reader_known_names"], story_seed["characters"])
    universe_memory = None
    if story_seed["universe"].lower() != "none":
        print("universe", story_seed["universe"].lower())
        universe_memory = initialize_universe_memory(story_seed["universe"])
    #root, text_boxes, outer_text_box, token_label = setup_gui(len(character_memories))
    root, outer_text_box, token_label = setup_gui(len(character_memories))
    root.mainloop()

if __name__ == "__main__":
    main()


