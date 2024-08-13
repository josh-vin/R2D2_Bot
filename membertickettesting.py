import re

def parse_ticket_message(message):
    # Regular expression pattern to match the expected format
    total_members_missed = 0
    total_tickets_missed = 0
    pattern = r".*Below are the members that missed the 600 ticket mark. Discipline as you must!\n(.*)" # This hotbot message is customizable per guild settings
        
    # Search for the pattern in the message
    match = re.search(pattern, message, re.DOTALL)
    print(match)
    if match:
        # Get the list of members and their ticket counts
        member_lines = match.group(1).split('\n')
        print(member_lines)
        # Initialize counters
        
        # Iterate over each member line
        for line in member_lines:
            # Extract member name and ticket count using regular expression
            member_match = re.match(r".*\s+\([\s,*]*(\d+)[\s,*]*/600\)", line)
            print(member_match)
            if member_match:
                # Increment counters
                print(member_match.group(1))
                total_members_missed += 1
                total_tickets_missed += 600 - int(member_match.group(1))

def calculate_left_to_farm(current_shards, out_of):
    # calculate shards left to farm
    shards_needed = 330
    match out_of:
        case 10 | 15:
            shards_needed = 320
        case 25:
            shards_needed = 305
        case 30 | 50: 
            shards_needed = 280
        case 65 | 80:
            shards_needed = 250
        case 85 | 145:
            shards_needed = 185
        case 100: 
            shards_needed = 100
    left_to_farm = shards_needed - current_shards
    return left_to_farm

# def calculate_farm_duration(left_to_farm, farm_type, drop_count, node_energy_cost):
#     if farm_type == "Cantina": 
        


if __name__ == '__main__':
    # parse_ticket_message(message)
    calculate_left_to_farm(61, 100)