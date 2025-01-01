import inkex
from lxml import etree
from inkex import Layer
import uuid

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'

class SiteBoundaries(inkex.EffectExtension):
    def effect(self):
        # Get the scale factor from the document metadata
        scale_factor = self.get_scale_factor()

        # Get the selected object
        obj = next(iter(self.svg.selected.values()), None)

        if obj is None:
            inkex.errormsg("Please select a closed polygon.")
            return

        # Check if the selected object is a closed path
        if obj.tag == inkex.addNS('path', 'svg'):
            path_data = obj.get('d', '').strip().upper()
            if not path_data.endswith('Z'):
                inkex.errormsg("Please select a closed polygon.")
                return

        # Calculate the area of the polygon in square meters
        area_m2 = self.calculate_area(obj.path.to_superpath(), scale_factor)
        area_m2 = round(area_m2, 0)
        inkex.utils.debug(f"The area of the selected polygon is: {area_m2} m²")

        # Find or create the "Base Map" layer
        base_map_layer = self.find_layer("Base Map")
        if base_map_layer is None:
            base_map_layer = self.create_layer("Base Map")

        # Create or find the "site boundaries" sublayer within the "Base Map" layer
        site_boundaries_layer = self.find_layer("site boundaries", base_map_layer)
        if site_boundaries_layer is None:
            site_boundaries_layer = self.create_sublayer(base_map_layer, "site boundaries")

        # Move the polygon to the "site boundaries" sublayer
        site_boundaries_layer.append(obj)

        # Get document dimensions
        svg = self.document.getroot()
        doc_width = self.svg.unittouu(svg.get('width'))
        doc_height = self.svg.unittouu(svg.get('height'))

        # Create a rectangle that covers the entire document
        background_rect = etree.Element(inkex.addNS('rect', 'svg'), {
            'x': '0', 'y': '0',
            'width': str(doc_width), 'height': str(doc_height),
            'style': "fill:#ffffff;fill-opacity:0.7;stroke:none"
        })

        # Add the rectangle to the "site boundaries" sublayer
        site_boundaries_layer.append(background_rect)

        # Create a mask that covers the entire document
        mask_id = 'mask-' + str(uuid.uuid4())
        mask = etree.SubElement(site_boundaries_layer, inkex.addNS('mask', 'svg'), {'id': mask_id})

        # Create a rectangle for the mask
        mask_rect = etree.Element(inkex.addNS('rect', 'svg'), {
            'x': '0', 'y': '0',
            'width': str(doc_width), 'height': str(doc_height),
            'style': "fill:#ffffff"
        })
        mask.append(mask_rect)

        # Add the polygon to the mask, set fill to black to make it fully transparent
        mask_polygon = obj.copy()
        mask_polygon.set('style', "fill:#000000;stroke:none")
        mask.append(mask_polygon)

        # Add text element to display the area
        text_content = f"Site area: {area_m2} m²"
        text_x = 10  # X-coordinate for text position
        text_y = 20  # Y-coordinate for text position
        self.create_text_element(site_boundaries_layer, text_content, text_x, text_y)

        # Apply the mask to the background rectangle
        background_rect.set('mask', f'url(#{mask_id})')

    def calculate_area(self, polygon, scale_factor):
        total_area = 0
        for subpath in polygon:
            if len(subpath) < 3:
                continue

            x = [pt[1][0] for pt in subpath]
            y = [pt[1][1] for pt in subpath]
            area = 0.5 * abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(-1, len(x) - 1)))
            total_area += area

        scaled_area = total_area / (scale_factor ** 2)
        return scaled_area

    def find_layer(self, layer_name, parent=None):
        parent = self.document.getroot() if parent is None else parent
        for layer in parent.iterfind('.//{http://www.w3.org/2000/svg}g'):
            if layer.get(inkex.addNS('label', 'inkscape')) == layer_name:
                return layer
        return None

    def create_layer(self, layer_name):
        layer = Layer.new(layer_name)
        self.document.getroot().append(layer)
        return layer

    def create_sublayer(self, parent_layer, label):
        sublayer = etree.SubElement(parent_layer, 'g')
        sublayer.set(inkex.addNS('label', 'inkscape'), label)
        sublayer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return sublayer

    def get_scale_factor(self):
        try:
            nsmap = {'inkscape': INKSCAPE_NS}
            scale_factor_element = self.svg.find('.//inkscape:scalefactor', namespaces=nsmap)

            if scale_factor_element is not None and scale_factor_element.text:
                return float(scale_factor_element.text)
            else:
                inkex.errormsg("Scale factor not found in the document metadata.")
                return None
        except Exception as e:
            inkex.errormsg(f"Error retrieving scale factor: {str(e)}")
            return None

    def create_text_element(self, layer, text, x, y):
        text_element = etree.SubElement(layer, inkex.addNS('text', 'svg'))
        text_element.text = text
        text_element.set('x', str(x))
        text_element.set('y', str(y))
        text_element.set('style', 'font-size:12px; font-family:Arial')

if __name__ == '__main__':
    SiteBoundaries().run()
