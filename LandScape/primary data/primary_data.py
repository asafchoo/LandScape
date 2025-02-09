import inkex
import requests
from lxml import etree
from datetime import datetime
import base64
import os
import tempfile
from PIL import Image, ImageFilter, ImageEnhance

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'
api_key = "AIzaSyDAblLSzOE_u7wS2OiPrQgsu_z4cdcIBU0"
url = "https://maps.googleapis.com/maps/api/staticmap?"

class PrimaryData(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--latitude", type=str, help="Latitude")
        pars.add_argument("--longitude", type=str, help="Longitude")
        pars.add_argument("--widthofdoc", type=str, help="width of document")
        pars.add_argument("--heightofdoc", type=str, help="height of document")
        pars.add_argument("--zoomlevel", type=str, help="zoom level")
        pars.add_argument("--measured_precipitation", type=str, help="Measured annual precipitation (mm)")
        pars.add_argument("--open_url", type=inkex.Boolean, help="Open Website")

    def effect(self):
        # Retrieve the input values
        lat = self.options.latitude
        lon = self.options.longitude
        widthofdoc = self.options.widthofdoc
        heightofdoc = self.options.heightofdoc
        zoom = self.options.zoomlevel
        measured_precipitation = self.options.measured_precipitation

        # Ensure all required parameters are present
        if not lat or not lon:
            inkex.errormsg("Latitude or Longitude not provided.")
            return

        # Get the SVG root element
        svg_root = self.document.getroot()
        svg_root.set('width', f'{widthofdoc}mm')
        svg_root.set('height', f'{heightofdoc}mm')
        svg_root.set('viewBox', f'0 0 {widthofdoc} {heightofdoc}')

        # Set the document units to mm
        namedview = svg_root.find('sodipodi:namedview', inkex.NSS)
        if namedview is not None:
            namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')
        else:
            namedview = etree.SubElement(svg_root, 'sodipodi:namedview', nsmap=inkex.NSS)
            namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

        # Ensure metadata exists
        metadata = svg_root.find('metadata')
        if metadata is None:
            metadata = etree.SubElement(svg_root, 'metadata')

        # Ensure geodata exists
        inkscape_ns = 'http://www.inkscape.org/namespaces/inkscape'
        geo_data = metadata.find(f'{{{inkscape_ns}}}geodata')
        if geo_data is None:
            geo_data = etree.SubElement(metadata, f'{{{inkscape_ns}}}geodata')

        # Set geodata attributes
        geo_data.set('latitude', lat)
        geo_data.set('longitude', lon)
        geo_data.set('zoomlevel', zoom)

        # Use measured precipitation if provided; otherwise, calculate
        if measured_precipitation:
            geo_data.set('annual_rainfall_avg', measured_precipitation)
        else:
            try:
                average_rainfall = self.calculate_annual_rainfall_average(lat, lon)
                geo_data.set('annual_rainfall_avg', f"{average_rainfall:.2f}")                
            except Exception as e:
                inkex.errormsg(f"Error calculating average rainfall: {str(e)}")
                return

        # Remove the default layer
        self.remove_default_layer(svg_root)

        # Create the structured layers for permaculture design
        self.create_layer_structure(svg_root)

        # Validate geodata before adding the base map
        if geo_data.get('latitude') and geo_data.get('longitude') and geo_data.get('zoomlevel'):
            self.add_base_map(svg_root)
        else:
            inkex.errormsg("Incomplete geodata. Cannot fetch base map.")

        # Open URL if the option is enabled
        if self.options.open_url:
            import webbrowser
            webbrowser.open("http://www.example.com")

    def calculate_annual_rainfall_average(self, lat, lon):
        start_year = datetime.now().year - 20
        end_year = datetime.now().year

        total_rainfall = 0
        years_counted = 0

        for year in range(start_year, end_year):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
                   f"&start_date={start_date}&end_date={end_date}&daily=precipitation_sum&timezone=GMT")
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                daily_precipitation = data.get("daily", {}).get("precipitation_sum", [])
                total_rainfall += sum(value for value in daily_precipitation if value is not None)
                years_counted += 1
            else:
                inkex.errormsg(f"Failed to fetch data for {year}: HTTP {response.status_code}")

        if years_counted == 0:
            raise ValueError("No data retrieved for the last 20 years.")

        return total_rainfall / years_counted

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
            "Energy": ["Solar","Wind","Hidro","Biogas","Biomass"],
            "Vegetation": ["Existing Vegetation", "Annual Gardens", "Orchards", "Companion Planting"],
            "Animals": ["Grazing Areas", "Animal Shelters", "Movement Paths"],
        }

        for parent_layer, sub_layers in layer_structure.items():
            parent = self.create_layer(svg_root, parent_layer)
            for sub_layer in sub_layers:
                self.create_layer(parent, sub_layer)

    def add_base_map(self, svg_root):
        """Fetch and embed the base map image."""
        inkscape_ns = 'http://www.inkscape.org/namespaces/inkscape'
        geo_data = svg_root.find('metadata').find(f'{{{inkscape_ns}}}geodata')

        # Validate that geodata exists and has the required attributes
        if geo_data is not None:
            lat = geo_data.get('latitude')
            lon = geo_data.get('longitude')
            zoom = geo_data.get('zoomlevel')

            if lat and lon and zoom:
                try:
                    # Fetch the base map image from Google Maps API
                    response = requests.get(
                        f"{url}center={lat},{lon}&zoom={zoom}&size=2108x2108&scale=2&maptype=hybrid&key={api_key}"
                    )
                    if response.status_code == 200:
                        # Save the image temporarily
                        temp = tempfile.NamedTemporaryFile(delete=False)
                        temp.write(response.content)
                        temp.close()

                        # Crop and resize the image
                        cropped_image_path = self.crop_and_resize_image(temp.name, svg_root)

                        # Embed the image into the SVG
                        href = self.embed_image(cropped_image_path)

                        # Ensure the "Satellite Map" layer exists
                        base_map_layer = self.find_layer("Base Map")
                        if base_map_layer is None:
                            base_map_layer = self.create_layer(svg_root, "Base Map")

                        satellite_layer = self.find_layer("Satellite Map")
                        if satellite_layer is None:
                            satellite_layer = self.create_layer(base_map_layer, "Satellite Map")

                        # Fetch the document dimensions
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

                        # Clean up temporary file
                        os.unlink(temp.name)
                    else:
                        inkex.errormsg(f"Failed to fetch base map. HTTP {response.status_code}")
                except Exception as e:
                    inkex.errormsg(f"Error while fetching or embedding base map: {str(e)}")
            else:
                inkex.errormsg("Latitude, Longitude, or Zoom level missing in geodata.")
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
    PrimaryData().run()
