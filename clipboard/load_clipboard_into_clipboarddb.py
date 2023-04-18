import json
import re
from datetime import datetime

with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()

def process_clipboard(file_path, suffix):
    with open(file_path, 'r') as file:
        text_with_dates = file.read()

    date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    date_time_format = "%Y-%m-%d %H:%M:%S"

    date_indices = [(m.start(0), m.end(0)) for m in re.finditer(date_pattern, text_with_dates)]

    for i, (start_idx, end_idx) in enumerate(date_indices):
        date_time_str = text_with_dates[start_idx:end_idx]
        date_time_obj = datetime.strptime(date_time_str, date_time_format)

        if i < len(date_indices) - 1:
            next_date_start_idx = date_indices[i + 1][0]
            text_value = text_with_dates[end_idx:next_date_start_idx].strip()
        else:
            text_value = text_with_dates[end_idx:].strip()

        txt_file_dict[date_time_obj.strftime(date_time_format) + suffix] = text_value

with open(obsidian_dir+'tail/clipboard/clipboarddb.txt', 'r') as file:
    txt_file_dict = json.load(file)

file_suffixes = [
    (obsidian_dir+"tail/clipboard/comp/comp_clipboard.md", "c"),
    (obsidian_dir+"tail/clipboard/phone/phone_clipboard.md", "p")
]

for file_path, suffix in file_suffixes:
    process_clipboard(file_path, suffix)

# Sort the dictionary by date-time keys as strings
sorted_txt_file_dict = dict(sorted(txt_file_dict.items()))

# Print the sorted dictionary
for key, value in sorted_txt_file_dict.items():
    print(f"{key}: {value}")

# Write the sorted dictionary to the file
with open(obsidian_dir+'tail/clipboard/clipboarddb.txt', 'w') as file:
    json.dump(sorted_txt_file_dict, file, indent=4)
