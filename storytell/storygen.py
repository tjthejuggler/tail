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

def start_story(root, outer_text_box, token_label_var):    
    character_memories, universe_memory, user_character_labels = initialize_story(story_seed_file)
    print('start_story universe_memory', universe_memory)
    run_loop(root, outer_text_box, token_label_var, character_memories, universe_memory, user_character_labels)

def setup_gui():
    root = tk.Tk()
    root.title("ChatGPT Terminal")
    inner_frame = tk.Frame(root)
    inner_frame.pack(side=tk.LEFT)
    outer_frame = tk.Frame(root)
    outer_frame.pack(side=tk.RIGHT)
    
    label = tk.Label(outer_frame, text="Select a story seed:")
    label.grid(row=0, column=1, padx=5, pady=5)
    
    combo_var = tk.StringVar()
    combo_var.set(story_seed_file)
    combo = ttk.Combobox(outer_frame, textvariable=combo_var)
    combo["values"] = get_story_seed_files()
    combo.bind("<<ComboboxSelected>>", on_dropdown_selected)
    combo.grid(row=1, column=1, padx=5, pady=5)
    
    start_button = tk.Button(outer_frame, text="Start", command=lambda: start_story(root, outer_text_box, token_label_var))
    start_button.grid(row=2, column=1, padx=5, pady=5)

    outer_text_box = scrolledtext.ScrolledText(outer_frame, wrap=tk.WORD, width=80, height=50, font=("Monospace", 14))
    outer_text_box.configure(bg="black")
    outer_text_box.grid(row=3, column=1, padx=5, pady=5)

    token_label_var = tk.StringVar()
    token_label_var.set("Total tokens: 0")
    token_label = tk.Label(outer_frame, textvariable=token_label_var)
    token_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NE)

    return root

def quit(root):
    root.quit()
    root.destroy()

def insert_text_with_color(text_box, text, color_tag, color=None):
    if color is None:
        color = color_tag
    position = text_box.index(tk.END + "-1c")
    text_box.insert(tk.END, text)
    text_box.tag_add(color_tag, position, text_box.index(tk.END + "-1c"))
    text_box.tag_config(color_tag, foreground=color)
    text_box.see(tk.END)

def insert_color_text(outer_text_box, inner_dialog, bot_num, outer_information_user_format, universe_response):
    insert_text_with_color(outer_text_box, inner_dialog + "\n", get_color_tag(bot_num))
    insert_text_with_color(outer_text_box, outer_information_user_format, "white")
    if universe_response is not None:
        lime_green = get_color_code("lime green")
        insert_text_with_color(outer_text_box, universe_response, lime_green)

def run_loop(root, outer_text_box, token_label_var, character_memories, universe_memory, user_character_labels):
    print("run_loop", character_memories, universe_memory)
    inner_dialog, outer_information_bot_format, outer_information_user_format = "","",""
    total_tokens = 0
    for cycle in range(3):
        for bot_num, bot_memory in enumerate(character_memories):
            try:                
                if cycle == 0 and bot_num == 0:
                    bot_memory, response, new_tokens = chatgpt_req.tell_character(bot_memory, "Begin role-playing")
                else:
                    bot_memory, response, new_tokens = chatgpt_req.tell_character(bot_memory, None)
                print("debug1")             
                inner_dialog, outer_information_bot_format, outer_information_user_format, parse_tokens, universe_response, universe_memory, bot_memory = parse_character_response(bot_num, response, user_character_labels, bot_memory.gender, universe_memory, bot_memory, story_seed_file)
                for other_bot_num, other_bot_memory in enumerate(character_memories):
                    if other_bot_num != bot_num:
                        print("other_bot_num", other_bot_num, other_bot_memory)
                        outer_information_bot_format_for_this_other_bot = replace_bot_known_labels(outer_information_bot_format, other_bot_memory)
                        other_bot_memory.append_to_last_user(outer_information_bot_format_for_this_other_bot)
                total_tokens = handle_tokens(new_tokens + parse_tokens, total_tokens, token_label_var)
                update_full_text_record(outer_information_user_format + (universe_response if universe_response is not None else ''))
                insert_color_text(outer_text_box, inner_dialog, bot_num, outer_information_user_format, universe_response)
                root.update_idletasks()
                root.update()
            except Exception as e:
                print("Error:", e)
                break
    create_history_file(total_tokens, story_seed_file, character_memories, universe_memory, user_character_labels)

def main():
    empty_full_text_record()
    root = setup_gui()
    root.mainloop()

if __name__ == "__main__":
    main()
