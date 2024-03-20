import ee
import geemap
import os
import time
import shutil
from PIL import Image
from google.colab import files, drive
from IPython.display import display, Image
import cv2
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
import json

# Authenticate to Earth Engine account
ee.Authenticate()

# Initialize Earth Engine
project = 'ee-sharmanikhil0607'

# Installs geemap package
import subprocess

try:
    import geemap
except ImportError:
    print('geemap package not installed. Installing ...')
    subprocess.check_call(["python", '-m', 'pip', 'install', 'geemap'])

# Checks whether this notebook is running on Google Colab
try:
    import google.colab
    import geemap.foliumap as emap
except:
    import geemap as emap

# Authenticates and initializes Earth Engine
import ee

try:
    ee.Initialize()
    ee.Initialize(project=project)
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project=project)
    ee.Initialize()


# Providing Longitude and Latitude for the location we need the images
# lon, lat = -90.70, 34.71

# Providing the date range for which we need the data.
# start_date, end_date = '2013-01-01', '2022-12-31'

# Percent of cloud cover we want on the photos
# max_cloud_cover = 50

# Folder path in Google Drive
drive_folder_path = '/content/drive/My Drive/Geo_Spatial/'


# Getting user input for latitude, longitude, start date, and end date
lat = float(input('Enter latitude: '))
lon = float(input('Enter longitude: '))
start_date = input('Enter start date (YYYY-MM-DD): ')
end_date = input('Enter end date (YYYY-MM-DD): ')
max_cloud_cover = float(input('Enter Maximum cloud cover (Images having more than max cloud cover will be filtered out) 0 - 100: '))
print("Now let's get the height and width of the image\n")
image_width = float(input('Width of the image: '))
image_height = float(input('Height of the image: '))


# Fetching Image collection from the Top Of Atmosphere (TOA) Satellite given the date range and the location.
image_collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA')
    .filterBounds(ee.Geometry.Point(lon, lat)).filterDate(start_date, end_date)
    .filter(ee.Filter.lt('CLOUD_COVER', max_cloud_cover))) # All the photos with more than max_cloud_cover will be filtered out.
print('Total images in the image collection:', image_collection.size().getInfo())

# Region: An area around the given (lon, lat)
region = ee.Geometry.BBox(
    lon - image_height ,
    lat - image_width,
    lon + image_height,
    lat + image_width
    )


# Mount Google Drive to access files
drive.mount('/content/drive')

# Folder Path
folder_path = drive_folder_path

# List all files in the folder
file_list = os.listdir(folder_path)

# Delete all files in the folder
for file_name in file_list:
    file_path = os.path.join(folder_path, file_name)
    os.remove(file_path)


# Main loop to continuously monitor the folder
while True:
    # List all files in the folder
    file_list = os.listdir(folder_path)

    # Check if any files are present in the folder
    if len(file_list) > 0:
        print("Remooving files from the folder:", file_list)
    else:
        print("All the content has been removed from the folder.")
        break;
    # Wait for some time before checking again
    time.sleep(10)  # Adjust the sleep duration as needed


# Iterate over each image in the collection
image_list = image_collection.toList(image_collection.size())
for i in range(image_list.size().getInfo()):
    image = ee.Image(image_list.get(i))

    # Select bands for RGB visualization
    selected_bands_image = image.select(['B4', 'B3', 'B2'])

    # Apply color correction
    corrected_image = selected_bands_image.visualize(**{
        'min': 0,
        'max': 0.3,
        'gamma': 1.4,
        'bands': ['B4', 'B3', 'B2']
    })

    # Create a Map
    Map = geemap.Map()

    # Set the center and zoom level explicitly
    Map.centerObject(region, 7)

    # Add the color-corrected image to the map
    Map.addLayer(corrected_image, {}, f'Corrected RGB - Image {i}')

    # Export the color-corrected image to Google Drive as GeoTIFF
    export_params = {
        'image': corrected_image,
        'description': f'landsat_image_{i}',
        'scale': 30,  # Adjust scale as needed
        'region': region,
        'maxPixels': 1e13,
        'folder': 'Geo_Spatial',
        'fileFormat': 'GeoTIFF',
        'formatOptions': {'cloudOptimized': True}
    }

    # Start the export task
    task = ee.batch.Export.image.toDrive(**export_params)
    task.start()

    # Print status
    print(f"Exporting color-corrected image {i} to Drive. Task ID: {task.id}")

    # Display the map
    Map.addLayerControl()
    Map


# Path to the folder containing your images
images_folder_path = drive_folder_path

# Get the expected number of files to be downloaded
expected_num_files = image_collection.size().getInfo()

# Initialize a variable to keep track of the number of .tif files downloaded
downloaded_tif_files = 0

# Loop until all .tif files are downloaded
while downloaded_tif_files < expected_num_files:
    # List files in the images folder ending with .tif
    tif_files = [file for file in os.listdir(images_folder_path) if file.endswith('.tif')]

    # Update the number of .tif files downloaded
    downloaded_tif_files = len(tif_files)

    # Clear the output
    clear_output(wait=True)

    # Print progress
    print(f'{downloaded_tif_files} out of {expected_num_files} .tif files downloaded. Waiting for all .tif files to be downloaded...')

    # If not all .tif files are downloaded, wait for some time before checking again
    if downloaded_tif_files < expected_num_files:
        time.sleep(10)  # Adjust the sleep duration as needed

# All .tif files are downloaded
print(f'All {expected_num_files} .tif files downloaded successfully.')


# Specify the folder path in Google Drive
drive_folder_path = drive_folder_path

# Create a temporary directory to store the downloaded images
temp_dir = '/content/temp_images'
os.makedirs(temp_dir, exist_ok=True)
print(f'Temporary directory: {temp_dir}')

# Copy all GeoTIFF files from Google Drive to the temporary directory
for file_name in os.listdir(drive_folder_path):
    if file_name.endswith('.tif'):
        src_path = os.path.join(drive_folder_path, file_name)
        dest_path = os.path.join(temp_dir, file_name)
        shutil.copy(src_path, dest_path)
        print(f'Copied: {file_name}')

# Confirm that the images are copied to the temporary directory
print(f'Number of images copied: {len(os.listdir(temp_dir))}')

# Sort the images by filename
image_files = sorted(os.listdir(temp_dir))

# Create a list to store image paths
image_paths = [os.path.join(temp_dir, img) for img in image_files]

# Specify the output video file path
output_video_path = '/content/output.mp4'

# Read the first image to get dimensions
first_image = cv2.imread(image_paths[0])
height, width, layers = first_image.shape

# Create the video using OpenCV
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use appropriate codec
video_writer = cv2.VideoWriter(output_video_path, fourcc, 10, (width, height))

for image_path in image_paths:
    img = cv2.imread(image_path)
    video_writer.write(img)

video_writer.release()

# Confirm that the video is created
print(f'Video created: {output_video_path}')


from google.colab import files

# Specify the path to the video file
video_path = '/content/output.mp4'

# Trigger the download of the video file
files.download(video_path)

# Specify the path to the video file
video_path = '/content/output.mp4'

# Create the destination folder if it doesn't exist
!mkdir -p "{drive_destination_folder}"

# Copy the video to the destination folder in Google Drive
drive_destination_path = drive_folder_path + 'output.mp4'
!cp "{video_path}" "{drive_destination_path}"

# Provide a link to the video in Google Drive
print("Video saved at: " + drive_destination_path)


# Specify the video file name
video_file_name = 'output.mp4'
folder_path = drive_folder_path

# Construct the full path to the video file
video_file_path = os.path.join(folder_path, video_file_name)

# Check if the video file exists in Google Drive
while not os.path.exists(video_file_path):
    print("Video file not found in Google Drive. Waiting...")
    time.sleep(10)  # Wait for 10 seconds before checking again

# Video file found, proceed with the next part of the code
print("Video has been downloaded to the drive.")


# Specify the path to the video file
video_path = '/content/output.mp4'

# Open the video file
cap = cv2.VideoCapture(video_path)

# Initialize lists to store normalized differences and frame numbers
normalized_diffs = []
frame_numbers = []

# Read the first frame
ret, prev_frame = cap.read()
prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
frame_number = 1

# Process each frame in the video
while True:
    # Read the next frame
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to grayscale
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Calculate the absolute difference between frames
    abs_diff = np.sum(np.abs(frame_gray - prev_frame_gray))

    # Append the absolute difference and frame number to the lists
    normalized_diffs.append(abs_diff)
    frame_numbers.append(frame_number)
    frame_number += 1

    # Update the previous frame
    prev_frame_gray = frame_gray

# Release the video capture object
cap.release()

# Calculate the maximum absolute difference
max_diff = max(normalized_diffs)

# Normalize the differences
normalized_diffs = [(100 * diff) / max_diff for diff in normalized_diffs]

# Round the normalized differences to 2 decimal places
normalized_diffs = [round(diff, 2) for diff in normalized_diffs]

# Plot the normalized differences over frame numbers
plt.figure(figsize=(17, 6))
plt.plot(frame_numbers, normalized_diffs)
plt.title('Normalized Differences Between Consecutive Frames')
plt.xlabel('Frame Number')
plt.ylabel('Normalized Difference')
plt.grid(True)
plt.show()

# Create a dictionary to store the data
data = {'frame_numbers': frame_numbers, 'normalized_differences': normalized_diffs}


# Create the JSON file path by joining the directory path with the file name
json_file_path = os.path.join(drive_folder_path, 'differences.json')

# Write the data to the JSON file
with open(json_file_path, 'w') as json_file:
    json.dump(data, json_file)

print(f"JSON file '{json_file_path}' created successfully.")
