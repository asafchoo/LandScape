#!/usr/bin/env python3
import inkex
from lxml import etree
import requests
import base64
import os
import tempfile
import math

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'

api_key ="AIzaSyDAblLSzOE_u7wS2OiPrQgsu_z4cdcIBU0"
url = "https://maps.googleapis.com/maps/api/staticmap?"

class BaseMap(inkex.EffectExtension):
    def effect(self):
        # Get the SVG root element
        svg_root = self.document.getroot()

        # Retrieve the custom namespaced geodata element
        geo_data = svg_root.find('svg:metadata/inkscape:geodata', inkex.NSS)
       
        # Extract the width and height of the document
        doc_width = self.svg.unittouu(svg_root.get('width'))
        doc_height = self.svg.unittouu(svg_root.get('height'))
        
         # Find or create the "Base Map" layer
        layer = self.find_layer("Base Map")
        if layer is not None:
            inkex.errormsg(f"Layer 'Base Map' already created before, there should be only one.")
            return
            
        if geo_data is not None:
            # Extract the latitude and longitude
            lat = geo_data.get('latitude')
            lon = geo_data.get('longitude')
            zoom = geo_data.get('zoomlevel')

            if lat and lon:
                self.add_text(svg_root, f"Latitude: {lat}", 100, 100) 
                self.add_text(svg_root, f"Longitude: {lon}", 100, 120)
                response = requests.get(url +"center="+lat+","+lon+"&zoom="+zoom+"&size=2048x2048&scale=2&maptype=hybrid&key=AIzaSyDAblLSzOE_u7wS2OiPrQgsu_z4cdcIBU0")
                if response.status_code == 200:
                    # Create a new layer called "Base Map"
                    layer = self.create_layer(svg_root, "Base Map")

                    # Save the image to a temporary file
                    temp = tempfile.NamedTemporaryFile(delete=False)
                    temp.write(response.content)
                    temp.close()
                
                    # Embed the image into the SVG
                    href = self.embed_image(temp.name)

                    # Create an image element in the SVG
                    image = inkex.Image(href=href)
                    image.set('x', '0')
                    image.set('y', '0')
                    image.set('width', str(doc_width))
                    image.set('height', str(doc_height))
                    layer.append(image)

                    # Delete the temporary file
                    os.unlink(temp.name)
                    
                else:
                    inkex.errormsg(f"Failed to retrieve the map image. Status Code: {response.status_code}")
                
            else:
                inkex.errormsg("Latitude or Longitude metadata not found.")
        else:
            inkex.errormsg("No metadata found in the SVG file.")
   
    def add_text(self, parent, text, x=100, y=100, size=20):
        # Create a new text element
        text_elem = inkex.TextElement.new(text)
        text_elem.set('x', str(x))
        text_elem.set('y', str(y))
        text_elem.style = str(inkex.Style({
            'font-size': str(size),
            'font-family': 'sans-serif',
            'text-anchor': 'start',
            'alignment-baseline': 'middle'
        }))

        # Add the text element to the parent
        parent.append(text_elem)
     
    def create_layer(self, parent, layer_name):
        # Check if layer already exists
        for layer in parent.findall(inkex.addNS('g', 'svg')):
            label = layer.find(inkex.addNS('label', 'inkscape'))
            if label is not None and label.text == layer_name:
                return layer  # Return the existing layer

        # Create a new layer
        new_layer = inkex.Layer.new(layer_name)
        parent.append(new_layer)
        return new_layer
    
    def find_layer(self, layer_name):
        svg_root = self.document.getroot()
        # Define the namespace map for the XPath search
        nsmap = {'svg': 'http://www.w3.org/2000/svg', 'inkscape': INKSCAPE_NS}

        # Use an XPath expression with the correct namespace to find all g elements with the specified label
        layer = svg_root.xpath(f"//svg:g[@inkscape:label='{layer_name}']", namespaces=nsmap)
    
        # The xpath method returns a list of found elements. We return the first one, or None if the list is empty.
        return layer[0] if layer else None
        
    def embed_image(self, file_path):
        # Read image data and convert to base64
        with open(file_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        # Create a data URI for the image
        href = 'data:image/png;base64,' + image_data
        return href
        
if __name__ == '__main__':
    BaseMap().run()