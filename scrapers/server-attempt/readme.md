# Direct-to-Server Attempt

## Overview

After playing around with inspect element and view page source on the ICAO Carbon Calculator [site](https://www.icao.int/environmental-protection/CarbonOffset/Pages/default.aspx), we found the method "computeByInput" in the javascript source code, which apparently sends the airport codes and other user-entered information to an ICAO database or server to compute the emissions from the flight and display them on the page. We attempted to access this database or servr directly by sending POST requests with curl, rather than having to work around the buttons on the site.

## Organization

This directory contains JSON files for each of 3 POST requests made to the server, as well as the scripts used to send them with curl from a terminal. The file 'request1.txt' shows in more detail which fields were sent, where, and what we think they mean for the calculator.

The html for the error message returned on request 2 is also in this directory. Also included is the html for the website.

## Results

Unfortunately, the server returned only latitude and longitude coordinates for the airport codes on both requests 1 and 3, and an error message on request 2.