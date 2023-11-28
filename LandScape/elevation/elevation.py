#!/usr/bin/env python3
import inkex
import requests
import math
from lxml import etree
import logging

# Set up logging to file
logging.basicConfig(filename='C:\\Users\\asafc\\Desktop\\debug.log', level=logging.DEBUG, filemode='w')

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'

def log(message):
    """Helper function to log a message to the debug.log file."""
    logging.debug(message)
    
class ElevationMapExtension(inkex.Effect):
    # Initialize variables for minimum and maximum elevation
    min_elevation = float('inf')
    max_elevation = float('-inf')
    
    def effect(self):
        scale = None

        # Get the SVG root element and extract the width and height of the document
        svg_root = self.document.getroot()
        doc_width = self.svg.unittouu(svg_root.get('width'))
        doc_height = self.svg.unittouu(svg_root.get('height'))

        # Retrieve the custom namespaced geodata element for center coordinates
        geo_data = svg_root.find('svg:metadata/inkscape:geodata', inkex.NSS)
        center_lat = float(geo_data.get('latitude'))
        center_lon = float(geo_data.get('longitude'))
        
        scale = self.get_scale_factor()
        
        # Constants for conversion
        meters_per_degree = 111139  # Average meters per degree of lat/long

        # Calculate number of points and spacing in the grid
        # Calculate number of points and spacing in the grid
        num_points = 200  # Adjust for a different grid size
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
                if fractional_part > 0.1 and fractional_part < 0.9:
                    continue  # Skip this point
        
                rounded_elevation = self.round_elevation(elevation)
                
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

        # Create SVG layers and draw circles and lines
        for rounded_elevation, points in elevation_groups.items():
            # Create a new layer for the elevation
            layer = etree.SubElement(svg_root, 'g')
            layer.set(inkex.addNS('label', 'inkscape'), f'{rounded_elevation}m')
            layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
            
            # Calculate gray level for the current elevation
            if self.max_elevation != self.min_elevation:  # Avoid division by zero
                gray_scale = 10 + 80 * (rounded_elevation - self.min_elevation) / (self.max_elevation - self.min_elevation)
            else:
                gray_scale = 50  # Default to middle gray if all elevations are the same
            gray_color = f"rgb({gray_scale}%,{gray_scale}%,{gray_scale}%)"
            
            # Iterate through the points and draw circles and lines
            last_x, last_y = None, None
            for point in points:
                x, y, lat, lon = point['x'], point['y'], point['latitude'], point['longitude']
                circle = self.draw_circle(layer, x, y, lat, lon, rounded_elevation)  # Pass rounded_elevation here                    

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
                    
if __name__ == '__main__':
    ElevationMapExtension().run()