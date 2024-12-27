#!/usr/bin/env python3
import inkex
from lxml import etree
import requests
import base64
import os
import tempfile
from PIL import Image, ImageFilter, ImageEnhance

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'

api_key = "AIzaSyDAblLSzOE_u7wS2OiPrQgsu_z4cdcIBU0"
url = "https://maps.googleapis.com/maps/api/staticmap?"

class BaseMap(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--latitude", type=str, help="Latitude")
        pars.add_argument("--longitude", type=str, help="Longitude")
        pars.add_argument("--zoomlevel", type=str, help="Zoom level")
        pars.add_argument("--art_my_map", type=inkex.Boolean, default=False, help="Apply artistic filter to the map image.")

    def effect(self):
        # Retrieve parameters
        art_my_map = self.options.art_my_map

        # Debugging: Log the status of the art_my_map parameter
        inkex.utils.debug(f"Art My Map option: {art_my_map}")

        # Get the SVG root element
        svg_root = self.document.getroot()

        # Remove the default layer
        self.remove_default_layer(svg_root)

        # Create the structured layers for permaculture design
        self.create_layer_structure(svg_root)

        # Optionally fetch and add the base map image
        self.add_base_map(svg_root, art_my_map)

    def remove_default_layer(self, svg_root):
        """Remove the default 'Layer 1' if it exists."""
        layer = self.find_layer("Layer 1")
        if layer is not None:
            layer.getparent().remove(layer)

    def create_layer_structure(self, svg_root):
        """Create a structured hierarchy of layers and sub-layers."""
        layer_structure = {
            "Base Map": ["Satellite Map", "Aerial Map", "Scale Measure", "Calculated Elevation Map", "Measured Elevation Map"],
            "Water Analysis": ["Keyline Analysis", "Precipitation", "Flows"],
            "Sectors": ["Sun Path", "Wind Patterns", "Noise/Visibility Zones"],
            "Zones": ["Zone 0", "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"],
            "Structures": ["Existing Structures", "Planned Structures", "Temporary Structures"],
            "Vegetation": ["Existing Vegetation", "Annual Gardens", "Orchards", "Companion Planting"],
            "Animals": ["Grazing Areas", "Animal Shelters", "Movement Paths"],
        }

        for parent_layer, sub_layers in layer_structure.items():
            parent = self.create_layer(svg_root, parent_layer)
            for sub_layer in sub_layers:
                self.create_layer(parent, sub_layer)

    def add_base_map(self, svg_root, art_my_map):
        """Fetch and embed the base map image."""
        geo_data = svg_root.find('svg:metadata/inkscape:geodata', inkex.NSS)
        if geo_data is not None:
            lat = geo_data.get('latitude')
            lon = geo_data.get('longitude')
            zoom = int(geo_data.get('zoomlevel'))

            if lat and lon:
                response = requests.get(
                    f"{url}center={lat},{lon}&zoom={zoom}&size=2108x2108&scale=2&maptype=hybrid&key={api_key}"
                )
                if response.status_code == 200:
                    temp = tempfile.NamedTemporaryFile(delete=False)
                    temp.write(response.content)
                    temp.close()

                    # Apply artistic filter if selected
                    if art_my_map:
                        self.apply_artistic_filter(temp.name)

                    # Crop the image and then stretch it
                    cropped_image_path = self.crop_and_resize_image(temp.name, svg_root)

                    href = self.embed_image(cropped_image_path)

                    # Ensure the "Satellite Map" layer exists
                    base_map_layer = self.find_layer("Base Map")
                    if base_map_layer is None:
                        base_map_layer = self.create_layer(svg_root, "Base Map")

                    satellite_layer = self.find_layer("Satellite Map")
                    if satellite_layer is None:
                        satellite_layer = self.create_layer(base_map_layer, "Satellite Map")

                    # Fetch the document dimensions and convert them to float
                    doc_width = self.convert_to_mm(svg_root.get('width'))
                    doc_height = self.convert_to_mm(svg_root.get('height'))

                    # Add the image to the "Satellite Map" layer
                    image = inkex.Image(href=href)
                    image.set('x', '0')
                    image.set('y', '0')
                    image.set('width', str(doc_width))
                    image.set('height', str(doc_height))
                    image.set('id', 'satellite image')  # Set proper ID
                    satellite_layer.append(image)

                    os.unlink(temp.name)
                else:
                    inkex.errormsg(f"Failed to fetch base map. HTTP {response.status_code}")
            else:
                inkex.errormsg("Latitude or Longitude metadata not found.")
        else:
            inkex.errormsg("No geodata found in metadata.")

    def crop_and_resize_image(self, image_path, svg_root):
        """Crop 20mm from all sides of the image and resize it to match the document size."""
        try:
            img = Image.open(image_path)

            # Convert document dimensions to pixels (assuming 96 DPI)
            doc_width_px = int(self.convert_to_mm(svg_root.get('width')) / 0.264583)
            doc_height_px = int(self.convert_to_mm(svg_root.get('height')) / 0.264583)

            # Calculate crop box (10mm in pixels)
            crop_margin = int(10 / 0.264583)
            crop_box = (
                crop_margin,  # left
                crop_margin,  # top
                img.width - crop_margin,  # right
                img.height - crop_margin  # bottom
            )

            # Crop the image
            cropped_img = img.crop(crop_box)

            # Resize to document dimensions
            resized_img = cropped_img.resize((doc_width_px, doc_height_px), Image.LANCZOS)

            # Save the modified image
            cropped_resized_path = image_path + "_cropped_resized.png"
            resized_img.save(cropped_resized_path, format="PNG")

            return cropped_resized_path
        except Exception as e:
            inkex.errormsg(f"Failed to crop and resize image: {e}")
            return image_path

    def apply_artistic_filter(self, image_path):
        """Apply a watercolor-like artistic filter."""
        try:
            img = Image.open(image_path)
            img = img.quantize(colors=64, method=Image.FASTOCTREE).convert("RGB")
            img = img.filter(ImageFilter.SMOOTH_MORE)
            img.save(image_path, format="PNG")
        except Exception as e:
            inkex.errormsg(f"Failed to apply artistic filter: {e}")

    def create_layer(self, parent, layer_name):
        """Create a new layer."""
        new_layer = inkex.Layer.new(layer_name)
        parent.append(new_layer)
        return new_layer

    def find_layer(self, layer_name):
        """Find an existing layer by its name."""
        nsmap = {'svg': 'http://www.w3.org/2000/svg', 'inkscape': INKSCAPE_NS}
        layers = self.document.getroot().xpath(f"//svg:g[@inkscape:label='{layer_name}']", namespaces=nsmap)
        return layers[0] if layers else None

    def embed_image(self, file_path):
        """Embed an image into the SVG document."""
        with open(file_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{image_data}"

    def convert_to_mm(self, dimension):
        """Convert dimension strings to millimeters."""
        if dimension.endswith("mm"):
            return float(dimension[:-2])
        elif dimension.endswith("px"):
            return float(dimension[:-2]) * 0.264583  # Assuming 96 DPI to convert pixels to mm
        else:
            raise ValueError("Unsupported dimension format: " + dimension)

if __name__ == "__main__":
    BaseMap().run()
