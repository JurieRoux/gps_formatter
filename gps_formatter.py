from gps_coordinates import GpsCoordinates

class GpsFormatter:
    @staticmethod
    def build_coordinates(latitude, longitude):
        gps_coordinates = GpsCoordinates(0, 0)

        gps_coordinates.latitude = GpsFormatter.format_coordinate(latitude)
        gps_coordinates.longitude = GpsFormatter.format_coordinate(longitude)

        return gps_coordinates

    @staticmethod
    def format_coordinate(coordinate):
        if len(coordinate) == 5:
            return float(coordinate)
        elif len(coordinate) == 4:
            return float(coordinate + "0")
        elif len(coordinate) == 3:
            return float(coordinate + "00")
        elif len(coordinate) == 2:
            return float(coordinate + "000")
        else:
            return float(coordinate.ljust(5, '0'))
