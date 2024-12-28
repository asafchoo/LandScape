import inkex
import requests
from lxml import etree
from datetime import datetime

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

            try:
                average_rainfall = self.calculate_annual_rainfall_average(lat, lon)
                self.save_to_metadata(average_rainfall)
                inkex.utils.debug(f"The 20-year annual rainfall average is: {average_rainfall:.2f} mm")
            except Exception as e:
                inkex.errormsg(f"Error calculating average rainfall: {str(e)}")

        else:
            inkex.errormsg("Latitude or Longitude not provided.")

        if self.options.open_url:
            import webbrowser
            webbrowser.open("http://www.example.com")

    def calculate_annual_rainfall_average(self, lat, lon):
        start_year = datetime.now().year - 20
        end_year = datetime.now().year

        total_rainfall = 0
        years_counted = 0

        for year in range(start_year, end_year):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
                   f"&start_date={start_date}&end_date={end_date}&daily=precipitation_sum&timezone=GMT")
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                daily_precipitation = data.get("daily", {}).get("precipitation_sum", [])
                total_rainfall += sum(daily_precipitation)
                years_counted += 1
            else:
                inkex.errormsg(f"Failed to fetch data for {year}: HTTP {response.status_code}")

        if years_counted == 0:
            raise ValueError("No data retrieved for the last 20 years.")

        return total_rainfall / years_counted

    def save_to_metadata(self, average_rainfall):
        svg_root = self.document.getroot()
        metadata = svg_root.find("metadata")

        if metadata is None:
            metadata = etree.SubElement(svg_root, "metadata")

        inkscape_ns = 'http://www.inkscape.org/namespaces/inkscape'
        geo_data = etree.Element(f'{{{inkscape_ns}}}geodata')
        geo_data.set("annual_rainfall_avg", str(average_rainfall))
        metadata.append(geo_data)

if __name__ == "__main__":
    PrimaryData().run()