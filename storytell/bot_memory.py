import os
import json
import random
cwd = os.getcwd()



# def get_random_voice():
#     voices = ["com.au", "us", "co.uk", "co.in"]
#     return voices[random.randint(0, len(voices)-1)]

class BotMemory:
    def __init__(self, index, summary=None):
        self.debugging = True
        self.index = index
        self.gender = ""
        self.other_character_labels = {}
        #self.voice = get_random_voice()
        if summary is None:
            self.summary = []
        else:
            self.summary = summary

    # def set_other_character_labels(self, new_label, character_number):
    #     self.other_character_labels[character_number] = new_label

    # def get_other_character_labels(self, character_number):
    #     return self.other_character_labels[character_number]
   
    def read(self):        
        if self.debugging:
            print("append", self.summary)
        return self.summary

    def append(self, new_entry):
        self.summary.append({"role": new_entry[0], "content": new_entry[1]})
        #save a backup of self to a file
        self.save_to_file()
        if self.debugging:
            print("append", self.summary)        

    def append_to_last_user(self, new_entry):
        print('index', self.index)
        print('summary', self.summary)
        if self.summary[-1]["role"] == "user":
            self.summary[-1]["content"] += "\n"+new_entry
        else:
            self.summary.append({"role": "user", "content": new_entry})
        self.save_to_file()
        if self.debugging:
            print("append_to_last_user", self.summary)

    # def save_to_file(self):
    #     with open(cwd+'/backups/convo.json', 'w') as file:
    #         json.dump(self, file)

    def save_to_file(self):
        print("saving to file", str(self.index), self.summary)
        with open(cwd+'/storytell/backups/convo'+str(self.index)+'.json', 'w') as file:
            json.dump(self.summary, file)

    def load_from_file(self):
        try:
            with open(cwd+'/storytell/backups/convo'+str(self.index)+'.json', 'r') as file:
                data = json.load(file)
            self.summary = data
        except FileNotFoundError:
            print('Backup file not found.')
