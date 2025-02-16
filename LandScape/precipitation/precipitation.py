import inkex
from lxml import etree

class PrecipitationExtension(inkex.EffectExtension):
    def effect(self):
        # Get the "precipitation" layer
        precipitation_layer = self.find_layer("Precipitation")
        if precipitation_layer is None:
            inkex.errormsg("No 'Precipitation' layer found in the document.")
            return

        # Retrieve precipitation value (mm/year) from metadata
        geo_data = self.document.getroot().find('svg:metadata/inkscape:geodata', inkex.NSS)
        if geo_data is None or 'annual_rainfall_avg' not in geo_data.attrib:
            inkex.errormsg("Precipitation value not found in metadata.")
            return

        try:
            precipitation_mm = float(geo_data.get('annual_rainfall_avg'))
        except ValueError:
            inkex.errormsg("Invalid precipitation value in metadata.")
            return

        # Get scale factor from document metadata
        scale_factor = self.get_scale_factor()
        if scale_factor is None:
            return

        for obj in precipitation_layer.iterchildren():
            if obj.tag == inkex.addNS('path', 'svg') and self.is_closed_path(obj):
                area_m2 = self.calculate_area(obj.path.to_superpath(), scale_factor)
                if area_m2 is None:
                    continue
                
                # Calculate precipitation volume (m^3)
                volume_m3 = area_m2 * (precipitation_mm / 1000)  # Convert mm to meters
                # Rename the polygon with the calculated precipitation volume and area
                inkex.utils.debug(f"The annual precipitation [{precipitation_mm:.2f}mm] within the chosen polygon of [{area_m2:.2f}m²] is: {volume_m3:.2f} m³/year")
                obj.set(inkex.addNS('label', 'inkscape'), f"{volume_m3:.2f} m³/year [{area_m2:.2f}m²]")
        
    def find_layer(self, label):
        """Find a layer by its label."""
        layers = self.document.getroot().xpath(
            f"//svg:g[@inkscape:label='{label}']", namespaces=inkex.NSS
        )
        return layers[0] if layers else None

    def get_scale_factor(self):
        """Retrieve scale factor from metadata."""
        scale_factor_element = self.document.getroot().xpath('//inkscape:scalefactor', namespaces=inkex.NSS)
        if scale_factor_element:
            try:
                return float(scale_factor_element[0].text)
            except ValueError:
                inkex.errormsg("Invalid scale factor value in metadata.")
        else:
            inkex.errormsg("Scale factor not found in metadata.")
        return None

    def is_closed_path(self, obj):
        """Check if a path is closed."""
        d = obj.get('d', '').strip().upper()
        return d.endswith('Z')

    def calculate_area(self, polygon, scale_factor):
        """Calculate the area of a polygon in square meters."""
        total_area = 0
        for subpath in polygon:
            if len(subpath) < 3:
                continue

            x = [pt[1][0] for pt in subpath]
            y = [pt[1][1] for pt in subpath]

            area = 0.5 * abs(
                sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(-1, len(x) - 1))
            )
            total_area += area

        return total_area / (scale_factor ** 2)

if __name__ == '__main__':
    PrecipitationExtension().run()
