import requests
from bs4 import BeautifulSoup
import re

# Base URL for scraping
base_url = 'https://swgoh.wiki/images/thumb/'

# List of directories to check
top_directories = [str(i) for i in range(0, 10)] + [chr(i) for i in range(ord('a'), ord('g'))]
sub_directories = [chr(i) for i in range(ord('a'), ord('g'))] + [str(i) for i in range(10)]

# List of items to search for
items = [
    "MK 8 Neuro-Saav Electrobinoculars Salvage",
    "Zinbiddle Card",
    "Impulse Detector",
    "Aeromagnifier",
    "Gyrda Keypad",
    "Droid Brain",
    "MK 8 Neuro-Saav Electrobinoculars Component",
    "Mk 5 A/KT Stun Gun Prototype Salvage"
]

# Dictionary to store item names and their image URLs
item_image_urls = {}

# Function to get the soup object for a given URL
def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.content, 'html.parser')

# Function to clean and match the item name with the image name
def clean_and_match(item_name, img_name):
    # Normalize the item name by replacing spaces, underscores, and hyphens with a standard separator
    normalized_item_name = re.sub(r'[\s/_-]+', '_', item_name.lower())
    normalized_img_name = re.sub(r'[\s/_-]+', '_', img_name.lower())
    
    # Extract the core name (without extension) for comparison
    img_name_core = normalized_img_name.split('.')[0]

    return "gear_" + normalized_item_name == img_name_core

# Function to validate image URL
def validate_image_url(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            return True
    except Exception as e:
        print(f"Error validating URL {url}: {e}")
    return False

# Scraping the directories
for top_dir in top_directories:
    for sub_dir in sub_directories:
        url = f"{base_url}{top_dir}/{top_dir}{sub_dir}/"
        try:
            soup = get_soup(url)
            links = soup.find_all('a')
            for link in links:
                href = link.get('href').rstrip('/')  # Remove trailing slash if present
                if href.endswith('.png'):
                    img_name = href.split('/')[-1]
                    for item in items:
                        if clean_and_match(item, img_name):
                            final_url = f"{base_url}{top_dir}/{top_dir}{sub_dir}/{href}/90px-{href}"
                            if validate_image_url(final_url):
                                item_image_urls[item] = final_url
                                print(f"Found {item}: {item_image_urls[item]}")
                            else: 
                                print(f"URL Not Valid {item}: {item_image_urls[item]}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

# Print the final dictionary of items and their image URLs
print("\nFinal item image URLs:")
for item, url in item_image_urls.items():
    print(f"{item}: {url}")
