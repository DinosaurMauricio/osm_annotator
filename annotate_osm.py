'''
This module lets a user annotate the image with description that contains information scraped from OSM TAGS.
'''

import streamlit as st 
import os
import pickle
import json
from scrape import fetch_overpass_data
from preprocessing import keep_only_tagged, connect_elements, filter_tags_in_list, intersect_elements, filter_outside_elements, proj_lat_lon_on_image
from image_text_pair import ImageTextPair
from difflib import ndiff
from html import escape

def next(): st.session_state.counter += 1
def prev(): st.session_state.counter -= 1

def highlight_differences(text1, text2):
    diff = ndiff(text1.split(), text2.split())
    highlighted_diff = []

    for word in diff:
        if word.startswith("-"):
            highlighted_diff.append(f'<span style="background-color: #ff6666;">{escape(word[2:])}</span>')
        elif word.startswith("+"):
            highlighted_diff.append(f'<span style="background-color: #66b2ff;">{escape(word[2:])}</span>')
        elif word.startswith("?"):
            continue
        else:
            highlighted_diff.append(escape(word[2:]))

    return " ".join(highlighted_diff)


def load_data(data_folder):
    data = []

    for folder in os.listdir(data_folder):
        folder_path = os.path.join(data_folder, folder)

        for filename in os.listdir(folder_path):
            # we ignore the text files as they will have the same name
            if filename.endswith(".png"):
                image_path = os.path.join(folder_path, filename)
                annotation_path = os.path.splitext(image_path)[0] + '.txt'

                annotation_path_osm = ""

                significative = False

                # Check if the image has already been annotated with OSM data and assign path
                if os.path.exists(os.path.splitext(image_path)[0] + '_osm.txt'):
                    annotation_path_osm = os.path.splitext(image_path)[0] + '_osm.txt'
                elif os.path.exists(os.path.splitext(image_path)[0] + '_osm_s.txt'):
                    annotation_path_osm = os.path.splitext(image_path)[0] + '_osm_s.txt'
                    significative = True


                pair = ImageTextPair(image_path, annotation_path, annotation_path_osm, significative)
                data.append(pair)
            
    return data

def load_annotations(path):
    if not os.path.exists(path):
        return ""

    with open( path, "r") as f:
        general_annotation = f.read()
        general_annotation = general_annotation.strip()
        general_annotation = general_annotation.replace("\n", " ")
        general_annotation = general_annotation.replace("  ", " ")
        if general_annotation[-1]!=".":
            general_annotation += "."

    return general_annotation

images_folder = "images_to_annotate"

st.set_page_config(layout="wide")
st.title("Image annotation for captioning project - descriptions with OSM data")

col1, col2 = st.columns([1, 1])

images_annotated_general = []
images_annotated_osm = []
images_to_annotate_osm = []

data_pair = load_data(images_folder)   

# Extracting info about the images left to annotate
for folder in os.listdir(images_folder):
    files = os.listdir(f"{images_folder}/" + folder)
    images = [file for file in files if file.endswith(".png")]
    txt = [file for file in files if file.endswith(".txt")]
    images_annotated_general.extend([folder+"/"+image for image in images if image.replace(".png", ".txt") in txt])
    images_annotated_osm.extend([folder+"/"+image for image in images if image.replace(".png", "_osm.txt") in txt or image.replace(".png", "_osm_s.txt") in txt])
    images_to_annotate_osm.extend([folder+"/"+image for image in images if image.replace(".png", "_osm.txt") not in txt and image.replace(".png", "_osm_s.txt") not in txt])


if 'counter' not in st.session_state:
    empty_index = 0
    st.session_state.counter = empty_index

cols = st.columns(3)
with cols[2]: st.button("Next ➡️", on_click=next, use_container_width=True)
with cols[0]: st.button("⬅️ Previous", on_click=prev, use_container_width=True)    


st.write("Images left to annotate: ", len(images_to_annotate_osm))
st.write("Images annotated general: ", len(images_annotated_general))
st.write("Images annotated osm: ", len(images_annotated_osm))


n_pairs = len(data_pair)
st.write(f"Image {st.session_state.counter}/{n_pairs}")

# Annotate
image_to_annotate = data_pair[st.session_state.counter%n_pairs]

general_annotation = load_annotations(image_to_annotate.annotation_path)
osm_annotation = load_annotations(image_to_annotate.annotation_path_osm)


        
st.write("Annotate image: ", image_to_annotate.image_path)

significative = col1.checkbox("Significative",value= image_to_annotate.significative)
result = highlight_differences(general_annotation, osm_annotation)
st.write(result, unsafe_allow_html=True)
annotation = col1.text_area("General Annotation", value=general_annotation)
annotation_osm = col2.text_area("OSM Annotation", value=osm_annotation)


col1.image(image_to_annotate.image_path)
# Open the tags 
location = image_to_annotate.image_path.split("\\")[1]
tile_id = image_to_annotate.image_path.split("\\")[2].replace(".png", "")

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
        with open( image_to_annotate.annotation_path, "r+") as f:
            f.seek(0)
            f.write(annotation)
            f.truncate()
    # Save OSM annotation
    if significative:
        with open(image_to_annotate.image_path.replace(".png", "_osm_s.txt"), "w") as f:
            f.write(annotation_osm)
        if os.path.exists(image_to_annotate.image_path.replace(".png", "_osm.txt")):
            os.remove(image_to_annotate.image_path.replace(".png", "_osm.txt"))
        st.experimental_rerun()
    else:
        with open(image_to_annotate.image_path.replace(".png", "_osm.txt"), "w") as f:
            f.write(annotation_osm)
        if os.path.exists( image_to_annotate.image_path.replace(".png", "_osm_s.txt")):
            os.remove(image_to_annotate.image_path.replace(".png", "_osm_s.txt"))
        st.experimental_rerun()