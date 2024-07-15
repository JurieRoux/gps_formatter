import pandas as pd
import sqlite3
import googlemaps
from tkinter import Tk, filedialog, Label, Button, Entry, Toplevel, messagebox, PhotoImage, StringVar
from tkinter import ttk
import threading
import logging

# Configure logging
logging.basicConfig(filename='gps_reverse_geocoder.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Replace 'YOUR_GOOGLE_MAPS_API_KEY' with your actual Google Maps API key
GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Set up the SQLite database
conn = sqlite3.connect('gps_coordinates.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS coordinates (
        id INTEGER PRIMARY KEY,
        latitude REAL,
        longitude REAL,
        address TEXT
    )
''')
conn.commit()

class GpsCoordinates:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

class GpsFormatter:
    @staticmethod
    def build_coordinates(latitude, longitude):
        gps_coordinates = GpsCoordinates(0, 0)
        gps_coordinates.latitude = GpsFormatter.format_coordinate(latitude)
        gps_coordinates.longitude = GpsFormatter.format_coordinate(longitude)
        return gps_coordinates

    @staticmethod
    def format_coordinate(coordinate):
        return float(coordinate.strip())

class ReverseGeocodingService:
    def get_address(self, coordinates):
        # Check the local database first
        address = self.get_address_from_db(coordinates.latitude, coordinates.longitude)
        if address:
            return address

        # If not found in the database, use the Google Maps API
        try:
            results = gmaps.reverse_geocode((coordinates.latitude, coordinates.longitude))
            if results:
                address = results[0]['formatted_address']
                self.save_coordinates_to_db(coordinates.latitude, coordinates.longitude, address)
                return address
            else:
                return "Address not found"
        except Exception as e:
            logging.error(f"Error during reverse geocoding: {e}")
            return "Error during reverse geocoding"

    def get_address_from_db(self, latitude, longitude):
        c.execute("SELECT address FROM coordinates WHERE latitude=? AND longitude=?", (latitude, longitude))
        result = c.fetchone()
        return result[0] if result else None

    def save_coordinates_to_db(self, latitude, longitude, address):
        c.execute("INSERT INTO coordinates (latitude, longitude, address) VALUES (?, ?, ?)", (latitude, longitude, address))
        conn.commit()

def adjust_coordinates(gps_coordinate):
    try:
        latitude, lat_direction, longitude, lon_direction = gps_coordinate.split(',')
        latitude = latitude.strip()
        longitude = longitude.strip()

        if lat_direction.strip().upper() == 'S':
            latitude = '-' + latitude
        if lon_direction.strip().upper() == 'W':
            longitude = '-' + longitude

        return latitude, longitude
    except ValueError:
        return None, None

def process_coordinates(latitude, longitude):
    formatter = GpsFormatter()
    coordinates = formatter.build_coordinates(latitude, longitude)
    reverse_geocoding_service = ReverseGeocodingService()
    address = reverse_geocoding_service.get_address(coordinates)
    return address

def select_file():
    file_path = filedialog.askopenfilename(
        title="Select Excel File",
        filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
    )
    if file_path:
        threading.Thread(target=process_file, args=(file_path,)).start()

def process_file(file_path):
    try:
        start_loading_animation()
        df = pd.read_excel(file_path)
        
        # Drop rows where 'GPS Co-ordinates' is NaN or empty
        df = df.dropna(subset=['GPS Co-ordinates'])
        df = df[df['GPS Co-ordinates'].str.strip() != '']

        df['GPS Co-ordinates'] = df['GPS Co-ordinates'].astype(str)
        df['End Destination'] = ""

        total_rows = len(df)
        progress_bar['maximum'] = total_rows

        for index, row in df.iterrows():
            gps_coordinate = str(row['GPS Co-ordinates']).strip()
            latitude, longitude = adjust_coordinates(gps_coordinate)
            if latitude is None or longitude is None:
                continue
            address = process_coordinates(latitude, longitude)
            df.at[index, 'End Destination'] = address

            progress_bar['value'] = index + 1
            root.update_idletasks()

        output_file_path = file_path.replace(".xlsx", "_with_end_destinations.xlsx")
        df.to_excel(output_file_path, index=False)
        result_label.config(text=f"Updated Excel file saved to: {output_file_path}")
        logging.info(f"Updated Excel file saved to: {output_file_path}")
    except pd.errors.EmptyDataError:
        messagebox.showerror("Error", "The selected file is empty.")
        logging.error("The selected file is empty.")
    except FileNotFoundError:
        messagebox.showerror("Error", "The selected file was not found.")
        logging.error("The selected file was not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        logging.error(f"Error processing file: {e}")
    finally:
        stop_loading_animation()
        progress_bar['value'] = 0

def process_manual_entry():
    start_loading_animation()
    gps_coordinate = manual_entry.get()
    latitude, longitude = adjust_coordinates(gps_coordinate)
    if latitude is None or longitude is None:
        result_label.config(text=f"Invalid GPS coordinate: {gps_coordinate}")
        logging.warning(f"Invalid GPS coordinate: {gps_coordinate}")
        stop_loading_animation()
        return
    address = process_coordinates(latitude, longitude)
    result_label.config(text=f"Reverse geocoded address for ({latitude}, {longitude}): {address}")
    logging.info(f"Reverse geocoded address for ({latitude}, {longitude}): {address}")
    stop_loading_animation()

def open_manual_entry_window():
    manual_entry_window = Toplevel(root)
    manual_entry_window.title("Manual GPS Entry")

    Label(manual_entry_window, text="Enter GPS coordinate (e.g., 33.932798,S,18.4213866,E):", bg='#f0f0f0', font=('Arial', 10)).pack(pady=5)
    global manual_entry
    manual_entry = Entry(manual_entry_window, width=50)
    manual_entry.pack(pady=5)
    Button(manual_entry_window, text="Submit", command=process_manual_entry, bg='#09a3a3', fg='white', font=('Arial', 10)).pack(pady=5)

def start_loading_animation():
    global loading
    loading = True
    animate_loading()

def stop_loading_animation():
    global loading
    loading = False

def animate_loading():
    if loading:
        current_text = loading_var.get()
        if current_text.endswith('...'):
            new_text = 'Loading'
        else:
            new_text = current_text + '.'
        loading_var.set(new_text)
        root.after(500, animate_loading)

root = Tk()
root.title("GPS Reverse Geocoder")

# Configure styles
style = ttk.Style()
style.configure("TLabel", background="#ffffff", font=('Arial', 12))
style.configure("TEntry", padding=6, font=('Arial', 12))
style.configure("TFrame", background="#ffffff")
style.configure("Custom.TButton", padding=10, relief="flat", background="#09a3a3", foreground="black", font=('Arial', 12), borderwidth=0)
style.configure("TProgressbar", troughcolor="#ffffff", background="#09a3a3")

# Add logo
logo_path = "logo.png"  # Make sure the logo file is named logo.png and is in the same directory
logo_image = PhotoImage(file=logo_path)
logo_label = Label(root, image=logo_image, bg='#ffffff')
logo_label.pack(pady=10)

Button(root, text="Select Excel File", command=select_file, bg='#09a3a3', fg='white', font=('Arial', 12)).pack(pady=10)
Button(root, text="Enter GPS Manually", command=open_manual_entry_window, bg='#09a3a3', fg='white', font=('Arial', 12)).pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
progress_bar.pack(pady=10)

loading_var = StringVar()
loading_var.set('')
loading_label = Label(root, textvariable=loading_var, bg='#ffffff', font=('Arial', 12))
loading_label.pack(pady=10)

result_label = Label(root, text="", wraplength=400, bg='#ffffff', font=('Arial', 12))
result_label.pack(pady=10)

# Customize GUI layout and styling
root.configure(bg='#ffffff')  # Change background color

root.mainloop()
