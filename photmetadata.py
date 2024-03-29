"""Class to handle metadata"""
from datetime import datetime
import subprocess
import requests
import json

# path = '/Users/lawrence/Pictures/Photos/2021/2021_03_AddlestoneWalk'
osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'
google_location_format = 'https://www.google.com/maps/?q=%f,%f'


class PhotoMetadata:
    def __init__(self, filename, timestamp, latitude=0.0, longitude=0.0, elevation=0.0):
        """Add new record. Initially just filename and timestamp
        :type filename: str
        :type timestamp: datetime
        """
#        print('Add %s' % filename)
        self.filename = filename
        self.timestamp_original = timestamp
        self.timestamp_corrected = timestamp
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.point_found = False
        self.location = ''

    def __lt__(self, other):
        """Default sort is by timestamp"""
        return self.timestamp_original < other.timestamp_original

    def get_osm_link(self):
        if self.point_found:
#            return osm_location_format % (self.latitude, self.longitude, self.latitude, self.longitude)
            return google_location_format % (self.latitude, self.longitude)
        else:
            return ''

    def set_gps(self, lat, long, elev):
        """Update GPS data
        :type lat: float
        :type long: float
        :type elev: float
        """
        self.latitude = lat
        self.longitude = long
        self.elevation = elev
        self.point_found = True

    def reset_gps(self):
        """Reset GPS data"""
        self.latitude = 0.0
        self.longitude = 0.0
        self.elevation = 0.0
        self.point_found = False
        self.location = ''

    def csv_output(self):
        """:return string for csv file"""
        if self.point_found:
            osm_link = self.get_osm_link()
            self.location = get_locality(self.latitude, self.longitude)
        else:
            osm_link = 'n/a'
            address = 'not found'
        s = '%s,%s,%s,%f,%f,"%s","%s"' % (self.filename,
                                          self.timestamp_original.strftime('%d:%m:%Y %H:%M:%S'),
                                          self.timestamp_corrected.strftime('%d:%m:%Y %H:%M:%S'),
                                          self.latitude,
                                          self.longitude,
                                          osm_link,
                                          self.location)
#        print(s)
        s += '\n'
        return s


def get_locality(latitude, longitude):
    """Get location details from co-ordinates, using Open Street Map.
    """
    osm_request = "https://nominatim.openstreetmap.org/reverse?lat=%f&lon=%f&zoom=20&format=json"
    result = requests.get(osm_request % (latitude, longitude))

    # Return full address for location ('display_name')
    return result.json()['display_name']


