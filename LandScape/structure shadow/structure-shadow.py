#!/usr/bin/env python3
import inkex
from lxml import etree
import math
import datetime
import urllib.request, json, ssl

class StructureShadow(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--heightofstructure", type=float, default=0,
                          help="Height of the structure (in meters).")
        # We no longer use the date/time parameters from the UI,
        # because the extension will compute seasonal shadows automatically.
    
    def effect(self):
        # Retrieve structure height
        structure_height = self.options.heightofstructure
        if structure_height <= 0:
            inkex.errormsg("Invalid height. Please enter a positive numeric value.")
            return

        # Get the selected polygon (the original structure)
        polygon = next(iter(self.svg.selected.values()), None)
        if polygon is None or polygon.tag != inkex.addNS('path', 'svg'):
            inkex.errormsg("Please select a valid closed polygon.")
            return

        # Get location and scale factor from metadata
        latitude = self.get_latitude()
        if latitude is None:
            inkex.errormsg("Latitude not found in metadata.")
            return
        longitude = self.get_longitude()
        if longitude is None:
            inkex.errormsg("Longitude not found in metadata.")
            return
        scale_factor = self.get_scale_factor()
        if scale_factor is None:
            inkex.errormsg("Scale factor not found in metadata.")
            return

        # Use current year to build seasonal dates.
        current_year = datetime.date.today().year

        # For locations in the Northern Hemisphere, use:
        #   winter: December 21; summer: June 21.
        # For the Southern Hemisphere, swap these.
        if latitude >= 0:
            winter_date = f"{current_year}-12-21"
            summer_date = f"{current_year}-06-21"
            winter_times = ["08:30", "12:00", "15:00"]
            summer_times = ["07:00", "12:00", "18:00"]
        else:
            winter_date = f"{current_year}-06-21"
            summer_date = f"{current_year}-12-21"
            winter_times = ["08:30", "12:00", "15:00"]
            summer_times = ["07:00", "12:00", "18:00"]

        # Create separate layers for winter and summer shadows.
        parent_layer = self.get_parent_layer(polygon)
        winter_layer = self.create_shadow_layer(parent_layer, "Winter Shadow")
        summer_layer = self.create_shadow_layer(parent_layer, "Summer Shadow")

        # Process each time for the winter shadows.
        for t in winter_times:
            dt_str = f"{winter_date} {t}"
            # Compute shadow using our new compute_shadow (which auto-gets the UTC offset)
            shadow_length, sun_azimuth, shadow_datetime = self.compute_shadow(latitude, structure_height, longitude, dt_str)
            if shadow_datetime is None:
                continue
            shadow_offset = shadow_length * scale_factor
            orig_shadow, off_shadow = self.create_shadow_polygons(polygon, winter_layer, shadow_offset, sun_azimuth)
            self.extrude_between_shadows(winter_layer, orig_shadow, off_shadow, shadow_datetime)
            inkex.utils.debug(f"Winter shadow at {self.get_shadow_time(shadow_datetime)}: length = {shadow_length}, azimuth = {sun_azimuth}")

        # Process each time for the summer shadows.
        for t in summer_times:
            dt_str = f"{summer_date} {t}"
            shadow_length, sun_azimuth, shadow_datetime = self.compute_shadow(latitude, structure_height, longitude, dt_str)
            if shadow_datetime is None:
                continue
            shadow_offset = shadow_length * scale_factor
            orig_shadow, off_shadow = self.create_shadow_polygons(polygon, summer_layer, shadow_offset, sun_azimuth)
            self.extrude_between_shadows(summer_layer, orig_shadow, off_shadow, shadow_datetime)
            inkex.utils.debug(f"Summer shadow at {self.get_shadow_time(shadow_datetime)}: length = {shadow_length}, azimuth = {sun_azimuth}")

        # --- Remove any empty "Combined Shadow" groups from the shadow layers ---
        self.remove_empty_combined_layers(winter_layer)
        self.remove_empty_combined_layers(summer_layer)

        inkex.utils.debug("Shadow processing completed. The original structure remains unchanged.")

    def get_google_utc_offset(self, lat, lon, date_str):
        """
        Use the Google Time Zone API to get the UTC offset (in hours) for the given location and date.
        date_str is in the format "YYYY-MM-DD".
        """
        # Use noon (12:00) on the given date for the timestamp.
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        dt = dt.replace(hour=12, minute=0, second=0)
        timestamp = int(dt.timestamp())
        api_key = "AIzaSyDAblLSzOE_u7wS2OiPrQgsu_z4cdcIBU0"
        url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lon}&timestamp={timestamp}&key={api_key}"
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen(url, context=context)
        data = json.load(response)
        if data["status"] != "OK":
            raise Exception("Google Time Zone API error: " + data.get("errorMessage", data["status"]))
        total_offset = data["rawOffset"] + data["dstOffset"]
        offset_hours = total_offset / 3600.0
        inkex.utils.debug(f"Google API: offset for {lat},{lon} on {date_str} is {offset_hours} hours")
        return offset_hours

    def compute_shadow(self, latitude, height, longitude, date_time_str):
        """
        Compute the solar geometry (shadow length and sun azimuth) for a given
        date and time (as a string "YYYY-MM-DD HH:MM").
        Returns (shadow_length, sun_azimuth, shadow_datetime).
        """
        try:
            shadow_datetime = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            inkex.errormsg("Invalid date/time format in compute_shadow.")
            return 0, 0, None

        # Get the local UTC offset automatically using Google Time Zone API.
        local_utc_offset = self.get_google_utc_offset(latitude, longitude, date_time_str.split()[0])
        # Make the shadow_datetime offset-aware.
        tz_local = datetime.timezone(datetime.timedelta(hours=local_utc_offset))
        shadow_datetime = shadow_datetime.replace(tzinfo=tz_local)

        n = shadow_datetime.timetuple().tm_yday
        decl_deg = 23.45 * math.sin(math.radians(360 * (284 + n) / 365))
        decl = math.radians(decl_deg)

        # --- Solar Time Correction via Sunrise-Sunset API ---
        def get_solar_noon_local(lat, lon, date_str, local_utc_offset):
            url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={date_str}&formatted=0"
            context = ssl._create_unverified_context()
            response = urllib.request.urlopen(url, context=context)
            data = json.load(response)
            if data['status'] != 'OK':
                raise Exception("API error: " + data.get('status', 'Unknown error'))
            solar_noon_utc = datetime.datetime.fromisoformat(data['results']['solar_noon'])
            solar_noon_local = solar_noon_utc + datetime.timedelta(hours=local_utc_offset)
            tz_local = datetime.timezone(datetime.timedelta(hours=local_utc_offset))
            solar_noon_local = solar_noon_local.replace(tzinfo=tz_local)
            return solar_noon_local

        solar_noon_local = get_solar_noon_local(latitude, longitude, date_time_str.split()[0], local_utc_offset)
        noon = shadow_datetime.replace(hour=12, minute=0, second=0, microsecond=0)
        offset_timedelta = noon - solar_noon_local
        offset_hours = offset_timedelta.total_seconds() / 3600.0

        solar_time = (shadow_datetime.hour + shadow_datetime.minute / 60.0) + offset_hours
        hour_angle_deg = 15 * (solar_time - 12)
        hour_angle = math.radians(hour_angle_deg)
        lat_rad = math.radians(latitude)
        sun_alt_rad = math.asin(
            math.sin(lat_rad) * math.sin(decl) +
            math.cos(lat_rad) * math.cos(decl) * math.cos(hour_angle)
        )
        tan_alt = math.tan(sun_alt_rad)
        if abs(tan_alt) < 1e-6:
            tan_alt = 1e-6
        shadow_length = height / tan_alt

        cos_az = (math.sin(decl) - math.sin(lat_rad) * math.sin(sun_alt_rad)) / (math.cos(lat_rad) * math.cos(sun_alt_rad))
        cos_az = max(min(cos_az, 1), -1)
        az_rad = math.acos(cos_az)
        if hour_angle > 0:
            az_rad = 2 * math.pi - az_rad
        sun_azimuth = math.degrees(az_rad)

        inkex.utils.debug(f"Computed {date_time_str}: sun altitude = {math.degrees(sun_alt_rad):.2f}°, HA = {hour_angle_deg:.2f}°")
        return shadow_length, sun_azimuth, shadow_datetime

    def get_shadow_time(self, shadow_datetime):
        return shadow_datetime.strftime("%H:%M")

    def compute_convex_hull(self, points):
        points = sorted(points)
        lower = []
        for p in points:
            while len(lower) >= 2 and self.cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and self.cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        return lower[:-1] + upper[:-1]

    def cross(self, o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    def create_shadow_polygons(self, polygon, shadow_layer, shadow_offset, azimuth_angle):
        # Create copies of the structure polygon for shadow calculation.
        # These copies will be removed after combining.
        original_shadow = polygon.copy()
        original_shadow.set("id", f"copy_shadow_original_{id(original_shadow)}")
        shadow_layer.append(original_shadow)

        shadow_direction = (azimuth_angle + 180) % 360
        azimuth_rad = math.radians(shadow_direction)
        dx = shadow_offset * math.sin(azimuth_rad)
        dy = -shadow_offset * math.cos(azimuth_rad)

        offset_shadow = polygon.copy()
        offset_shadow.set("id", f"copy_shadow_offset_{id(offset_shadow)}")
        offset_shadow.set("transform", f"translate({dx},{dy})")
        shadow_layer.append(offset_shadow)

        return original_shadow, offset_shadow

    def extrude_between_shadows(self, shadow_layer, original_shadow, offset_shadow, shadow_datetime):
        # Create a combined shadow (convex hull) from the original and offset shadow nodes.
        combined_layer = etree.SubElement(shadow_layer, inkex.addNS('g', 'svg'))
        combined_layer.set(inkex.addNS('label', 'inkscape'), 'Combined Shadow')
        combined_layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        original_nodes = [seg[1] for seg in original_shadow.path.to_superpath()[0]]
        offset_transform = offset_shadow.get("transform")
        dx, dy = 0, 0
        if offset_transform and "translate" in offset_transform:
            translate_values = offset_transform.replace("translate(", "").replace(")", "").split(",")
            dx, dy = float(translate_values[0]), float(translate_values[1])
        offset_nodes = [[seg[1][0] + dx, seg[1][1] + dy] for seg in offset_shadow.path.to_superpath()[0]]
        all_nodes = original_nodes + offset_nodes
        hull = self.compute_convex_hull(all_nodes)
        path_data = "M " + " L ".join([f"{p[0]},{p[1]}" for p in hull]) + " Z"

        shadow_path = inkex.PathElement()
        shadow_path.set("d", path_data)
        shadow_path.style = inkex.Style({"fill": "black", "stroke": "none", "fill-opacity": "0.5"})
        shadow_time = self.get_shadow_time(shadow_datetime)
        shadow_path.set(inkex.addNS('label', 'inkscape'), shadow_time)
        shadow_layer.append(shadow_path)
        inkex.utils.debug(f"Shadow successfully created for {shadow_time}.")

        # Remove the shadow copies so only the final shadow remains.
        if original_shadow.getparent() is not None:
            original_shadow.getparent().remove(original_shadow)
        if offset_shadow.getparent() is not None:
            offset_shadow.getparent().remove(offset_shadow)

    def remove_empty_combined_layers(self, shadow_layer):
        """
        Remove every direct child of the provided shadow_layer whose label is "Combined Shadow".
        """
        for child in list(shadow_layer):
            if child.tag == inkex.addNS('g', 'svg'):
                label = child.get(inkex.addNS('label', 'inkscape'))
                if label == "Combined Shadow":
                    shadow_layer.remove(child)

    def get_parent_layer(self, element):
        parent = element.getparent()
        while parent is not None and parent.tag != inkex.addNS('g', 'svg'):
            parent = parent.getparent()
        return parent

    def create_shadow_layer(self, parent_layer, name):
        shadow_layer = etree.Element(inkex.addNS('g', 'svg'))
        shadow_layer.set(inkex.addNS('label', 'inkscape'), name)
        shadow_layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        parent_layer.insert(0, shadow_layer)
        return shadow_layer

    def get_latitude(self):
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
        svg_root = self.document.getroot()
        scale_factor_element = svg_root.find('.//inkscape:scalefactor',
                                             namespaces={'inkscape': 'http://www.inkscape.org/namespaces/inkscape'})
        if scale_factor_element is not None and scale_factor_element.text:
            try:
                return float(scale_factor_element.text)
            except ValueError:
                return None
        return None

    def get_longitude(self):
        svg_root = self.document.getroot()
        metadata = svg_root.find('svg:metadata', inkex.NSS)
        if metadata is not None:
            geo_data = metadata.find('inkscape:geodata', inkex.NSS)
            if geo_data is not None:
                longitude = geo_data.get('longitude')
                if longitude:
                    return float(longitude)
        return None

if __name__ == '__main__':
    StructureShadow().run()
