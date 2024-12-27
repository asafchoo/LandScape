#!/usr/bin/env python3
import inkex
from lxml import etree
import webbrowser

class PrimaryData(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--latitude", type=str, help="Latitude")
        pars.add_argument("--longitude", type=str, help="Longitude")
        pars.add_argument("--widthofdoc", type=str, help="width of document")
        pars.add_argument("--heightofdoc", type=str, help="height of document")
        pars.add_argument("--zoomlevel", type=str, help="zoom level")
        pars.add_argument("--Precipitation", type=str, help="Precipitation")
        pars.add_argument("--open_url", type=inkex.Boolean, help="Open Website")

    def effect(self):
         # Retrieve the input values
        lat = self.options.latitude
        lon = self.options.longitude
        widthofdoc = self.options.widthofdoc
        heightofdoc = self.options.heightofdoc
        zoom = self.options.zoomlevel


        if lat and lon:
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
                # If there is no namedview element, create one and set the units
                # If there is no namedview element, create one and set the units
                # If there is no namedview element, create one and set the units
                namedview = etree.SubElement(svg_root, 'sodipodi:namedview', nsmap=inkex.NSS)
                namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

            # Find or create the metadata element
            metadata = svg_root.find('metadata')
            if metadata is None:
                metadata = etree.SubElement(svg_root, 'metadata')

            # Define the Inkscape namespace
            inkscape_ns = 'http://www.inkscape.org/namespaces/inkscape'

            # Create a new element for our custom data
            geo_data = etree.Element('{%s}geodata' % inkscape_ns)
            geo_data.set('latitude', lat)
            geo_data.set('longitude', lon)
            geo_data.set('zoomlevel', zoom)
            geo_data.set('Precipitation', zoom)
            metadata.append(geo_data)

            # Output a message
            inkex.utils.debug(f"Metadata set: Latitude: {lat}, Longitude: {lon}, Zoom level: {zoom}")
        else:
            inkex.errormsg("Latitude or Longitude not provided.")
        
        if self.options.open_url:
            webbrowser.open("http://www.example.com")

if __name__ == '__main__':
    PrimaryData().run()