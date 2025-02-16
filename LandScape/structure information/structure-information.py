import inkex
from lxml import etree
import math

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'

class Structureinformation(inkex.EffectExtension):
    def effect(self):
        # Get the selected polygon
        polygon = next(iter(self.svg.selected.values()), None)
        if polygon is None or polygon.tag != inkex.addNS('path', 'svg'):
            inkex.errormsg("Please select a valid closed polygon.")
            return

        # Ensure the polygon is closed
        path_data = polygon.get('d', '').strip().upper()
        if not path_data.endswith('Z'):
            inkex.errormsg("Selected object is not a closed polygon.")
            return

        # Get the bounding box of the polygon
        bbox = polygon.bounding_box()

        # Get latitude from the document metadata
        latitude = self.get_latitude()
        if latitude is None:
            inkex.errormsg("Latitude not found in the metadata. Please set it using the primary data extension.")
            return

        # Use the original polygon's Inkscape label (or fallback if missing)
        original_name = polygon.get(inkex.addNS('label', 'inkscape')) or "Structure"

        # Create a parent layer for the structure, named after the polygon
        structure_layer = self.create_sublayer(polygon.getparent(), original_name)
        structure_layer.append(polygon)

        # Calculate area and precipitation
        scale_factor = self.get_scale_factor()
        if not scale_factor:
            inkex.errormsg("Scale factor not found. Please set the scaling using the scaling extension.")
            return

        area_m2 = self.calculate_area(polygon, scale_factor)
        annual_rainfall = self.get_precipitation()  # mm/year
        precipitation_volume = (area_m2 * annual_rainfall) / 1000  # Convert mm to m³

        # Add size and precipitation layers
        self.create_text_layer(structure_layer, "size", f"Area: {area_m2:.2f} m²", polygon, bbox, 0.4)
        self.create_text_layer(structure_layer, "precipitation", f"Rainfall: {precipitation_volume:.2f} m³", polygon, bbox, 0.5)

    def create_sublayer(self, parent, name):
        """Create a sublayer with the given name."""
        sublayer = etree.Element(inkex.addNS('g', 'svg'))
        sublayer.set(inkex.addNS('label', 'inkscape'), name)
        sublayer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        parent.append(sublayer)
        return sublayer

    def create_text_layer(self, parent, name, text, polygon, bbox, vertical_position):
        """Create a text sublayer for annotation."""
        width = float(bbox.right - bbox.left)
        height = float(bbox.bottom - bbox.top)
        x = float(bbox.left) + (width / 2)  # Center horizontally
        y = float(bbox.top) + (height * vertical_position)  # Position vertically within the polygon

        font_size = min(width / 10, height / 10)  # Adjust font size to fit within the polygon
        text_layer = self.create_sublayer(parent, name)
        text_element = etree.SubElement(text_layer, inkex.addNS('text', 'svg'))
        text_element.text = text
        text_element.set('x', str(x))
        text_element.set('y', str(y))
        text_element.set('style', f'font-size:{font_size}px; font-family:Arial; text-anchor:middle;')

    def calculate_area(self, polygon, scale_factor):
        """Calculate the area of the polygon."""
        area = 0.0
        points = polygon.path.to_superpath()
        for subpath in points:
            if len(subpath) < 3:  # A polygon must have at least 3 points
                continue
            x = [pt[1][0] for pt in subpath]  # X coordinates
            y = [pt[1][1] for pt in subpath]  # Y coordinates
            area += 0.5 * abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(-1, len(x) - 1)))
        return area / (scale_factor ** 2)  # Scale area to meters squared

    def get_precipitation(self):
        """Retrieve precipitation value from metadata."""
        svg_root = self.document.getroot()
        geo_data = svg_root.find('svg:metadata/inkscape:geodata', inkex.NSS)
        if geo_data is not None:
            precipitation = geo_data.get('annual_rainfall_avg')  # mm/year
            return float(precipitation)
        return 0

    def get_scale_factor(self):
        """Retrieve the scale factor from metadata."""
        svg_root = self.document.getroot()
        nsmap = {'inkscape': INKSCAPE_NS}
        scale_factor_element = svg_root.find('.//inkscape:scalefactor', namespaces=nsmap)
        if scale_factor_element is not None and scale_factor_element.text:
            try:
                return float(scale_factor_element.text)
            except ValueError:
                return None
        return None

    def get_latitude(self):
        """Retrieve latitude from metadata."""
        svg_root = self.document.getroot()
        metadata = svg_root.find('svg:metadata', inkex.NSS)
        if metadata is not None:
            geo_data = metadata.find('inkscape:geodata', inkex.NSS)
            if geo_data is not None:
                latitude = geo_data.get('latitude')
                if latitude:
                    return float(latitude)
        return None

if __name__ == '__main__':
    Structureinformation().run()
