'''
This module lets a user annotate the image with description that contains information scraped from OSM TAGS.
'''

import streamlit as st 
import os
import pickle
import json
from scrape import fetch_overpass_data
from preprocessing import keep_only_tagged, connect_elements, filter_tags_in_list, intersect_elements, filter_outside_elements, proj_lat_lon_on_image

st.set_page_config(layout="wide")
st.title("Image annotation for captioning project - descriptions with OSM data")

col1, col2 = st.columns([1, 1])

images_annotated_general = []
images_annotated_osm = []
images_to_annotate_osm = []

# Extracting info about the images left to annotate
for folder in os.listdir("images_to_annotate_automatic"):
    files = os.listdir("images_to_annotate_automatic/" + folder)
    images = [file for file in files if file.endswith(".png")]
    txt = [file for file in files if file.endswith(".txt")]
    images_annotated_general.extend([folder+"/"+image for image in images if image.replace(".png", ".txt") in txt])
    images_annotated_osm.extend([folder+"/"+image for image in images if image.replace(".png", "_osm.txt") in txt or image.replace(".png", "_osm_s.txt") in txt])
    images_to_annotate_osm.extend([folder+"/"+image for image in images if image.replace(".png", "_osm.txt") not in txt and image.replace(".png", "_osm_s.txt") not in txt])

st.write("Images left to annotate: ", len(images_to_annotate_osm))
st.write("Images annotated general: ", len(images_annotated_general))
st.write("Images annotated osm: ", len(images_annotated_osm))

# Annotate
image_to_annotate = images_to_annotate_osm[0]
with open("images_to_annotate_automatic/" + image_to_annotate.replace(".png", ".txt"), "r") as f:
    general_annotation = f.read()
    general_annotation = general_annotation.strip()
    general_annotation = general_annotation.replace("\n", " ")
    general_annotation = general_annotation.replace("  ", " ")
    if general_annotation[-1]!=".":
        general_annotation += "."
        
st.write("Annotate image: ", image_to_annotate)

significative = col1.checkbox("Significative")
annotation = col1.text_area("General Annotation", value=general_annotation)
annotation_osm = col2.text_area("OSM Annotation", value=general_annotation)

col1.image("images_to_annotate_automatic/" + image_to_annotate)
# Open the tags 
location = image_to_annotate.split("/")[0]
tile_id = image_to_annotate.split("/")[1].replace(".png", "")

with open("tiles_intersected/" + location + "_tiles_intersected.pkl", "rb") as f:
    data = pickle.load(f)
    
correspondence_tag_location = json.load(open("correspondece_tag_location.json", "r"))
tags = list(correspondence_tag_location.keys())

tile_data_row = data[data["tile_id"]==int(tile_id)]
geometry_coords = tile_data_row['geometry_coords'].values[0]
bbox = [min(geometry_coords['lat']), min(geometry_coords['lon']), max(geometry_coords['lat']), max(geometry_coords['lon'])]
osm_data = fetch_overpass_data(bbox)
elements = keep_only_tagged(osm_data["elements"])
elements = connect_elements(elements)
elements = filter_tags_in_list(tags, elements)
elements = intersect_elements(elements, bbox)
elements = filter_outside_elements(elements, bbox) # at least 3% inside the tile in every direction
elements = proj_lat_lon_on_image(elements, bbox)

for element in elements:
    col2.write(element["tags"])

if st.button("Submit"):
    # Correct the general annotation if needed
    if annotation != "" and annotation!=general_annotation:
        with open("images_to_annotate_automatic/" + image_to_annotate.replace(".png", ".txt"), "r+") as f:
            f.seek(0)
            f.write(annotation)
            f.truncate()
    # Save OSM annotation
    if significative:
        with open("images_to_annotate_automatic/" + image_to_annotate.replace(".png", "_osm_s.txt"), "w") as f:
            f.write(annotation_osm)
            st.experimental_rerun()
    else:
        with open("images_to_annotate_automatic/" + image_to_annotate.replace(".png", "_osm.txt"), "w") as f:
            f.write(annotation_osm)
            st.experimental_rerun()