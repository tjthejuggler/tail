import random
from character_creator_autogen import get_list_of_available_dates, create_character

num_characters = 1

def create_story_seed(): #make a seperate function that creates a complete story_seed, it needs to be told how many characetrs, and it also needs to create a universe
    #this takes in a storyline and creates a seed for it for a single story

    #decide if we will use new characters or already existing characters 
    possible_dates = get_list_of_available_dates()

    for i in range(num_characters):
        #choose random date for this character
        random_date = random.choice(possible_dates)

        create_character(random_date)
        #create a character
        #make a directory for this character
        #we should keep track of interactions that characters have with each other for when they meet again later


create_story_seed()

    #choose time period?
    #choose location
    #covertly inject problems into the story based on habits that have long anti-streaks, or even short streaks
    #   if the used is able to detect the associated habit and fix it then some help is provided and a new problem is introduced based on a different habit
    #create a universe


#Punishment for ignoring covert warnings for too long can be that a character dies, maybe first someone gets hurt or sick or something as a warning, maybe a harsher warning can be someone getting permenantly disfigured. The potential of someone dying has that thing built into it where money and potential will be burnt
