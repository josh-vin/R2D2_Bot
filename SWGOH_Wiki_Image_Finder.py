import requests
from bs4 import BeautifulSoup
import os

# Base URL for scraping
base_url = 'https://swgoh.wiki/images/thumb/'

# List of directories to check
top_directories = [str(i) for i in range(0, 10)] + [chr(i) for i in range(ord('a'), ord('g'))]
sub_directories = [chr(i) for i in range(ord('a'), ord('g'))] + [str(i) for i in range(10)]

# Directory to save images
save_dir = 'mod_images'
os.makedirs(save_dir, exist_ok=True)

# Function to get the soup object for a given URL
def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.content, 'html.parser')

# Function to validate image URL
def validate_image_url(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            return True
    except Exception as e:
        print(f"Error validating URL {url}: {e}")
    return False

# Function to download and save the image
def download_and_save_image(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        with open(os.path.join(save_dir, filename), 'wb') as f:
            f.write(response.content)
        print(f"Saved image {filename} to {save_dir}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Scraping the directories
for top_dir in top_directories:
    for sub_dir in sub_directories:
        url = f"{base_url}{top_dir}/{top_dir}{sub_dir}/"
        try:
            soup = get_soup(url)
            links = soup.find_all('a')
            for link in links:
                href = link.get('href').rstrip('/')  # Remove trailing slash if present
                if href.endswith('.png') and 'Mod-' in href:
                    img_name = href.split('/')[-1]
                    final_url = f"{base_url}{top_dir}/{top_dir}{sub_dir}/{img_name}/120px-{href}"
                    if validate_image_url(final_url):
                        download_and_save_image(final_url, img_name)
                    else:
                        print(f"URL Not Valid {img_name}: {final_url}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

print("\nFinished saving mod images.")
