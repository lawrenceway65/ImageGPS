"""Class to handle metadata"""
from datetime import datetime
import subprocess
import json

# path = '/Users/lawrence/Pictures/Photos/2021/2021_03_AddlestoneWalk'
osm_location_format = 'https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=18/%f/%f'


class PhotoMetadata:
    def __init__(self, filename, timestamp, latitude=0.0, longitude=0.0, elevation=0.0):
        """Add new record. Initially just filename and timestamp
        :type filename: str
        :type timestamp: datetime
        """
#        print('Add %s' % filename)
        self.filename = filename
        self.timestamp = timestamp
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation

    def __lt__(self, other):
        """Default sort is by timestamp"""
        return self.timestamp < other.timestamp

    def set_gps(self, lat, long, elev):
        """Update GPS data
        :type lat: float
        :type long: float
        :type elev: float
        """
        self.latitude = lat
        self.longitude = long
        self.elevation = elev

    def csv_output(self):
        """:return string for csv file"""
        osm_link = osm_location_format % (self.latitude, self.longitude, self.latitude, self.longitude)
        s = '%s,%s,%f,%f,"%s","%s"' % (self.filename,
                                       self.timestamp.strftime('%d:%m:%Y %H:%M:%S'),
                                       self.latitude,
                                       self.longitude,
                                       osm_link,
                                       get_locality(self.latitude, self.longitude))
        print(s)
        s += '\n'
        return s


def get_locality(latitude, longitude):
    """Get location details from co-ordinates, using Open Street Map.
    """
    osm_request = "https://nominatim.openstreetmap.org/reverse?lat=%f&lon=%f&zoom=20&format=json"
    result = subprocess.check_output(['curl', '-s', osm_request % (latitude, longitude)]).decode("utf-8")
    result_json = json.loads(result)

    # Return full address for location ('display_name')
    return result_json['display_name']


