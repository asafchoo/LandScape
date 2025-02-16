# LandScape
https://www.patreon.com/LandScape_Permaculture

This is an extension pack for Permaculture Design with Inkscape. it is a work in progress. 
It tries to overcome the coplexity of CAD tools, that are far fetched for most Permaculture Designers. It has to be simple top-down approach that will help connetcing the dots of a multi-layered Design as permaculture mostly involve with.

# Why Inkscape?
Along the years i found that most of the softwares dedicated for landscape or architectual design couldn't grasp the wide system oriented prespective of permaculture. from the other hand, a lot of the permaculture parctitioners does not have the time or ability to learn the existing available software that for general has a steep learning curve, or to pay hundreds or thousands of dollars to legally register those softwares. 
I started to look for an alternative ten years ago, and after a long round, l came back to InkScape - the best open source vector drawing software there is. I figured that a good software will balance flexability, ease of use and complexity, and tought it is best to start with a good platform that has the feel of... a drawing software. One of the most favorable tools in inksacpe for our matter is the option to use user written extention that adds layers of functions. And here we are...

# What inside (recent update: 9/2/25)?
An Inkscape extension called "LandScape", composed of 7 semi-extensions and an icon library. 

## 1. Primary data
Collects several needed pieces of information about the plot at hand, and creates the base map layers.

takes:
   * size of actual physical map (when you'll maybe want to print it at the end)
   * geo location (latitude and longtitude) and centers the map around that point (get it from google maps or oter GPS tool)
   * zoom level (in correlation of how google maps are using it)
   * precipitation annual avrage (if field is empty. it will take it from a global open api service but that's not very accurate, so...)

do:
  * place google map imagery according to the GPS and zoom level)
  * create a set of layers and sub-layers in a permaculture structure logic

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/JgF1QUInbz0/0.jpg)](https://www.youtube.com/watch?v=JgF1QUInbz0)

## 2. Scaling 
Clibrate the map to workable scale (in meters ,for now) that will be usfull with all the extensions that will need to use field masurments, like calculating areas or distances. 

takes:
   * A path (line in inkscape) bwtween two points on the actuall map
   * the actuall distance between those two points (either measured by hand, or from google maps or other digital service)

do:
  * Calibrate the map to actuall scale in SI units system
  * Creates a visible scale on the upper border of the document, from west to east.
  * Deletes the path that was created only for the scale 

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/8ZMC5a2uESA/0.jpg)](https://www.youtube.com/watch?v=8ZMC5a2uESA)

## 3. Elevation
A neat tool for creating contour lines on top of the map project. 

takes:
   * Number of points to use in each axis of the matrix of points
   * Vertical distance between contour line in meters
   * Threshold & distance between paths - parameters for twick if plotting of contours needs to improve

do:
  * Creates a contour line grid with the parameter chosen within the layer "Base Map" > "Calculated Elevation Map"

Note: 
* The amount of data aquired is large so this process can halt inkscape for several minutes, usually between 2-4, so please be patient.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/nrjLl_p6_V8/0.jpg)](https://www.youtube.com/watch?v=nrjLl_p6_V8)

## 4. Site Boundaries
The Site Boundaries tool masures the sites plot size and focus on it.

takes:
  * a path polygon drawn all around the plot, as accuratly as possible.

do:
  * calculate the size of the plot
  * creates a opac layer that help to focus on the design plot without trimming neighboring plots that might be needed in the future.
  * prints the size of the plot on the left corner of the site boundaries layer 

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/VFBRRd1N17w/0.jpg)](https://www.youtube.com/watch?v=VFBRRd1N17w)

## 5. Precipitation Calculator
Estimate the amount of annual rainfall for a given area.

takes:
  * A drawn polygon under the "Precipitation" layer
  * location data
  * annual rainfall data
  * scale

do:
  * change the name of the polygon object to the annual rainfall that this polygon can aproximatly harvest.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/GyxEYZd6Skw/0.jpg)](https://www.youtube.com/watch?v=GyxEYZd6Skw)

## 6. Structure information & Shadow casting
Generate specific information and shadow casting of a specific structure on site.

takes:
  * A polygon that represent a structure on site.
  * Height of structure
  * Location data and scale calibration

Do:
  * calculate surface of structure
  * Calculate roof rain catchment area and volume.
  * Cast shadow of structure on winter & summer solistice on morning, noon & evening.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/kBJmJJ0zg4I/0.jpg)](https://www.youtube.com/watch?v=kBJmJJ0zg4I)

# Compatability
tested on:
1. inkscape 1.3 & Inkscape 1.4 (86a8ad7, 2024-10-11) on windows 11
2. inkscape 1.3.2 on windows 10
