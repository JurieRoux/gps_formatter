from geopy.geocoders import Nominatim

class ReverseGeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="gps_formatter")

    def get_address(self, coordinates):
        location = self.geolocator.reverse((coordinates.latitude, coordinates.longitude), exactly_one=True)
        return location.address if location else "Address not found"
