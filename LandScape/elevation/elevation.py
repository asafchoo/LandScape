#!/usr/bin/env python3
import inkex
import requests
import math
from lxml import etree
import logging

# Set up logging to file
logging.basicConfig(filename='C:\\Users\\hamaadama\\Desktop\\debug.log', level=logging.DEBUG, filemode='w')

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'

def log(message):
    """Helper function to log a message to the debug.log file."""
    logging.debug(message)
    
class ElevationMapExtension(inkex.Effect):
    def add_arguments(self, pars):
        pars.add_argument("--num_points", type=int, default=350, help="Number of points along one side of the grid")
        pars.add_argument("--threshold", type=int, default=2, help="accuracy of path seperation")
        pars.add_argument("--max_distance", type=int, default=10, help="distance between paths")
        pars.add_argument("--contour_gaps", type=int, default=1, help="gaps between contour lines - default is 1m")

    # Initialize variables for minimum and maximum elevation
    # Initialize variables for minimum and maximum elevation
    # Initialize variables for minimum and maximum elevation
    # Initialize variables for minimum and maximum elevation
    # Initialize variables for minimum and maximum elevation
    # Initialize variables for minimum and maximum elevation
    # Initialize variables for minimum and maximum elevation
    min_elevation = float('inf')
    max_elevation = float('-inf')
    
    def effect(self):
        scale = None
        threshold = self.options.threshold
        # Get the SVG root element and extract the width and height of the document
        svg_root = self.document.getroot()
        doc_width = self.svg.unittouu(svg_root.get('width'))
        doc_height = self.svg.unittouu(svg_root.get('height'))
        
        # Create "elevation" layer as the parent layer
        elevation_layer = self.create_parent_layer(svg_root, "elevation")
        
        # Retrieve the custom namespaced geodata element for center coordinates
        geo_data = svg_root.find('svg:metadata/inkscape:geodata', inkex.NSS)
        center_lat = float(geo_data.get('latitude'))
        center_lon = float(geo_data.get('longitude'))
        
        scale = self.get_scale_factor()
        
        # Constants for conversion
        meters_per_degree = 111139  # Average meters per degree of lat/long

        # Calculate number of points and spacing in the grid
        num_points = self.options.num_points
        spacing_mm_x = doc_width / (num_points - 1)
        spacing_mm_y = doc_height / (num_points - 1)

        # Google Elevation API Key
        api_key = 'AIzaSyDAblLSzOE_u7wS2OiPrQgsu_z4cdcIBU0'

        # Initialize empty list for storing elevation data and batch requests
        elevation_data = []
        batch_requests = []
        grid_points = []
        elevation_groups = {}

        # Generate grid points and create batch requests
        for i in range(num_points):
            for j in range(num_points):
                # Calculate grid coordinates
                x = i * spacing_mm_x
                y = doc_height - (j * spacing_mm_y)  # This flips the y-coordinate
 
                # Calculate latitude and longitude for each point
                lat = center_lat + ((doc_height / 2 - y) / scale) / meters_per_degree
                lon = center_lon + ((x - doc_width / 2) / scale) / (meters_per_degree * math.cos(math.radians(center_lat)))

                # Add grid coordinates with corresponding lat-lon to the list
                grid_points.append((x, y, lat, lon))

        # Create batch requests using grid_points list for Google Elevation API
        for x, y, lat, lon in grid_points:
            new_location = f"{lat},{lon}"
            if len(batch_requests) == 0 or len(batch_requests[-1] + new_location) + 1 >= 8192:
                batch_requests.append(f"https://maps.googleapis.com/maps/api/elevation/json?locations={new_location}")
            else:
                batch_requests[-1] += '|' + new_location

        # Append API key to each request
        for i in range(len(batch_requests)):
            batch_requests[i] += f"&key={api_key}"

        # Fetch elevation data in batches
        grid_point_index = 0
        for request in batch_requests:
            batch_elevation_data = self.fetch_elevation_batch(request)
            for elevation, lat, lon in batch_elevation_data:
                # Get the corresponding grid point
                x, y, lat, lon = grid_points[grid_point_index]
                grid_point_index += 1
                
                # Calculate the fractional part of the elevation
                fractional_part = elevation - int(elevation)
                
                # Check if the fractional part is within 0.15 of being a whole number
                if fractional_part > 0.05 and fractional_part < 0.95:
                    continue  # Skip this point
        
                rounded_elevation = self.round_elevation(elevation)
                contour_gaps = self.options.contour_gaps
                
                if rounded_elevation % contour_gaps != 0:
                    continue # Skip contour 
                    
                # Store the data with grid coordinates
                point_data = {
                    'elevation': rounded_elevation,
                    'latitude': lat,
                    'longitude': lon,
                    'x': x,
                    'y': y
                }

                # Add the point to the appropriate elevation group 
                if rounded_elevation not in elevation_groups:
                    elevation_groups[rounded_elevation] = []
                elevation_groups[rounded_elevation].append(point_data)

                # Update min and max elevations
                self.min_elevation = min(self.min_elevation, rounded_elevation)
                self.max_elevation = max(self.max_elevation, rounded_elevation)
        
        sublayers = []  # List to store sublayers

        # Create SVG layers and draw circles and lines
        for rounded_elevation, points in elevation_groups.items():
            # Create a sublayer for each elevation group
            layer_label = f'{rounded_elevation}m'
            sublayer = self.create_sublayer(elevation_layer, layer_label)

            # Now, for each point in points, create paths and add them to the sublayer
            for point in points:
                # Assume create_path returns an SVG path element for the given point
                path_element = self.create_path_element([point], "black")
                sublayer.append(path_element)  # Add the path to the sublayer, not the main layer
            
            self.create_paths_for_group(sublayer, points,threshold)
            self.consolidate_paths(sublayer)
            sublayers.append((rounded_elevation, sublayer))
        
        for _, sublayer in sorted(sublayers, key=lambda x: x[0], reverse=True):
            elevation_layer.append(sublayer)

    # Method to find a layer by label
    def find_layer(self, svg_root, label):
        for layer in svg_root.iterfind('.//{http://www.w3.org/2000/svg}g'):
            if layer.get(inkex.addNS('label', 'inkscape')) == label:
                return layer
        return None
      
    def draw_circle(self, parent, x, y, lat, lon, elevation):
        # Create a new circle element with calculated color and opacity
        circle = etree.SubElement(parent, inkex.addNS('circle', 'svg'))
        circle.set('style', f'stroke:none;fill:black;fill-opacity:1')
        circle.set('r', str(self.svg.unittouu('1mm')))
        circle.set('cx', str(x))
        circle.set('cy', str(y))

        # Add a title element to the circle to store the coordinates
        title = etree.SubElement(circle, 'title')
        title.text = f"Lat: {lat}, Lon: {lon}"
        return circle

    def fetch_elevation_batch(self, request):
        try:
            response = requests.get(request)
            data = response.json()
            return [(result['elevation'], result['location']['lat'], result['location']['lng']) for result in data['results']]
        except requests.exceptions.RequestException as e:
            inkex.utils.errormsg(str(e))
            return []
    
    def round_elevation(self, elevation):
        return round(elevation)
    
    def get_scale_factor(self):
        svg_root = self.document.getroot()
        # Define the namespace map
        nsmap = {'inkscape': INKSCAPE_NS}

        # Use an XPath expression with the correct namespace to find the scalefactor
        scale_factor_element = svg_root.find('.//inkscape:scalefactor', namespaces=nsmap)

        if scale_factor_element is not None and scale_factor_element.text:
            try:
                # Convert the text to a float and return it
                return float(scale_factor_element.text)
            except ValueError as e:
                inkex.errormsg(f"Error converting scale factor to float: {str(e)}")
                return None
        else:
            inkex.errormsg("Scale factor not found or has no value.")
            return None
            
    def distance_between_points(p1, p2):
        return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)
    
    def find_closest_point(current_point, points):
        closest_point = None
        closest_distance = float('inf')
        for point in points:
            if point is current_point:
                continue  # Skip the current point
            dist = distance_between_points(current_point, point)
            if dist < closest_distance:
                closest_distance = dist
                closest_point = point
        return closest_point, closest_distance

    def create_paths(self, points):
        max_distance = self.options.max_distance  # Define max_distance based on your threshold logic
        paths = []
        while points:
            path = [points.pop(0)]  # Start a new path with the first point
            while True:
                # Find the next closest point
                closest_point, _ = self.find_closest_point(path[-1], points)
                if not closest_point or self.distance_between_points(path[-1], closest_point) > max_distance:
                    break  # If no close enough point is found, break the loop
                path.append(closest_point)  # Add the closest point to the path
                points.remove(closest_point)  # Remove the closest point from the list
            paths.append(path)  # Add the completed path to the list of paths
        return paths
    
    def add_paths_to_svg(svg_root, svg_paths, color):
        for path_data in svg_paths:
            path_element = etree.Element(inkex.addNS('path', 'svg'))
            path_element.set('d', path_data)
            path_element.set('style', f'stroke:{color};fill:none;')
            svg_root.append(path_element)
    
    def calculate_average_distance(self, points):
        total_distance = 0
        count = 0
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            distance = math.sqrt((p2['x'] - p1['x'])**2 + (p2['y'] - p1['y'])**2)
            total_distance += distance
            count += 1
        return total_distance / count if count else 0

    def create_paths_for_group(self, layer, points, threshold_multiplier):
        # Calculate the threshold based on average distance
        average_distance = self.calculate_average_distance(points)
        threshold = threshold_multiplier * average_distance
        
        paths = []
        used_points = set()
        
        for point in points:
            if (point['x'], point['y']) in used_points:
                continue

            path = self.create_path_from_point(points, point, used_points, threshold)
            if path:
                path_element = self.create_path_element(path, "black")
                layer.append(path_element)
                paths.append({'d': path_element.get('d'), 'elevation': path[0]['elevation']})

        
    
    def remove_circles_from_layer(self, layer):
        # Find all circle elements in the layer and remove them
        circles = layer.findall('.//{http://www.w3.org/2000/svg}circle')
        for circle in circles:
            layer.remove(circle)

    def create_path_from_point(self, points, start_point, used_points, threshold):
        path = [start_point]
        used_points.add((start_point['x'], start_point['y']))
        current_point = start_point

        while True:
            next_point = self.find_next_closest_point(current_point, points, used_points)
            if not next_point or self.distance_between_points(current_point, next_point) > threshold:
                break
            path.append(next_point)
            used_points.add((next_point['x'], next_point['y']))
            current_point = next_point

        return path

    def find_next_closest_point(self, current_point, points, used_points):
        closest_point = None
        closest_distance = float('inf')
        for point in points:
            if (point['x'], point['y']) in used_points:
                continue
            distance = self.distance_between_points(point, current_point)
            if distance < closest_distance:
                closest_distance = distance
                closest_point = point
        return closest_point

    def distance_between_points(self, p1, p2):
        return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)

    def create_path_element(self, points, color):
        if not points:
            return None
        
        # Start the path with the first point
        d = f"M {points[0]['x']},{points[0]['y']} "

        # Create the rest of the path using Bezier curves
        for i in range(1, len(points) - 1):
            # Calculate midpoints
            mid_x1 = (points[i-1]['x'] + points[i]['x']) / 2
            mid_y1 = (points[i-1]['y'] + points[i]['y']) / 2
            mid_x2 = (points[i]['x'] + points[i+1]['x']) / 2
            mid_y2 = (points[i]['y'] + points[i+1]['y']) / 2

            # Use the midpoints as control points
            d += f"Q {points[i]['x']},{points[i]['y']} {mid_x2},{mid_y2} "

        # Add the last point with a quadratic Bezier curve to make the end smooth
        d += f"Q {points[-1]['x']},{points[-1]['y']} {points[-1]['x']},{points[-1]['y']}"

        # Create the path element
        path = etree.Element(inkex.addNS('path', 'svg'), {
            'd': d,
            'style': f'stroke:{color};fill:none;stroke-width:1;stroke-linecap:round;stroke-linejoin:round;'
        })
        return path

    def create_parent_layer(self, svg_root, layer_name="elevation"):
        # Check if the parent layer already exists
        parent_layer = self.find_layer(svg_root, layer_name)
        if parent_layer is None:
            # Create the parent layer if it doesn't exist
            parent_layer = etree.SubElement(svg_root, 'g')
            parent_layer.set(inkex.addNS('label', 'inkscape'), layer_name)
            parent_layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return parent_layer

    def create_sublayer(self, parent_layer, label):
        # Create a new sublayer within the parent layer
        sublayer = etree.SubElement(parent_layer, 'g')
        sublayer.set(inkex.addNS('label', 'inkscape'), label)
        sublayer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return sublayer
    
    def consolidate_paths(self, sublayer):
        # Get all path elements
        paths = sublayer.findall('.//{http://www.w3.org/2000/svg}path')
        # Initialize an empty string for the 'd' attribute
        consolidated_d = ""
        # Loop through all paths and concatenate their 'd' attributes
        for path in paths:
            consolidated_d += path.get('d') + " "
            sublayer.remove(path)  # Remove the individual path
        # Create a new path element with the consolidated 'd' attribute
        new_path = etree.SubElement(sublayer, inkex.addNS('path', 'svg'))
        new_path.set('d', consolidated_d.strip())
        new_path.set('style', "stroke:white;fill:none;stroke-width:0.5")  # Set the style as needed
    
if __name__ == '__main__':
    ElevationMapExtension().run()