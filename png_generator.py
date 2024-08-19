from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

def download_image(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return Image.open(BytesIO(response.content))

def get_centered_x(draw, text, font, image_width):
    text_length = draw.textlength(text, font=font)
    if text_length > image_width:
        return None  # Text is too long for the image with this font
    return (image_width - text_length) / 2

def create_image_with_mods(output_path, character_name, character_url, mod_data, mod_set_types):
    # Image dimensions: taller than wide
    width, height = 700, 1000
    background_color = (0, 0, 0)
    image = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # Load fonts
    try:
        font_path = "arial.ttf"
        font_large = ImageFont.truetype(font_path, 48)  # Larger font for character name
        font_medium = ImageFont.truetype(font_path, 24)  # Medium font for mod names
        font_small = ImageFont.truetype(font_path, 16) # Small font for footer
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Add character name
    text_color = (255, 255, 255)
    # Draw the text centered at the top
    font = font_large
    centered_x = get_centered_x(draw, character_name, font, width)

    if centered_x is None:
        font = font_medium
        centered_x = get_centered_x(draw, character_name, font, width)

    if centered_x is not None:
        # Draw the text centered at the calculated x position
        text_y = 50  # Position text at a specific y-coordinate
        draw.text((centered_x, text_y), character_name, font=font, fill=text_color)
    
    # Add character picture on the left side
    character_img = download_image(character_url)
    character_img = character_img.resize((200, 200))  # Resize to fit nicely
    # Calculate image position (centered horizontally below the text)
    image_x = width / 2 - character_img.width / 2
    image_y = 100

    # Paste the character image
    image.paste(character_img, (int(image_x), int(image_y)), character_img)


    # Load mod set images and position them
    mod_set_icons = []
    for mod_set_type in mod_set_types:
        mod_set_type_formated = mod_set_type.replace(" ", "_")
        mod_set_image_path = os.path.join('mod_images', f'Mod-{mod_set_type_formated}-Transmitter-E.png')  # Updated filename
        if os.path.exists(mod_set_image_path):
            mod_set_img = Image.open(mod_set_image_path)
            mod_set_img = mod_set_img.resize((120, 120))  # Resize to 120px
            mod_set_icons.append((mod_set_img, mod_set_type))
        else:
            print(f"Mod set image not found: {mod_set_image_path}")

    # Space for mod sets
    mod_set_y_start = 350  # Adjusted to move mod sets down
    mod_set_spacing = 100  # Space between mod sets
    total_width = len(mod_set_icons) * 120 + (len(mod_set_icons) - 1) * mod_set_spacing
    start_x_row = (width - total_width) // 2  # Center row horizontally

    for i, (mod_set_img, mod_set_type) in enumerate(mod_set_icons):
        x_position = start_x_row + i * (120 + mod_set_spacing)
        image.paste(mod_set_img, (x_position, mod_set_y_start), mod_set_img)

        # Add text for the mod set type
        text_position = (x_position + (120 // 1.75), mod_set_y_start + 120 + 25)  # Below the icon
        draw.text(text_position, mod_set_type, font=font_medium, fill=text_color, anchor='mm')

    # Load static mod icons from mod_images directory
    mod_icons = {
        'circle': 'Mod-Data-Bus-E.png',
        'arrow': 'Mod-Receiver-E.png',
        'triangle': 'Mod-Holo-Array-E.png',
        'cross': 'Mod-Multiplexer-E.png'
    }

    # Positions and layout configuration
    icon_size = 120
    spacing = 200
    row_height = 150
    start_y = 550

    rows = [
        ['circle', 'arrow'],
        ['triangle', 'cross']
    ]

    for row_index, row in enumerate(rows):
        y_position = start_y + row_index * row_height
        total_width = (len(row) * (icon_size + spacing)) - spacing
        start_x_row = (width - total_width) // 3  # Center row horizontally

        for col_index, mod_type in enumerate(row):
            icon_filename = mod_icons.get(mod_type)
            if icon_filename:
                icon_path = os.path.join('mod_images', icon_filename)
                if os.path.exists(icon_path):
                    icon_img = Image.open(icon_path)
                    icon_img = icon_img.resize((icon_size, icon_size))  # Resize icons if needed
                    x_position = start_x_row + col_index * (icon_size + spacing)
                    image.paste(icon_img, (x_position, y_position), icon_img)

                    # Add text for the mod type
                    mod_text = mod_data.get(mod_type, 'Not Available')
                    text_position = (x_position + icon_size + 10, y_position + (icon_size // 3))
                    draw.text(text_position, mod_text, font=font_medium, fill=text_color)



    # Add the footer text
    gap = 30
    footer_text = "Data provided by swgoh.gg. Aggregated from All Players"
    footer_x = get_centered_x(draw, footer_text, font_small, width)
    footer_y = height - gap 

    
    # Draw footer background
    footer_background = Image.new("RGBA", (width, footer_y), "grey")
    image.paste(footer_background, (0, footer_y-font_small.size), footer_background)

    if footer_x is not None:
        draw.text((footer_x, footer_y), footer_text, font=font_small, fill="white")
    # Save the final image
    image.save(output_path)

# Example data
character_name = "Supreme Leader Kylo Ren"
character_url = "https://game-assets.swgoh.gg/textures/tex.charui_kyloren_tros.png"
mod_data = {
    "arrow": "Speed",
    "triangle": "Critical Damage",
    "circle": "Health",
    "cross": "Health"
}
mod_set_types = ["Offense", "Critical Chance"]  # Example mod set types

# Create the image
create_image_with_mods("output_image.png", character_name, character_url, mod_data, mod_set_types)
