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
    return(last_7_days_total/7, last_30_days_total/30)

def set_keyboard_leds(theme):
    #msi-perkeyrgb --id 1038:113a -s 00ff00
    hex_color = {
        "red": "ff0000",
        "orange": "ff7f00",
        "green": "00ff00",
        "blue": "0000ff",
        "pink": "ff00ff",
        "yellow": "ffff00",
        "transparent": "ffffff"
    }
    with open('/home/lunkwill/projects/tail/current_monthly_hex_code.txt', 'w') as f:
        f.write(hex_color[theme])
    with open('/home/lunkwill/projects/tail/use_plover_keys.txt', 'r') as f:
        plover_keys = f.read().strip()
    if plover_keys == "true":
        #msi-perkeyrgb --id 1038:113a -c /home/lunkwill/projects/tail/plover_led_keys.txt
        subprocess.run(["msi-perkeyrgb", "--id", "1038:113a", "-c", "/home/lunkwill/projects/tail/plover_led_keys.txt"])
    else:
        subprocess.run(["msi-perkeyrgb", "--id", "1038:113a", "-s", hex_color[theme]])


def set_kde_color_theme(theme):
    theme_package = {
        "red": "Moe-Dark",
        "orange": "E5150-Orange",
        "green": "spectrum-mawsitsit",
        "blue": "Shadows-Global",
        "pink": "spectrum-strawberryquartz",
        #"pink": "Gently",
        "yellow": "Neon-Knights-Yellow",
        "transparent": "Glassy"
    }

    #set_keyboard_leds(theme)

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

def get_color_from_count(count):

    if count < 13:
        return "red"
    elif 13 < count <= 20:
        return "orange"
    elif 20 < count <= 30:
        return "green"
    elif 30 < count <= 41:
        return "blue"
    elif 41 < count <= 48:
        return "pink"
    elif 48 < count <= 55:
        return "yellow"
    elif 55 < count <= 62:
        return "transparent"
    else:
        return "transparent"




def main():
    
    time.sleep(7) #this is to avoid incorrect habit counts due to the phone adding habits to habitsdb.txt before removing them from habitsdb_to_add.txt
    total_habit_count_weekly, total_habit_count_monthly = get_total_habit_count()

    #round total_habit_count up
    #total_habit_count = round(total_habit_count)

    print(total_habit_count_weekly)  

    weekly_color = get_color_from_count(total_habit_count_weekly)
    monthly_color = get_color_from_count(total_habit_count_monthly)

    set_kde_color_theme(weekly_color)
    set_keyboard_leds(monthly_color)


    # if total_habit_count_weekly < 13:
    #     set_kde_color_theme("red")
    # elif 13 < total_habit_count_weekly <= 20:
    #     set_kde_color_theme("orange")
    # elif 20 < total_habit_count_weekly <= 30:
    #     set_kde_color_theme("green")
    # elif 30 < total_habit_count_weekly <= 41:
    #     set_kde_color_theme("blue")
    # elif 41 < total_habit_count_weekly <= 48:
    #     set_kde_color_theme("pink")
    # elif 48 < total_habit_count_weekly <= 55:
    #     set_kde_color_theme("yellow")
    # elif 55 < total_habit_count_weekly <= 62:
    #     set_kde_color_theme("transparent")

    print(total_habit_count_weekly)
    notify(str(total_habit_count_weekly))

main()



