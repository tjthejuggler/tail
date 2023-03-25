#this script changes the KDE color theme based on how many habits I have done so far today

import os
import subprocess

total_habit_count_location = '~/Documents/obsidian_note_vault/noteVault/habitCounters/totalHabitCount.txt'
total_habit_count_location = os.path.expanduser(total_habit_count_location)

# with open(json_location, "r") as f:
#     json_obj = json.load(f)

#open this normal text file
with open(total_habit_count_location, "r") as f:
    total_habit_count = int(f.read())

def set_kde_color_theme(theme):
    theme_package = {
        "red": "spectrum-garnet",
        "orange": "E5150-Orange",
        "green": "spectrum-mawsitsit",
        "blue": "Shadows-Global",
        "light_blue": "Glassy"
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

if total_habit_count < 14:
    set_kde_color_theme("red")
elif 14 <= total_habit_count < 21:
    set_kde_color_theme("orange")
elif 21 <= total_habit_count < 31:
    set_kde_color_theme("green")
elif 31 <= total_habit_count < 42:
    set_kde_color_theme("blue")
elif 42 <= total_habit_count:
    set_kde_color_theme("light_blue")

print(total_habit_count)







