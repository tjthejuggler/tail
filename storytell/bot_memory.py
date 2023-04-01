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
    #     with open(cwd+'/backups/character.json', 'w') as file:
    #         json.dump(self, file)

    def save_to_file(self):
        print("saving to file", str(self.index), self.summary)
        with open(cwd+'/storytell/backups/character'+str(self.index)+'.json', 'w') as file:
            json.dump(self.summary, file)

    def load_from_file(self):
        try:
            with open(cwd+'/storytell/backups/character'+str(self.index)+'.json', 'r') as file:
                data = json.load(file)
            self.summary = data
        except FileNotFoundError:
            print('Backup file not found.')

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