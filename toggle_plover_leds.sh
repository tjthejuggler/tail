#!/bin/bash

filename='/home/lunkwill/projects/tail/use_plover_keys.txt'
plover_keys=$(cat "$filename" | tr -d '[:space:]')

#switch to base conda environment
source /home/lunkwill/miniconda3/etc/profile.d/conda.sh

if [ "$plover_keys" = "true" ]; then
    new_value="false"
    msi-perkeyrgb --id 1038:113a -c /home/lunkwill/projects/tail/plover_led_keys.txt
else
    new_value="true"
    #subprocess.run(["msi-perkeyrgb", "--id", "1038:113a", "-s", hex_color[theme]])
    #hex code is in file /home/lunkwill/projects/tail/current_monthly_hex_code.txt
    hex_color=$(cat "/home/lunkwill/projects/tail/current_monthly_hex_code.txt" | tr -d '[:space:]')
    msi-perkeyrgb --id 1038:113a -s $hex_color

fi

echo "$new_value" > "$filename"

# sudo chmod 666 /dev/hidraw* - run this if it doesnt work, but it should work