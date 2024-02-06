import ee
import geemap
import time
# Authenticate to Earth Engine account
# Make sure to run 'earthengine authenticate' in the command line first
ee.Authenticate()

# Initialize Earth Engine
ee.Initialize(project='ee-sharmanikhil0607')


# Define the region of interest (ROI) using latitudes and longitudes
roi = ee.Geometry.Point([31.5051, -26.6061]).buffer(2)

# Define the date range for filtering images
start_date = '2022-01-01'
end_date = '2022-06-30'

# Load a Landsat image collection and filter based on ROI and date range
image_collection = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                    .filterBounds(roi)
                    .filterDate(ee.Date(start_date), ee.Date(end_date)))

# Print the number of images in the collection
print("Number of images in the collection:", image_collection.size().getInfo())

# Select the first image from the collection
selected_image = image_collection.first()
print(selected_image)
#print(type(selected_image))
print('Image size (bytes):', selected_image.getInfo()['properties']['system:asset_size'])

# Display the selected image on an interactive map using geemap
Map = geemap.Map()
Map.centerObject(roi, 3)  # Adjust the zoom level as needed
Map.addLayer(selected_image, {
    'bands': ['SR_B4', 'SR_B3', 'SR_B2'],  # Adjust bands based on the image
    'min': 0,
    'max': 3000
}, 'Selected Image')

# Add the ROI to the map for reference
Map.addLayer(roi, {'color': 'FF0000'}, 'ROI')

# Display the map

print('Image size (bytes):', selected_image.getInfo()['properties']['system:asset_size'])
Map


# Export the image to Google Drive
task = ee.batch.Export.image.toDrive(
    image=selected_image,
    folder='Geo_Spatial',
    description='landsat_image',
    scale=300,
    region=roi,
    maxPixels=1e13  # Adjust the value based on your needs
)

# Example export task to Google Cloud Storage
# task = ee.batch.Export.image.toCloudStorage(
#     image=selected_image,
#     description='ImageExport',
#     bucket='cis-692-nikhil/cis-692',
#     fileNamePrefix='landsat_image',
#     scale=300,
#     region=roi
# )

# Start the export task
task.start()


# Monitor the task status
while task.status()['state'] in ['READY', 'RUNNING']:
    print('Task is', task.status()['state'])
    time.sleep(10)  # Wait for 10 seconds

print('Task completed:', task.status()['state'])
print('Task status:', task.status())
