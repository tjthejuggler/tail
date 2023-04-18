import os
import shutil
from pathlib import Path

def change_kde_color_scheme(scheme_name):
    home = str(Path.home())
    kdeglobals_path = os.path.join(home, '.config', 'kdeglobals')
    color_scheme_dir = '/usr/share/color-schemes/'
    color_scheme_path = os.path.join(color_scheme_dir, f'{scheme_name}.colors')

    if not os.path.exists(color_scheme_path):
        print(f"Color scheme '{scheme_name}' not found in {color_scheme_dir}")
        return

    with open(kdeglobals_path, 'r') as kde_globals_file:
        kde_globals_content = kde_globals_file.readlines()

    color_scheme_start = None
    color_scheme_end = None

    for index, line in enumerate(kde_globals_content):
        if '[Color]' in line:
            color_scheme_start = index
        elif color_scheme_start is not None and line.startswith('['):
            color_scheme_end = index
            break

    if color_scheme_start is None:
        print("No existing color scheme found in kdeglobals")
        return

    if color_scheme_end is None:
        color_scheme_end = len(kde_globals_content)

    with open(color_scheme_path, 'r') as color_scheme_file:
        new_scheme_content = color_scheme_file.readlines()

    new_scheme_content = [line for line in new_scheme_content if line.startswith('Color')]

    kde_globals_content[color_scheme_start:color_scheme_end] = new_scheme_content

    with open(kdeglobals_path, 'w') as kde_globals_file:
        kde_globals_file.writelines(kde_globals_content)

    print(f"Color scheme changed to '{scheme_name}'")

if __name__ == "__main__":
    # Replace "Breeze" with the desired color scheme name
    change_kde_color_scheme("BreezeDark")
