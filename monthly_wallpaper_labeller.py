import json
from PIL import Image, ImageDraw, ImageFont

# Load the json file
with open('./animal_names.json', 'r') as f:
    names = json.load(f)

# Set the font (you may need to adjust the path and size)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size=50)

# Loop through the numbers
for i in range(1, 57):
    # Open the image
    img = Image.open(f'/home/lunkwill/Pictures/Wallpapers/mon/result_{i}.png')
    draw = ImageDraw.Draw(img)

    # Get the corresponding name
    text = names[str(i)]

    # Calculate the width and height of the text
    text_width, text_height = draw.textsize(text, font=font)

    # Calculate the x position
    x = (img.width - text_width) / 2

    # Draw the text on the image
    draw.text((x, 500), text, fill='white', font=font)

    # Save the image
    img.save(f'/home/lunkwill/Pictures/Wallpapers/mon/result_{i}.png')