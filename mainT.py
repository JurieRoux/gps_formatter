import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QFrame
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import sys
import threading

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
        if isinstance(coordinate, str):
            return float(coordinate.strip())
        return float(coordinate)

class ReverseGeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="gps_formatter")

    def get_address(self, coordinates):
        try:
            location = self.geolocator.reverse((coordinates.latitude, coordinates.longitude), exactly_one=True, zoom=18)
            return location.address if location else "Address not found"
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Error during reverse geocoding: {e}")
            return "Error during reverse geocoding"

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

class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap, QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(pixmap.size())  # Set fixed size based on pixmap size

    def showEvent(self, event):
        screen_geometry = QtWidgets.QDesktopWidget().screenGeometry(QtWidgets.QDesktopWidget().primaryScreen())
        self.setGeometry(screen_geometry)
        super().showEvent(event)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.showSplashScreen()

    def showSplashScreen(self):
        pixmap = QtGui.QPixmap('Welcome.png')
        self.splash = SplashScreen(pixmap)
        self.splash.show()
        QtCore.QTimer.singleShot(3000, self.closeSplashScreen)  # Close splash screen after 3 seconds

    def closeSplashScreen(self):
        self.splash.close()

    def initUI(self):
        self.setWindowTitle('GPS Reverse Geocoder')
        self.setGeometry(100, 100, 800, 600)

        layout = QtWidgets.QVBoxLayout()

        # Logo
        self.logo = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap('logo.png')
        self.logo.setPixmap(pixmap)
        self.logo.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.logo)

        # eLogger GPS input block
        elogger_block = QtWidgets.QWidget(self)
        elogger_block_layout = QtWidgets.QVBoxLayout(elogger_block)
        elogger_block.setStyleSheet("background-color: #09e5a4; padding: 5px; border-radius: 10px; text-align: center;")
        self.eloggerLabel = QtWidgets.QLabel('Enter eLogger GPS coordinate (e.g., 33.932798,S,18.4213866,E):', self)
        self.eloggerLabel.setAlignment(QtCore.Qt.AlignCenter)
        elogger_block_layout.addWidget(self.eloggerLabel)
        self.eloggerEntry = QtWidgets.QLineEdit(self)
        elogger_block_layout.addWidget(self.eloggerEntry)
        self.eloggerButton = QtWidgets.QPushButton('Submit eLogger GPS', self)
        self.eloggerButton.clicked.connect(self.process_manual_entry_elogger)
        elogger_block_layout.addWidget(self.eloggerButton)
        layout.addWidget(elogger_block)
        layout.addSpacing(50)

        # Traditional GPS input block
        traditional_block = QtWidgets.QWidget(self)
        traditional_block_layout = QtWidgets.QVBoxLayout(traditional_block)
        traditional_block.setStyleSheet("background-color: #09e5a4; padding: 5px; border-radius: 10px; text-align: center;")
        self.traditionalLabel = QtWidgets.QLabel('Enter traditional GPS coordinates (e.g., -25.852981907621604, 28.324011875758643):', self)
        self.traditionalLabel.setAlignment(QtCore.Qt.AlignCenter)
        traditional_block_layout.addWidget(self.traditionalLabel)
        self.traditionalEntry = QtWidgets.QLineEdit(self)
        traditional_block_layout.addWidget(self.traditionalEntry)
        self.traditionalButton = QtWidgets.QPushButton('Submit Traditional GPS', self)
        self.traditionalButton.clicked.connect(self.process_manual_entry_traditional)
        traditional_block_layout.addWidget(self.traditionalButton)
        layout.addWidget(traditional_block)
        layout.addSpacing(50)

        # Select file block
        file_block = QtWidgets.QWidget(self)
        file_block_layout = QtWidgets.QVBoxLayout(file_block)
        file_block.setStyleSheet("background-color: #09e5a4; padding: 0px; border-radius: 10px; text-align: center;")
        self.selectFileButton = QtWidgets.QPushButton('Select Excel File', self)
        self.selectFileButton.clicked.connect(self.select_file)
        file_block_layout.addWidget(self.selectFileButton)
        layout.addWidget(file_block)
        layout.addSpacing(10)

        # Progress Bar
        self.progressBar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progressBar)
        layout.addSpacing(10)

        # Loading Label
        self.loadingLabel = QtWidgets.QLabel('', self)
        self.loadingLabel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.loadingLabel)
        layout.addSpacing(10)

        # Result Label
        self.resultLabel = QtWidgets.QLabel('', self)
        self.resultLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.resultLabel.setWordWrap(True)
        layout.addWidget(self.resultLabel)

        self.setLayout(layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                font-family: Consolas, Arial;
                font-size: 14px;
                text-align: center;
            }
            QPushButton {
                background-color: #09a3a3;
                color: black;
                padding: 10px;
                border-radius: 3px;
                font-size: 16px;
                margin: 5px 0;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #078787;
            }
            QLabel {
                margin: 5px 0;
                padding: 5px;
                text-align: center;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ffffff;
                border-radius: 5px;
                font-size: 14px;
                margin: 5px 0;
                text-align: center;
                background-color: white;
            }
            QProgressBar {
                border: 2px solid #15f59e;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #09a3a3;
                width: 20px;
            }
        """)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Excel File', '', 'Excel Files (*.xlsx);;All Files (*)')
        if file_path:
            threading.Thread(target=self.process_file, args=(file_path,)).start()

    def process_file(self, file_path):
        try:
            self.start_loading_animation()
            self.loadingLabel.setText("Loading...")
            df = pd.read_excel(file_path)

            df['GPS Co-ordinates'] = df['GPS Co-ordinates'].astype(str)
            df['End Destination'] = ""

            total_rows = len(df)
            self.progressBar.setMaximum(total_rows)

            for index, row in df.iterrows():
                gps_coordinate = str(row['GPS Co-ordinates']).strip()
                latitude, longitude = adjust_coordinates(gps_coordinate)
                if latitude is None or longitude is None:
                    continue
                address = process_coordinates(latitude, longitude)
                df.at[index, 'End Destination'] = address

                self.progressBar.setValue(index + 1)
                QtCore.QCoreApplication.processEvents()

            output_file_path = file_path.replace(".xlsx", "_with_end_destinations.xlsx")
            df.to_excel(output_file_path, index=False)
            self.resultLabel.setText(f"Updated Excel file saved to: {output_file_path}")
        except pd.errors.EmptyDataError:
            QMessageBox.critical(self, "Error", "The selected file is empty.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "The selected file was not found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        finally:
            self.stop_loading_animation()
            self.progressBar.setValue(0)
            self.loadingLabel.setText("")  # Clear loading text at the end

    def start_loading_animation(self):
        self.loading = True
        self.animate_loading()

    def stop_loading_animation(self):
        self.loading = False

    def animate_loading(self):
        if self.loading:
            current_text = self.loadingLabel.text()
            if current_text.endswith('...'):
                new_text = 'Loading'
            else:
                new_text = current_text + '.'
            self.loadingLabel.setText(new_text)
            QtCore.QTimer.singleShot(500, self.animate_loading)

    def process_manual_entry_elogger(self):
        gps_coordinate = self.eloggerEntry.text()
        latitude, longitude = adjust_coordinates(gps_coordinate)
        if latitude is None or longitude is None:
            self.resultLabel.setText(f"Invalid GPS coordinate: {gps_coordinate}")
            return
        address = process_coordinates(latitude, longitude)
        self.resultLabel.setText(f"Reverse geocoded address for ({latitude}, {longitude}): {address}")

    def process_manual_entry_traditional(self):
        lat_long = self.traditionalEntry.text()
        try:
            latitude, longitude = map(float, lat_long.split(','))
            address = process_coordinates(latitude, longitude)
            self.resultLabel.setText(f"Reverse geocoded address for ({latitude}, {longitude}): {address}")
        except ValueError:
            self.resultLabel.setText(f"Invalid input: {lat_long}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
