import streamlit as st
import pandas as pd
import os
import base64
import requests
from PIL import Image
from io import BytesIO
import leafmap.foliumap as leafmap

# Set Streamlit page layout
st.set_page_config(layout="wide")
st.title("Memory Map: Geotagged Images with Thumbnails")

# Load CSV file
csv_path = "geotag_test_csv.csv"
df = pd.read_csv(csv_path)

# Directory to store thumbnails
thumbnail_dir = "thumbnails"
os.makedirs(thumbnail_dir, exist_ok=True)

# Function to create a thumbnail from an image URL
def create_thumbnail(url, output_path, size=(128, 128)):
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error creating thumbnail for {url}: {e}")
        return False

# Add a thumbnail path column
df['thumbnail_path'] = None

# Generate thumbnails (skip if already exists)
for index, row in df.iterrows():
    image_url = row['word_presslink']
    if pd.notnull(image_url):
        image_name = row['image_name']
        thumbnail_filename = f"{image_name}_thumbnail.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
        if not os.path.exists(thumbnail_path):
            if create_thumbnail(image_url, thumbnail_path):
                df.loc[index, 'thumbnail_path'] = thumbnail_path
        else:
            df.loc[index, 'thumbnail_path'] = thumbnail_path

# Create the Leafmap map centered on Bengaluru
m = leafmap.Map(center=[12.9716, 77.5946], zoom=12)

# Function to generate HTML popup with clickable image name and thumbnail
def create_popup_html(row):
    image_name = row['image_name']
    thumbnail_path = row['thumbnail_path']
    word_presslink = row['word_presslink']

    # Make image name a clickable link
    clickable_image_name = f'<a href="{word_presslink}" target="_blank">{image_name}</a>'

    if pd.notnull(thumbnail_path) and os.path.exists(thumbnail_path):
        with open(thumbnail_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return f'{clickable_image_name}<br><img src="data:image/jpeg;base64,{encoded_string}" width="100">'
    else:
        return f'{clickable_image_name}<br>No thumbnail available'

# Add markers to the map
for index, row in df.iterrows():
    if pd.notnull(row['lat']) and pd.notnull(row['lomg']):
        m.add_marker(
            location=(row['lat'], row['lomg']),
            popup=create_popup_html(row),
            tooltip=row['image_name']
        )

# Display map in Streamlit
m.to_streamlit(height=700)
