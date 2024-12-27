#!/usr/bin/env python3
import inkex
from lxml import etree
from inkex.paths import CubicSuperPath
import math

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
        if length == 0:
            return  # Exit if no valid object is selected

        # Convert the line length to meters using the user input
        real_length_meters = int(length) / float(self.options.linetometer)

        # Check for existing scale factor and override if needed
        if self.options.override:
            self.override_metadata(real_length_meters)
        else:
            self.store_metadata(real_length_meters)

        # Delete the original line or path used as reference before any changes
        self.remove_reference_object(obj)

        # Create or update the "Scale Measure" layer
        self.update_scale_layer(real_length_meters)

        # Draw the scale
        self.draw_scale(real_length_meters)

    def measure_line(self, obj):
        if obj.tag == inkex.addNS('line', 'svg'):
            x1, y1, x2, y2 = obj.get('x1'), obj.get('y1'), obj.get('x2'), obj.get('y2')
            if None in (x1, y1, x2, y2):
                inkex.errormsg("Selected line object does not have valid attributes.")
                return 0
            return ((float(x2) - float(x1)) ** 2 + (float(y2) - float(y1)) ** 2) ** 0.5
        elif obj.tag == inkex.addNS('path', 'svg'):
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
        total_length = 0.0
        for subpath in path:
            for i in range(1, len(subpath)):
                p1 = subpath[i - 1][1]
                p2 = subpath[i][1]
                total_length += ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
        return total_length

    def override_metadata(self, length):
        svg_root = self.document.getroot()
        nsmap = {'inkscape': INKSCAPE_NS}
        scale_factors = svg_root.xpath('//inkscape:scalefactor', namespaces=nsmap)
        for scale_factor in scale_factors:
            parent = scale_factor.getparent()
            if parent is not None:
                grandparent = parent.getparent()
                if grandparent is not None:
                    grandparent.remove(parent)
        self.store_metadata(length)

    def store_metadata(self, length):
        svg_root = self.document.getroot()
        metadata = svg_root.find('metadata')
        if metadata is None:
            metadata = etree.SubElement(svg_root, 'metadata')
        for scale_factor in metadata.findall('{%s}scalefactor' % INKSCAPE_NS):
            metadata.remove(scale_factor)
        scale_factor = etree.SubElement(metadata, '{%s}scalefactor' % INKSCAPE_NS)
        scale_factor.text = str(length)

    def update_scale_layer(self, scale_factor):
        svg_root = self.document.getroot()
        scale_layer = self.find_or_create_layer("Scale Measure")

        # Remove the empty path element with ID "scale" if it exists
        empty_scale_path = scale_layer.xpath(".//*[@id='scale']")
        if empty_scale_path:
            for path in empty_scale_path:
                path.getparent().remove(path)
                inkex.utils.debug("Removed empty path element 'scale'.")

    def draw_scale(self, scale_factor):
        svg_root = self.document.getroot()
        scale_layer = self.find_or_create_layer("Scale Measure")

        # Define scale parameters
        svg_width = self.svg.unittouu(svg_root.get('width'))
        num_segments = int(svg_width / scale_factor)
        y_position = 0
        segment_height = 10

        # Create scale lines
        combined_path_d = ""
        for i in range(num_segments + 1):
            x_position = i * scale_factor
            line_height = segment_height if i % 5 == 0 else segment_height / 2

            line_d = f"M {x_position},{y_position} L {x_position},{y_position - line_height} "
            combined_path_d += line_d

        # Add the combined path for the scale lines
        combined_path = etree.Element(inkex.addNS('path', 'svg'), {
            'd': combined_path_d.strip(),
            'style': 'stroke:black;stroke-width:1;',
            'id': 'scale-lines'
        })
        scale_layer.append(combined_path)

        # Add text for width in meters
        width_in_meters = svg_width / scale_factor
        text = etree.Element(inkex.addNS('text', 'svg'), {
            'x': str(svg_width / 2),
            'y': str(y_position - 20),
            'style': 'text-anchor:middle;font-size:12px;fill:black;',
            'id': 'scale title'
        })
        text.text = f"{width_in_meters:.1f} meters"
        scale_layer.append(text)

    def remove_reference_object(self, obj):
        if obj is not None:
            try:
                inkex.utils.debug(f"Attempting to remove reference object {obj.get('id', 'unknown')}.")
                obj_id = obj.get("id", "unknown")  # Save ID for verification

                # Try inkex's delete method
                try:
                    obj.delete()
                    inkex.utils.debug(f"delete() method used successfully for {obj_id}.")
                except AttributeError:
                    inkex.utils.debug("delete() method not available; falling back to parent.remove().")
                    # Fallback if delete() is not supported
                    parent = obj.getparent()
                    if parent is not None:
                        parent.remove(obj)
                        inkex.utils.debug(f"Fallback parent.remove() used successfully for {obj_id}.")

                # Re-check to verify it's removed from the DOM
                svg_root = self.document.getroot()
                existing = svg_root.xpath(f"//*[@id='{obj_id}']")
                if existing:
                    inkex.errormsg(f"Failed to remove the reference object with ID {obj_id}: still exists.")
                else:
                    inkex.utils.debug(f"Reference object with ID {obj_id} successfully removed.")

                # Final forced removal via XPath if still exists
                if existing:
                    for element in existing:
                        element.getparent().remove(element)
                    inkex.utils.debug(f"Reference object with ID {obj_id} forcibly removed via XPath.")

            except Exception as e:
                inkex.errormsg(f"Failed to remove the reference object: {e}")
        else:
            inkex.errormsg("Reference object is None and cannot be removed.")

    def find_or_create_layer(self, layer_name):
        svg_root = self.document.getroot()
        layer = self.find_layer(layer_name)
        if layer is None:
            layer = etree.SubElement(svg_root, 'g', {
                inkex.addNS('label', 'inkscape'): layer_name,
                inkex.addNS('groupmode', 'inkscape'): 'layer'
            })
        return layer

    def find_layer(self, layer_name):
        nsmap = {'svg': 'http://www.w3.org/2000/svg', 'inkscape': INKSCAPE_NS}
        layers = self.document.getroot().xpath(f"//svg:g[@inkscape:label='{layer_name}']", namespaces=nsmap)
        return layers[0] if layers else None

if __name__ == '__main__':
    scaling().run()
