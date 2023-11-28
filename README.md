# LandScape
https://www.patreon.com/LandScape_Permaculture

This is an extension pack for Permaculture Design with Inkscape. it is a work in progress. 
It tries to overcome the coplexity of CAD tools, that are far fetched for most Permaculture Designers. It has to be simple top-down approach that will help connetcing the dots of a multi-layered Design as permaculture mostly involve with.

# Why Inkscape?
soon...

# What inside (recent update: 29.11)?
As for now there are four extensions that needs to be processed one after the other (they are numbered in the LandScape submenu at the "Extensions" menu inside inkscape. 

## 1. Primary data
Collects several needed facts about the plot at hand. will be update along the way, including GEO data for retriving stuff from google maps API

## 2. Base Map
For now, With out any parameters. it just retreives the google map correct satalite imagery and fix the right document measurments. In the future, will be experimenting with self acquired Arial imagary from drones, as it should be able to use eiter. 

## 3. Scaling 
This extension will calibrate the scale of the document in meters with a known realworld measurment on the plot. For now also tested sucsessfully with measuring with google maps tools and calibrating with that measurment. 

## 4. Elevation
This extention will draw elevation contour lines on the base map. the data is acquired from google elevation maps API service, but it's pretty acurate, as far of the experiments done so far.
Note: 
* still not contour lines but instead contour points that can interperted as lines (TODO)
* As for now the process of acquiring the data can take several minutes as it requesting around 40K data points for the plot(!) regardless of the resolution of choice. Eventually it will discard only rounded or close to rounded values so there will be only 10th of the points on the document. but the filteration is done localy so the request can take 3-4 min.

# compatability
tested on:
1. inkscape 1.3 on windows 11.

# Project updates:
**29.11: first code upload.**

