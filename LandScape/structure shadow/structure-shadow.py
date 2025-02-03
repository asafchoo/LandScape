import inkex
from lxml import etree
import math
from inkex.paths import Line, Move
from inkex.turtle import PathBuilder

class StructureShadow(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--heightofstructure", type=float, default=0, help="Height of the structure (in meters).")
    
    def effect(self):
        # Retrieve structure height
        structure_height = self.options.heightofstructure
        if structure_height <= 0:
            inkex.errormsg("Invalid height. Please enter a positive numeric value.")
            return
        
        # Get the selected polygon
        polygon = next(iter(self.svg.selected.values()), None)
        if polygon is None or polygon.tag != inkex.addNS('path', 'svg'):
            inkex.errormsg("Please select a valid closed polygon.")
            return
        
        # Get latitude from metadata
        latitude = self.get_latitude()
        if latitude is None:
            inkex.errormsg("Latitude not found in the metadata. Please set it using the primary data extension.")
            return
        
        # Retrieve the scale factor
        scale_factor = self.get_scale_factor()
        if scale_factor is None:
            inkex.errormsg("Scale factor not found. Please set the scaling using the scaling extension.")
            return
        
        # Calculate shadow length and azimuth
        shadow_length, sun_azimuth = self.calculate_shadow(latitude, structure_height)
        
        # Convert shadow length to document units
        shadow_offset = shadow_length * scale_factor

        # Create shadow layer
        parent_layer = self.get_parent_layer(polygon)
        shadow_layer = self.create_shadow_layer(parent_layer, "Winter Shadow")
        original_shadow, offset_shadow = self.create_shadow_polygons(polygon, shadow_layer, shadow_offset, sun_azimuth)

        # Call extrusion logic
        self.extrude_between_shadows(shadow_layer, original_shadow, offset_shadow)
        inkex.utils.debug(f"Shadow length:{shadow_length} Shadow azimuth:{sun_azimuth}.")

    def extrude_between_shadows(self, shadow_layer, original_shadow, offset_shadow):
        """Create a single bounding polygon that covers both shadows and clean up the layers."""
        combined_layer = etree.SubElement(shadow_layer, inkex.addNS('g', 'svg'))
        combined_layer.set(inkex.addNS('label', 'inkscape'), 'Combined Shadow')
        combined_layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        # Extract node coordinates
        original_nodes = [seg[1] for seg in original_shadow.path.to_superpath()[0]]
        offset_transform = offset_shadow.get("transform")
        dx, dy = 0, 0
        if offset_transform and "translate" in offset_transform:
            translate_values = offset_transform.replace("translate(", "").replace(")", "").split(",")
            dx, dy = float(translate_values[0]), float(translate_values[1])
        offset_nodes = [[seg[1][0] + dx, seg[1][1] + dy] for seg in offset_shadow.path.to_superpath()[0]]

        # Combine all nodes
        all_nodes = original_nodes + offset_nodes

        # Compute Convex Hull
        hull = self.compute_convex_hull(all_nodes)

        # Create SVG path for the Convex Hull
        path_data = "M " + " L ".join([f"{point[0]},{point[1]}" for point in hull]) + " Z"

        # Remove all other paths inside "Winter Shadow"
        for path in shadow_layer.findall(".//" + inkex.addNS("path", "svg")):
            shadow_layer.remove(path)

        # Create the final shadow path
        shadow_path = inkex.PathElement()
        shadow_path.set("d", path_data)
        shadow_path.style = inkex.Style({"fill": "black", "stroke": "none", "fill-opacity": "0.5"})

        # Assign time label based on hour angle
        shadow_time = self.get_shadow_time()
        shadow_path.set(inkex.addNS('label', 'inkscape'), shadow_time)

        # Add the path to "Winter Shadow"
        shadow_layer.append(shadow_path)

        # Remove "Combined Shadow" layer
        shadow_layer.remove(combined_layer)

        inkex.utils.debug(f"Shadow successfully created for {shadow_time}.")

    def get_shadow_time(self):
        """Retrieve the time from the existing hour angle."""
        hour_angle_degrees = -44.54  # 15:00
        local_solar_time = 12 + (hour_angle_degrees / 15)

        # Convert to HH:MM format
        hours = int(local_solar_time)
        minutes = int((local_solar_time - hours) * 60)
        return f"{hours:02}:{minutes:02}"


    def compute_convex_hull(self, points):
        """Compute the convex hull of a set of 2D points."""
        # Sort the points lexicographically (by x, then by y)
        points = sorted(points)

        # Build the lower hull
        lower = []
        for p in points:
            while len(lower) >= 2 and self.cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        # Build the upper hull
        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and self.cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        # Concatenate lower and upper hulls (excluding the last point of each because it's repeated)
        return lower[:-1] + upper[:-1]

    def cross(self, o, a, b):
        """Calculate the cross product of vectors OA and OB.
        A positive cross product indicates a counter-clockwise turn, and a negative indicates a clockwise turn.
        """
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


    def create_shadow_polygons(self, polygon, shadow_layer, shadow_offset, azimuth_angle):
        """Create two separate shadow polygons: one at the original position and one at the offset."""
        # Remove any pre-existing shadow paths in the shadow layer to avoid duplicates
        existing_paths = shadow_layer.findall(".//" + inkex.addNS("path", "svg"))
        for path in existing_paths:
            shadow_layer.remove(path)

        # Create original shadow polygon (at the same location)
        original_shadow = polygon.copy()
        original_shadow.set("id", f"shadow_original_{id(original_shadow)}")
        shadow_layer.append(original_shadow)

        # Since the computed azimuth is the direction of the sun, the shadow points in the opposite direction.
        shadow_direction = (azimuth_angle + 180) % 360
        
        # Convert polar coordinates (using north as 0°) to SVG coordinates (x right, y down, with north up)
        azimuth_rad = math.radians(shadow_direction)
        dx = shadow_offset * math.sin(azimuth_rad)
        dy = -shadow_offset * math.cos(azimuth_rad)

        # Create offset shadow polygon
        offset_shadow = polygon.copy()
        offset_shadow.set("id", f"shadow_offset_{id(offset_shadow)}")
        offset_shadow.set("transform", f"translate({dx},{dy})")
        shadow_layer.append(offset_shadow)

        return original_shadow, offset_shadow

    def calculate_shadow(self, latitude, height):
        """Calculate shadow length and sun azimuth angle."""
        declination = math.radians(-23.44)  # Solar declination for winter solstice
        hour_angle = math.radians(-44.54)  # Hour angle 
        latitude_rad = math.radians(latitude)

        # Compute sun altitude angle
        sun_altitude_rad = math.asin(math.sin(declination) * math.sin(latitude_rad) +
                                     math.cos(declination) * math.cos(latitude_rad) * math.cos(hour_angle))
        sun_altitude = math.degrees(sun_altitude_rad)

        # Compute shadow length (height / tan(sun altitude))
        shadow_length = height / max(math.tan(sun_altitude_rad), 0.01)  # Avoid division by zero

        # Compute solar azimuth angle
        sin_azimuth = -math.cos(declination) * math.sin(hour_angle) / math.cos(sun_altitude_rad)
        cos_azimuth = (math.sin(declination) - math.sin(latitude_rad) * math.sin(sun_altitude_rad)) / (math.cos(latitude_rad) * math.cos(sun_altitude_rad))
        sun_azimuth = math.degrees(math.atan2(sin_azimuth, cos_azimuth))

        # Convert azimuth to range [0, 360)
        if sun_azimuth < 0:
            sun_azimuth += 360

        return shadow_length, sun_azimuth

    def get_parent_layer(self, element):
        """Find the parent layer of the given element."""
        parent = element.getparent()
        while parent is not None and parent.tag != inkex.addNS('g', 'svg'):
            parent = parent.getparent()
        return parent

    def create_shadow_layer(self, parent_layer, name):
        """Create a shadow layer under the given parent layer."""
        shadow_layer = etree.Element(inkex.addNS('g', 'svg'))
        shadow_layer.set(inkex.addNS('label', 'inkscape'), name)
        shadow_layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        parent_layer.insert(0, shadow_layer)  # Insert as the lowest layer
        return shadow_layer

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
    
    def get_scale_factor(self):
        """Retrieve the scale factor from metadata."""
        svg_root = self.document.getroot()
        scale_factor_element = svg_root.find('.//inkscape:scalefactor', namespaces={'inkscape': 'http://www.inkscape.org/namespaces/inkscape'})
        if scale_factor_element is not None and scale_factor_element.text:
            try:
                return float(scale_factor_element.text)
            except ValueError:
                return None
        return None

if __name__ == '__main__':
    StructureShadow().run()
