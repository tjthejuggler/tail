import re
import random

todo_file = '/home/lunkwill/Documents/obsidian_note_vault/noteVault/Inbox.md'

#open this file
with open(todo_file, 'r') as f:
    text = f.read()


# Define a regular expression that matches empty lines
regex = r"(?:\r?\n){2,}"

# Split the text on empty lines
sections = re.split(regex, text)

for item in sections:
    if item.startswith('https:'):
        sections.remove(item)

random_section = random.choice(sections)

# Print the resulting sections
print(random_section)


 

 #BELOW HERE IS SUPPOSEDLY A WAY TO RANDOMLY CHOOSE WITH A SLOPE, THIS SLOPE SHOULD RESULT IN THese weights
# [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]



#  import random

# # Define the array of items
# items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# # Define the slope of the weight function
# slope = 0.5

# # Define the weights for each item based on the slope
# weights = [slope * (i + 1) for i in range(len(items))]

# # Choose a random item based on the weights
# chosen_item = random.choices(items, weights)[0]

# print(chosen_item)