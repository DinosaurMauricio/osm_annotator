'''
This module lets a user annotate the image with a thoroguh description.
'''

from annotate_osm import images_folder
import streamlit as st 
import os

st.set_page_config(layout="wide")
st.title("Image annotation for captioning project")

images_to_annotate = []
images_annotated = []

# Extracting info about the images left to annotate
for folder in os.listdir(images_folder):
    files = os.listdir(f"{images_folder}/" + folder)
    images = [file for file in files if file.endswith(".png")]
    txt = [file for file in files if file.endswith(".txt")]
    images_annotated.extend([folder+"/"+image for image in images if image.replace(".png", ".txt") in txt])
    images_to_annotate.extend([folder+"/"+image for image in images if image.replace(".png", ".txt") not in txt])

st.write("Images left to annotate: ", len(images_to_annotate))
st.write("Images annotated: ", len(images_annotated))

# Annotate
image_to_annotate = images_to_annotate[0]
st.write("Annotate image: ", image_to_annotate)

st.image(f"{images_folder}/" + image_to_annotate)
annotation = st.text_area("Annotation", value="")

if st.button("Submit"):
    with open(f"{images_folder}/" + image_to_annotate.replace(".png", ".txt"), "w") as f:
        f.write(annotation)
        st.experimental_rerun()