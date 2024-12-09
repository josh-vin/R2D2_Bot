import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
COMLINK_API = os.getenv('COMLINK_API')

LOC_FILE_PATH = 'Loc_ENG_US.txt.json'
VERSIONS_URL = 'https://raw.githubusercontent.com/swgoh-utils/gamedata/main/allVersions.json'
LOC_FILE_URL = 'https://raw.githubusercontent.com/swgoh-utils/gamedata/main/Loc_ENG_US.txt.json'

def get_local_version():
    if os.path.exists(LOC_FILE_PATH):
        with open(LOC_FILE_PATH, 'r', encoding='utf-8') as loc_file:
            loc_data = json.load(loc_file)
            return loc_data.get('version', '')
    return ''

def get_latest_version():
    response = requests.get(VERSIONS_URL)
    response.raise_for_status()
    versions_data = response.json()
    return versions_data.get('localeVersion', '')

def update_loc_file():
    print("Updating Loc_ENG_US.txt.json...")
    response = requests.get(LOC_FILE_URL)
    response.raise_for_status()
    # Attempt to load and validate the JSON content
    new_data = response.json()
    if 'version' in new_data and 'data' in new_data:
        with open(LOC_FILE_PATH, 'wb') as loc_file:
            loc_file.write(response.content)
        print("Loc_ENG_US.txt.json updated successfully.")
    else:
        print("Downloaded file does not have the expected structure.")

def check_and_update_loc_file():
    try:
        local_version = get_local_version()
        latest_version = get_latest_version()

        if local_version != latest_version:
            print(f"Local version ({local_version}) is outdated. Latest version is ({latest_version}).")
            update_loc_file()
    except Exception as e:
        print(f"An error occurred while checking/updating the localization file: {e}")
        print("Proceeding with the current version of Loc_ENG_US.txt.json.")

def create_gear_script(json_data, output_file="gear_script.js", template_file="gear_script_template.js"):
    # Read the JavaScript template
    with open(template_file, 'r', encoding='utf-8') as template:
        js_template = template.read()
    
    # Replace the placeholder with the JSON data
    json_string = json.dumps(json_data, indent=4)
    js_script = js_template.replace("{{GEAR_DATA_PLACEHOLDER}}", json_string)
    
    # Write the final script to the output file
    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(js_script)
    
    print(f"Generated script saved to {output_file}")

def parse_inventory_file(inventory_file_path):
    check_and_update_loc_file()

    with open(inventory_file_path, 'r', encoding='utf-8') as inv_file:
        inventory_data = json.load(inv_file)

    with open(LOC_FILE_PATH, 'r', encoding='utf-8') as loc_file:
        localization_data = json.load(loc_file)

    # Extract relevant sections
    equipment = inventory_data['inventory']['equipment']
    materials = inventory_data['inventory']['material']
    ally_code = inventory_data['allyCode']
    localization = localization_data['data']
    
    # Prepare the output
    # Prepare filenames with ally code
    output_file = f'{ally_code}_inventory_output.csv'
    json_output_file = f'{ally_code}_inventory_output.json'
    gear_import_file = f'{ally_code}_gear_script.js'
    output_lines = []
    json_data = []

    output_lines.append('"Item Name", "Quantity"')

    def fetch_player_data(ally_code):
        url = COMLINK_API + "/player" # ComLink URL
        payload = {
            "payload": {
                "allyCode": ally_code
            }
        }
        response = requests.post(url, json=payload)
        return response.json()

    def parse_definition_id(definition_id):
        unit, star = definition_id.split(':')
        star_value = {
            'ONE_STAR': 1,
            'TWO_STAR': 2,
            'THREE_STAR': 3,
            'FOUR_STAR': 4,
            'FIVE_STAR': 5,
            'SIX_STAR': 6,
            'SEVEN_STAR': 7
        }.get(star, 0)
        return unit, star_value

    player_data = fetch_player_data(str(ally_code))
    roster_units = player_data['rosterUnit']

    unit_stars = {}
    for unit in roster_units:
        unit_id, star_value = parse_definition_id(unit['definitionId'])
        unit_stars[unit_id] = star_value

    for item in equipment:
        item_id = item['id']
        quantity = item['quantity']
        loc_key = f"EQUIPMENT_{item_id}_NAME".upper()  # Ensure the lookup key is uppercase

            # Handle cases where _V2 is part of the loc_key
        if "_V2" in loc_key:
            loc_key = loc_key.replace("_V2", "") + "_V2"
        item_name = localization.get(loc_key, loc_key)
        
        # Format the output line
        output_line = f"\"{item_name}\", \"{quantity}\""
        output_lines.append(output_line)

        json_data.append({
                "item_name": item_name,
                "quantity": quantity
            })

    # Process materials
    for item in materials:
        item_id = item['id']
        quantity = item['quantity']

        if 'unitshard' in item_id.lower():
            unit_key = item_id.split('_', 1)[1]
            loc_key = f"UNIT_{unit_key}_NAME".upper()
            star_count = unit_stars.get(unit_key, 0)
            item_name = localization.get(loc_key, loc_key)
            output_line = f"\"{item_name}\", \"{star_count};{quantity}\""
            # json_data.append({
            #     "item_name": item_name,
            #     "star_count": star_count,
            #     "quantity": quantity
            # })
        else:
            loc_key = f"{item_id}_NAME"
            item_name = localization.get(loc_key, loc_key)
            output_line = f"\"{item_name}\", \"{quantity}\""
            # json_data.append({
            #     "item_name": item_name,
            #     "quantity": quantity
            # })

        # Format the output line
        output_lines.append(output_line)

    # Write the output lines to a file
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for line in output_lines:
            out_file.write(line + '\n')

    # Write the JSON data to a file
    with open(json_output_file, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

    # print(f"Output written to {output_file}")
    # print(f"Json Output written to {json_output_file}")

    create_gear_script(json_data, gear_import_file)

    return output_file, gear_import_file

# Example usage if run as a standalone script
if __name__ == "__main__":
    import sys
    inventory_file_path = sys.argv[1]
    parse_inventory_file(inventory_file_path)