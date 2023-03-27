from bot_memory import BotMemory
import chatgpt_req
import json
import tkinter as tk
from tkinter import scrolledtext

#make it not close tkinter window when it is over or if it crashes
#keep a running total of tokens used

def tell_bot(memory, request_message):
    if request_message:
        memory.append(["user",request_message])
    response, tokens = chatgpt_req.send_request(memory.read())
    memory.append(["assistant",response])
    return(memory, memory.read()[-1]['content'], tokens)

def initiate_bot_memories():
    bot_memories = []
    for i in range(2):
        indiv_sum = BotMemory(i)
        bot_memories.append(indiv_sum)

    bot_instruction = (
        "Welcome to a cinematic role-playing experience. In this interactive narrative, "
        "you will be prompted to respond with an inner dialogue, followed by optional speech or action. "
        "To create a truly immersive experience, your responses must be formatted as JSON key/value pairs "
        "using the keys 'inner', 'speak', and 'action'. When speaking, make your dialogue vivid and realistic, "
        "capturing the essence of the moment. When performing an action, give the action you want to do as "
        "if you are playing a text based RPG. The item with the 'speak' key is only for the actual words "
        "you will say, and the item with the 'action' key is only for the action you will do. Do not combine "
        "them. Each response should be encapsulated within a single JSON object."
    )

    bot_memories[0].append([
        "system",
        bot_instruction + " You are a 28-year-old man on a first blind date arranged by your best friend. "
        "The meeting takes place at a charming restaurant. You are an extemely shy person, and it is very "
        "hard for you to get out of your own head. As you and your date take your seats at the table, "
        "you can't help but feel a little nervous, but you are very attracted to Julie."
    ])

    bot_memories[1].append([
        "system",
        bot_instruction + " You are a 27-year-old woman on a first blind date set up by your coworker. "
        "The encounter is at a cozy restaurant. You are very talkative, always having something to say "
        "and constantly making jokes. You are excited to be on this date, and look forward to getting to "
        "know David better."
    ])

    return bot_memories


def is_null_or_empty(string):
    return not string or string.isspace()

def parse_response(bot, response):
    #convert response string to a json object
    print("response", response)
    response = json.loads(response)
    inner_dialog = ""
    outer_information_bot_format = ""
    outer_information_user_format = ""
    if 'inner' in response:
        inner_dialog = response['inner']
    if 'speak' in response and not is_null_or_empty(response['speak']):
        outer_information_bot_format = 'Your date says, "'+response['speak']+ '".'
        outer_information_user_format = str(bot)+' says: "'+response['speak'] + '"\n'
    if 'action' in response and not is_null_or_empty(response['action']):
        outer_information_bot_format += response['action']
        outer_information_user_format += str(bot)+" does: "+response['action'] +"\n"
    if outer_information_bot_format == "":
        outer_information_bot_format, outer_information_user_format = "A small amount of time goes by."
    return inner_dialog, outer_information_bot_format, outer_information_user_format

def setup_gui():
    root = tk.Tk()
    root.title("ChatGPT Terminal")
    inner_frame = tk.Frame(root)
    inner_frame.pack(side=tk.LEFT)
    
    outer_frame = tk.Frame(root)
    outer_frame.pack(side=tk.RIGHT)

    text_boxes = []
    for i in range(2):
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

def run_loop(root, text_boxes, outer_text_box, token_label, bot_memories):
    inner_dialog, outer_information_bot_format, outer_information_user_format = "","",""
    total_tokens = 0

    for cycle in range(5):
        for i, bot_memory in enumerate(bot_memories):
            try:
                if cycle == 0 and i == 0:
                    bot_memory, response, tokens = tell_bot(bot_memory, "Begin role-playing")
                else:
                    bot_memory, response, tokens = tell_bot(bot_memory, outer_information_bot_format)
                total_tokens += tokens
                print("total tokens", total_tokens, '$'+str(total_tokens*0.000002))
                token_label.config(text=f"Total tokens: {total_tokens} ${total_tokens*0.000002:.2f}")
                inner_dialog, outer_information_bot_format, outer_information_user_format = parse_response(i, response)

                text_boxes[i].insert(tk.END, inner_dialog + "\n")
                text_boxes[i].see(tk.END)

                position = outer_text_box.index(tk.END + "-1c")
                outer_text_box.insert(tk.END, inner_dialog + "\n")
                color_tag = "blue" if i == 0 else "red"
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
    bot_memories = initiate_bot_memories()
    root, text_boxes, outer_text_box, token_label = setup_gui()
    run_loop(root, text_boxes, outer_text_box, token_label, bot_memories)
    root.mainloop()

if __name__ == "__main__":
    main()