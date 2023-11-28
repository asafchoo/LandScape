#!/usr/bin/env python3
import inkex
from lxml import etree
import math
from inkex.paths import CubicSuperPath

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'

class scaling(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--linetometer", type=str, help="Length of Line")
        pars.add_argument("--override", type=inkex.Boolean, help="Override existing scaling?")

    def effect(self):
        # Get the first selected object which should be the line or path
        obj = next(iter(self.svg.selected.values()), None)

        if obj is None:
            inkex.errormsg("Please select a line or a path.")
            return

        # Measure the length of the line or path
        length = self.measure_line(obj)
        if length == 0: return  # Exit if no valid object is selected
        
        # Convert the line length to meters using the user input
        real_length_meters = int(length) / float(self.options.linetometer)

        # Check for existing scale factor and override if needed
        if self.options.override:
            self.override_metadata(real_length_meters)
        else:
            self.store_metadata(real_length_meters)
        
        # After storing metadata, draw the scale stripe
        self.draw_scale_stripe(real_length_meters, "Base Map")

    def measure_line(self, obj):
        if obj.tag == inkex.addNS('line', 'svg'):
            # It's a line, get attributes as before
            x1, y1, x2, y2 = obj.get('x1'), obj.get('y1'), obj.get('x2'), obj.get('y2')
            if None in (x1, y1, x2, y2):
                inkex.errormsg("Selected line object does not have valid attributes.")
                return 0
            return math.sqrt((float(x2) - float(x1))**2 + (float(y2) - float(y1))**2)
        elif obj.tag == inkex.addNS('path', 'svg'):
            # It's a path, calculate its length
            d = obj.get('d')
            if d:
                path = CubicSuperPath(d)
                return self.calculate_path_length(path)
            else:
                inkex.errormsg("Selected path object does not have a valid 'd' attribute.")
                return 0
        else:
            inkex.errormsg("Selected object is not a line or path.")
            return 0

    def calculate_path_length(self, path):
        # Calculate the total length of the path
        total_length = 0.0
        for subpath in path:
            if len(subpath) > 1:
                for i in range(1, len(subpath)):
                    p1 = subpath[i-1][1]
                    p2 = subpath[i][1]
                    total_length += distance(p1, p2)
        return total_length
  
    def override_metadata(self, length):
        svg_root = self.document.getroot()
    
        # Define the namespace map
        nsmap = {'inkscape': INKSCAPE_NS}
    
        # Find all scalefactor elements using xpath
        scale_factors = svg_root.xpath('//inkscape:scalefactor', namespaces=nsmap)
    
        # Remove the parent <metadata> elements of each <inkscape:scalefactor>
        for scale_factor in scale_factors:
            parent = scale_factor.getparent()
            if parent is not None:
                grandparent = parent.getparent()
                if grandparent is not None:
                    # Remove the parent <metadata> element
                    grandparent.remove(parent)
                    inkex.utils.debug("Old scale factor and its parent metadata removed.")


        # Create a new <metadata> element and store the new scale factor
        self.store_metadata(length)

    def store_metadata(self, length):
        svg_root = self.document.getroot()
    
        # Look for an existing <metadata> element
        metadata = svg_root.find('metadata')
        if metadata is None:
            # If it does not exist, create a new <metadata> element
            metadata = etree.SubElement(svg_root, 'metadata')

        # Remove any existing scalefactor element
        for scale_factor in metadata.findall('{http://www.inkscape.org/namespaces/inkscape}scalefactor'):
            metadata.remove(scale_factor)

        # Create new scalefactor element
        scale_factor = etree.SubElement(metadata, '{http://www.inkscape.org/namespaces/inkscape}scalefactor')
        scale_factor.text = str(length)
        inkex.utils.debug("New scaling successful.")
    
    def draw_scale_stripe(self, scale_factor, layer_name):
        # Find or create the "Base Map" layer
        layer = self.find_layer(layer_name)
        if layer is None:
            inkex.errormsg(f"Layer '{layer_name}' not found. Please create the layer and try again.")
            return
            
        svg = self.document.getroot()
        width = self.svg.unittouu(svg.get('width'))
        height = self.svg.unittouu(svg.get('height'))

        # Calculate the position and size of the stripe
        stripe_height = self.svg.unittouu('10mm')
        stripe_y = -stripe_height -5  # 10mm above the document
        
        # Calculate the number of years to represent
        num_years = int(width / scale_factor)

         # Define the heights for different types of lines
        normal_line_height = self.svg.unittouu('5mm')  # Normal year line
        five_year_line_height = self.svg.unittouu('7mm')  # Every 5 years
        ten_year_line_height = self.svg.unittouu('10mm')  # Every 10 years

        # Y-position for the top of the scale
        scale_y_top = 0

        for i in range(num_years):
            # Determine the height of the line
            if i % 10 == 0:
                line_height = ten_year_line_height
            elif i % 5 == 0:
                line_height = five_year_line_height
            else:
                line_height = normal_line_height

            # X-position for each line
            line_x = i * scale_factor

            # Create the line element
            line = etree.Element(inkex.addNS('line', 'svg'), {
                'x1': str(line_x),
                'y1': str(scale_y_top),
                'x2': str(line_x),
                'y2': str(scale_y_top - line_height),
                'style': 'stroke:black; stroke-width:1;'
            })
            layer.append(line)

        # Create the base rectangle
        stripe = etree.Element(inkex.addNS('rect', 'svg'), {
            'x': '0',
            'y': str(scale_y_top),
            'width': str(width),
            'height': str(ten_year_line_height),
            'style': 'fill:grey; fill-opacity:0.5; stroke:none;'
        })
        layer.insert(0, stripe)  # Insert the stripe at the bottom layer

        # Create the text element for the scale factor
        text = etree.Element(inkex.addNS('text', 'svg'), {
            'x': str(width / 2),
            'y': str(stripe_y - 5),  # 5mm above the stripe
            'style': 'text-anchor:middle; font-size:10px; fill:black;'
        })
        text.text = "{:.1f}".format(width / scale_factor)
        layer.append(text)

    def find_layer(self, layer_name):
        svg_root = self.document.getroot()
        # Define the namespace map for the XPath search
        nsmap = {'svg': 'http://www.w3.org/2000/svg', 'inkscape': INKSCAPE_NS}

        # Use an XPath expression with the correct namespace to find all g elements with the specified label
        layer = svg_root.xpath(f"//svg:g[@inkscape:label='{layer_name}']", namespaces=nsmap)
    
        # The xpath method returns a list of found elements. We return the first one, or None if the list is empty.
        return layer[0] if layer else None

    def create_layer(self, layer_name):
        # Create a new layer with the given name
        layer = etree.Element(inkex.addNS('g', 'svg'), {
            inkex.addNS('label', 'inkscape'): layer_name,
            inkex.addNS('groupmode', 'inkscape'): 'layer'
        })
        self.document.getroot().append(layer)
        return layer
        
# Helper function to calculate distance between two points
def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

if __name__ == '__main__':
    scaling().run()
