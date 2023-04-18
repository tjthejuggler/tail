import json

with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()


with open(obsidian_dir+'tail/clipboard/clipboarddb.txt', 'r') as file:
    txt_file_dict = json.load(file)

for key in list(txt_file_dict.keys()):
    if not key.endswith(('c', 'p')):
        new_key = key + 'c'
        txt_file_dict[new_key] = txt_file_dict.pop(key)

# Write the sorted dictionary to the file
with open(obsidian_dir+'tail/clipboard/clipboarddb.txt', 'w') as file:
    json.dump(txt_file_dict, file, indent=4)
