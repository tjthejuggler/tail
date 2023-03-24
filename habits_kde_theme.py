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
        "red": "Sweet-Mars",
        "orange": "E5150-Orange",
        "green": "Manjaro-Cyan-Global",
        "blue": "Shadows-Global",
        "light_blue": "Glassy"
    }

    if theme not in theme_package:
        print(f"Invalid theme name: {theme}")
        return

    try:
        #only set the theme if it's not already the one set in kde_theme.txt
        with open("kde_theme.txt", "r") as f:
            if f.read() == theme_package[theme]:
                print(f"KDE global theme is already set to {theme}")
            else:    
                subprocess.run(["lookandfeeltool", "-a", theme_package[theme]])
                #save the theme_package[theme] to a file
                with open("kde_theme.txt", "w") as f:
                    f.write(theme_package[theme])
    except Exception as e:
        print(f"Failed to set KDE global theme to {theme}: {e}")

if total_habit_count < 10:
    set_kde_color_theme("red")
elif 10 <= total_habit_count < 20:
    set_kde_color_theme("orange")
elif 20 <= total_habit_count < 30:
    set_kde_color_theme("green")
elif 30 <= total_habit_count < 40:
    set_kde_color_theme("blue")
elif 40 <= total_habit_count:
    set_kde_color_theme("light_blue")

print(total_habit_count)







