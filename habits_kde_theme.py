#this script changes the KDE color theme based on how many habits I have done so far today

import os
import subprocess
import json
import time

with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()

def notify(text):
    print('text')    
    msg = "notify-send ' ' '"+text+"'"
    os.system(msg)

# def get_total_habit_count():
#     habitsdb_dir = obsidian_dir+ 'habitsdb.txt'
#     habitsdb_dir = os.path.expanduser(habitsdb_dir)
#     with open(habitsdb_dir, 'r') as f:
#         habitsdb = json.load(f)

#     habitsdb_final_only = {}

#     for key, value in habitsdb.items():
#         habitsdb_final_only[key] = list(value.values())[-1]

#     habitsdb_to_add_dir = obsidian_dir+ 'habitsdb_to_add.txt'
#     habitsdb_to_add_dir = os.path.expanduser(habitsdb_to_add_dir)
#     with open(habitsdb_to_add_dir, 'r') as f:
#         habitsdb_to_add = json.load(f)

#     total_habit_count = 0

#     for this_dict in [habitsdb_final_only, habitsdb_to_add]:
#         for key, value in this_dict.items():

#             if "Pushups" in key:
#                 value = round(value/30)
#             elif "Situps" in key:
#                 print(value)
#                 value = round(value/50)
#             elif "Squats" in key:
#                 value = round(value/30)
#                 print(value)
#             elif "Cold Shower" in key:
#                 if value > 0 and value < 3:
#                     value = 3
#                 value = round(value/3)            
#             total_habit_count += value
#     return total_habit_count

def get_total_habit_count():
    habitsdb_dir = obsidian_dir + 'habitsdb.txt'
    habitsdb_dir = os.path.expanduser(habitsdb_dir)
    with open(habitsdb_dir, 'r') as f:
        habitsdb = json.load(f)

    habitsdb_to_add_dir = obsidian_dir+ 'habitsdb_to_add.txt'
    habitsdb_to_add_dir = os.path.expanduser(habitsdb_to_add_dir)
    with open(habitsdb_to_add_dir, 'r') as f:
        habitsdb_to_add = json.load(f)

    total_habit_count, last_7_days_total, last_30_days_total = 0, 0, 0

    def adjust_habit_count(count, habit_name):
        if "Pushups" in habit_name:
            return round(count / 30)
        elif "Situps" in habit_name:
            return round(count / 50)
        elif "Squats" in habit_name:
            return round(count / 30)
        elif "Cold Shower" in habit_name:
            if count > 0 and count < 3:
                count = 3
            return round(count / 3)
        else:
            return count

    for key, habit_counts in habitsdb.items():
        sorted_dates = sorted(habit_counts.keys(), reverse=True)
        habit_to_add = habitsdb_to_add.get(key, 0)
        today_habit = habit_counts[sorted_dates[0]] + habit_to_add
        total_habit_count += adjust_habit_count(today_habit, key)

        for date in sorted_dates[:7]:
            last_7_days_total += adjust_habit_count(habit_counts[date], key)

        for date in sorted_dates[:30]:
            last_30_days_total += adjust_habit_count(habit_counts[date], key)

    print(total_habit_count, last_7_days_total/7, last_30_days_total/30)
    return last_7_days_total/7


def set_kde_color_theme(theme):
    theme_package = {
        "red": "Moe-Dark",
        "orange": "E5150-Orange",
        "green": "spectrum-mawsitsit",
        "blue": "Shadows-Global",
        "pink": "spectrum-strawberryquartz",
        "yellow": "Neon-Knights-Yellow",
    }

    if theme not in theme_package:
        print(f"Invalid theme name: {theme}")
        return
    try:
        prev_theme = '~/projects/tail/kde_theme.txt'
        prev_theme = os.path.expanduser(prev_theme)
        #only set the theme if it's not already the one set in kde_theme.txt
        with open(prev_theme, "r") as f:
            if f.read() == theme_package[theme]:
                print(f"KDE global theme is already set to {theme}")
            else:    
                subprocess.run(["lookandfeeltool", "-a", theme_package[theme]])
                #save the theme_package[theme] to a file
                with open(prev_theme, "w") as f:
                    f.write(theme_package[theme])
    except Exception as e:
        print(f"Failed to set KDE global theme to {theme}: {e}")

def main():
    
    time.sleep(7) #this is to avoid incorrect habit counts due to the phone adding habits to habitsdb.txt before removing them from habitsdb_to_add.txt
    total_habit_count = get_total_habit_count()

    #round total_habit_count up
    #total_habit_count = round(total_habit_count)

    print(total_habit_count)  


    if total_habit_count < 13:
        set_kde_color_theme("red")
    elif 13 < total_habit_count <= 20:
        set_kde_color_theme("orange")
    elif 20 < total_habit_count <= 30:
        set_kde_color_theme("green")
    elif 30 < total_habit_count <= 41:
        set_kde_color_theme("blue")
    elif 41 < total_habit_count <= 48:
        set_kde_color_theme("pink")
    elif 48 < total_habit_count <= 55:
        set_kde_color_theme("yellow")

    print(total_habit_count)
    notify(str(total_habit_count))

main()



