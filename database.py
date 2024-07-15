import sqlite3
from geopy.distance import geodesic

class Database:
    def __init__(self):
        self.connection = sqlite3.connect(':memory:')
        self.cursor = self.connection.cursor()
        self.create_table()
        self.seed_data()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE locations (
                latitude REAL,
                longitude REAL,
                address TEXT
            )
        ''')

    def seed_data(self):
        data = [
            (40.712776, -74.005974, 'New York, NY, USA'),
            (34.052235, -118.243683, 'Los Angeles, CA, USA')
        ]
        self.cursor.executemany('INSERT INTO locations VALUES (?, ?, ?)', data)
        self.connection.commit()

    def check_nearby(self, coordinates):
        self.cursor.execute('SELECT latitude, longitude, address FROM locations')
        rows = self.cursor.fetchall()
        for row in rows:
            stored_coordinates = (row[0], row[1])
            if geodesic(stored_coordinates, (coordinates.latitude, coordinates.longitude)).km <= 5:
                return row[2]
        return None
