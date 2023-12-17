#!/usr/bin/env python3
import inkex
from lxml import etree
from inkex import Rectangle, Layer
from inkex.paths import Path
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

        # Create a new layer called "site boundaries"
        site_boundaries_layer = self.create_layer("site boundaries")
        
        # Move the polygon to the new layer
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

        # Add the rectangle to the layer
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
            # Assuming each subpath is a closed polygon
            if len(subpath) < 3:  # A polygon must have at least 3 points
                continue

            # Calculate area using the shoelace formula
            x = [pt[1][0] for pt in subpath]  # X coordinates
            y = [pt[1][1] for pt in subpath]  # Y coordinates
            area = 0.5 * abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(-1, len(x) - 1)))
            total_area += area

        # Scale the area based on the scale factor
        scaled_area = total_area / (scale_factor *scale_factor)
        return scaled_area

    def create_layer(self, layer_name):
        layer = Layer.new(layer_name)
        self.document.getroot().append(layer)
        return layer

    def get_scale_factor(self):
        try:
            # Define the namespace map
            nsmap = {'inkscape': INKSCAPE_NS}

            # Use an XPath expression with the correct namespace to find the scalefactor
            scale_factor_element = self.svg.find('.//inkscape:scalefactor', namespaces=nsmap)

            if scale_factor_element is not None and scale_factor_element.text:
                # Convert the text to a float and return it
                return float(scale_factor_element.text)
            else:
                inkex.errormsg("Scale factor not found in the document metadata.")
                return None
        except Exception as e:
            inkex.errormsg(f"Error retrieving scale factor: {str(e)}")
            return None
    
    def create_text_element(self, layer, text, x, y):
        """Create a text element and add it to the specified layer."""
        text_element = etree.SubElement(layer, inkex.addNS('text', 'svg'))
        text_element.text = text
        text_element.set('x', str(x))
        text_element.set('y', str(y))
        text_element.set('style', 'font-size:12px; font-family:Arial')

if __name__ == '__main__':
    SiteBoundaries().run()
