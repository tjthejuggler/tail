import os
import json

def notify(text):
    print('text')    
    msg = "notify-send ' ' '"+text+"'"
    os.system(msg)

with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()

habitsdb_dir = obsidian_dir+ 'habitsdb.txt'
habitsdb_dir = os.path.expanduser(habitsdb_dir)
with open(habitsdb_dir, 'r') as f:
    habitsdb = json.load(f)

tasks_by_day = {}

for key, activity in habitsdb.items():
    for date, count in activity.items():
        adjusted_count = count
        if "Pushups" in key:
            adjusted_count = round(count / 30)
        elif "Situps" in key:
            adjusted_count = round(count / 50)
        elif "Squats" in key:
            adjusted_count = round(count / 30)
        elif "Cold Shower" in key:
            if count > 0 and count < 3:
                adjusted_count = 3
            adjusted_count = round(count / 3)

        if date in tasks_by_day:
            tasks_by_day[date] += adjusted_count
        else:
            tasks_by_day[date] = adjusted_count

most_tasks_day = max(tasks_by_day, key=tasks_by_day.get)
print("The day with the most tasks is:", most_tasks_day)
print("The number of tasks on that day is:", tasks_by_day[most_tasks_day])
