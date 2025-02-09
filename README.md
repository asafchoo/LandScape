# LandScape
https://www.patreon.com/LandScape_Permaculture

This is an extension pack for Permaculture Design with Inkscape. it is a work in progress. 
It tries to overcome the coplexity of CAD tools, that are far fetched for most Permaculture Designers. It has to be simple top-down approach that will help connetcing the dots of a multi-layered Design as permaculture mostly involve with.

# Why Inkscape?
soon...

# What inside (recent update: 16.12)?
As for now there are four extensions that needs to be processed one after the other (they are numbered in the LandScape submenu at the "Extensions" menu inside inkscape. 

## 1. Primary data
Collects several needed facts about the plot at hand. will be update along the way, including GEO data for retriving stuff from google maps API
<iframe width="1280" height="720" src="https://www.youtube.com/embed/JgF1QUInbz0" title="LandScape: Permaculture Extension for Inkscape - Primary data usage [9.2.25]" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
## 2. Base Map
For now, With out any parameters. it just retreives the google map correct satalite imagery and fix the right document measurments. In the future, will be experimenting with self acquired Arial imagary from drones, as it should be able to use eiter. 

## 3. Scaling 
This extension will calibrate the scale of the document in meters with a known realworld measurment on the plot. For now also tested sucsessfully with measuring with google maps tools and calibrating with that measurment. 

## 4. Elevation
This extention will draw elevation contour lines on the base map. the data is acquired from google elevation maps API service, but it's pretty acurate, as far of the experiments done so far.
Note: 
* The extension will use user input for number of points (squered), will define the basic resolution, while the threshold and distance between pathes are needed to clean the defenition between the contour lines. the user can also define the spacing beteen contour lines, between 1m wich will preduce a contour line every 1m, and 10m thgat will preduce contours every 10m. 
* As for now the process of acquiring the data can take several minutes as it requesting around 40K data points for the plot(!) regardless of the resolution of choice. Eventually it will discard only rounded or close to rounded values so there will be only 10th of the points on the document. but the filteration is done localy so the request can take 3-4 min.

## 5. Site Boundaries
The Site Boundaries uses a polygon that the designer is marking on the basemap to:
1. calculate the site area in square meters and print it on the document
2. fadeout everything that is not within the site. 

# compatability
tested on:
1. inkscape 1.3 on windows 11
2. inkscape 1.3.2 on windows 10

# Project updates:
1.1.25:
1. Aggregated data of precipitation from open-meteo.com and calculating last 20 years avarage (at Primary data)
2. Refined the process of polygon area calculation 

24.12.24 (after a long stall): 
1. Layer nameing in basemap extention
2. Layer nameing and optimizing object creation on scale extention

**15.12.23: added functionality - Site Boundaries**

10.12.23: inx's file update.

29.11.23: first code upload.

## TODO:
**Precipitation** - a tool that will take a predefined polygon, will move it to a new layer (if it's not already on that layer), take the yearly Precipitation data, and calculate the Precipitation that will fall yearly on that polygon 
