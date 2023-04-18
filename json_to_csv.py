

import pandas as pd
import os
import json

with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()

json_location = obsidian_dir+'habitsdb.txt'
#json_location = os.path.expanduser(json_location)

# with open(json_location, "r") as f:
#     json_obj = json.load(f)

with open("json_dict.txt", "r") as f:
    json_obj = json.load(f)

# create a DataFrame from the JSON object
df = pd.DataFrame.from_dict(json_obj, orient="index")

# sort the columns by date
df = df.reindex(sorted(df.columns), axis=1)

# export the DataFrame to a CSV file
df.to_csv("fruits.csv")



