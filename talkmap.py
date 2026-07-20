# Leaflet cluster map of talk locations
#
# Run this from the repository root (the folder containing _talks/). It scrapes
# the title, location, and date from each talk's Markdown front matter,
# geolocates the city with geopy/Nominatim, and writes talkmap/org-locations.js,
# which talkmap/map.html reads. Functionally the same as talkmap.ipynb.
import frontmatter
import glob
import json
import time
from datetime import date, datetime
from geopy import Nominatim
from geopy.exc import GeocoderTimedOut

# Set the default timeout, in seconds
TIMEOUT = 5

# Collect the Markdown files
g = sorted(glob.glob("_talks/*.md"))

# Prepare to geolocate.
# address_points is a LIST, so two talks in the same location each get their
# own marker -- nothing overrides anything.
geocoder = Nominatim(user_agent="academicpages.github.io")
address_points = []

# Perform geolocation
for file in g:
    data = frontmatter.load(file).to_dict()

    # Skip talks with no location
    if 'location' not in data:
        continue

    title = str(data['title']).strip()
    location = str(data['location']).strip()

    # Format the date as e.g. "13 December 2024"
    raw_date = data.get('date', '')
    if isinstance(raw_date, (date, datetime)):
        talk_date = raw_date.strftime('%d %B %Y')
    else:
        talk_date = str(raw_date).strip()

    # Marker popup text: title, location (city & country), date
    label = f"{title}<br />{location}<br />{talk_date}"

    # Geocode and append ONE entry per talk
    try:
        geo = geocoder.geocode(location, timeout=TIMEOUT)
        if geo is None:
            print(f"Warning: no geocode result for {location!r}")
            continue
        address_points.append([label, geo.latitude, geo.longitude])
        print(label.replace("<br />", " | "), "->", geo.latitude, geo.longitude)
        time.sleep(1)  # respect Nominatim's ~1 request/second policy
    except GeocoderTimedOut as ex:
        print(f"Error: geocode timed out on {location!r}: {ex}")
    except ValueError as ex:
        print(f"Error: geocode failed on {location!r}: {ex}")
    except Exception as ex:
        print(f"Unhandled error on {location!r}: {ex}")

# Write the data file that talkmap/map.html reads
with open("talkmap/org-locations.js", "w") as f:
    f.write("var addressPoints = ")
    json.dump(address_points, f, indent=2)
    f.write(";")

print(f"Wrote {len(address_points)} markers to talkmap/org-locations.js")
