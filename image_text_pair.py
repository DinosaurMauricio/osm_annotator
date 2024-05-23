import os
from PIL import Image

class ImageTextPair:

    def __init__(self, image_path, annotation_path, annotation_osm_path, significative = False):
        self.image_path = image_path
        self.annotation_path = annotation_path
        self.annotation_path_osm = annotation_osm_path 
        self.annotation = self.load_text()
        self.image = self.load_image()
        self.osm_annotation = self.load_osm_text() 
        self.significative = significative

    def load_osm_text(self):
        if not os.path.exists(self.annotation_path_osm):
            return ""

        with open(self.annotation_path_osm, "r", encoding="utf-8") as f:
            return f.read()

    def load_text(self):
        if not os.path.exists(self.annotation_path):
            return ""

        with open(self.annotation_path, "r", encoding="utf-8") as f:
            return f.read()
        
    def load_image(self):
        return Image.open(self.image_path)
    
    def save_annotation(self):
        with open(self.annotation_path, "w", encoding="utf-8") as f:
            f.write(self.annotation)