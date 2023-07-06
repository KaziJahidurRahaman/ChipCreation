import rasterio
from rasterio.windows import Window
import geopandas as gpd
import os
from shapely.geometry import box


# Path to the input raster image
input_file = "D:/3. Projects/PhnomPenh_TrainingDatGeneration/Data/Bands/AllBands.tif"

# Output directory to store the chips
output_directory = "D:/3. Projects/PhnomPenh_TrainingDatGeneration/Data/Bands/RasterChips/"


# Path to the land class shapefile
landclass_shapefile = "D:/3. Projects/PhnomPenh_TrainingDatGeneration/Data/eo4sd_phnom_penh_lulcvhr_2017/EO4SD_PHNOM_PENH_LULCVHR_2017_Dissolved.gpkg"


# Size of each chip
chip_size = 32  # assuming square chips of 32x32 pixels
c = 0
# Open the raster image
with rasterio.open(input_file) as src:
    # Get the transform and CRS from the source raster
    transform = src.transform

    # Get the dimensions of the raster
    width = src.width
    height = src.height
    crs = src.crs


    # Open the land class shapefile
    landclass_data = gpd.read_file(landclass_shapefile)

    # Iterate over the raster in 32x32 pixel chips
    for y in range(0, height, chip_size):
        for x in range(0, width, chip_size):
            # Define the window for the current chip
            window = Window(x, y, chip_size, chip_size)

            # Read the chip data and transform it to the source CRS
            chip = src.read(window=window)
            chip_transform = rasterio.windows.transform(window, transform)


            # Get the spatial extent of the chip
            chip_bounds = rasterio.windows.bounds(window, transform)
 

            chip_polygon = box(*chip_bounds)
            

            # Check for land class within the chip using spatial query
            landclass = landclass_data[landclass_data.geometry.intersects(chip_polygon)]
            
            
            if len(landclass) <=0:
                print("No land class found for for a chip. Skipping")
                
            else:
                # Dissolve the land class based on 'C_L4'
                dissolved_landclass = landclass.dissolve(by='C_L4')
                
                
                # Recalibrate the shape area for polygons in landclass
                dissolved_landclass['AREA'] = dissolved_landclass.geometry.area
                
                largest = dissolved_landclass.sort_values('AREA', ascending=False).iloc[[0]]
                   
                output_path = os.path.join(output_directory,str(largest.index[0]))
                
                isExist = os.path.exists(output_path)
                
                if not isExist:
                    print('Path to save chips, doesnot exist, creating path...')
                    # Create a new directory because it does not exist
                    os.makedirs(output_path)
 
   
                # Create an output file name
                chip_filename =f'{largest.index[0]}_{x}_{y}.tif'
                
                # chip_filename = f'chip_{x}_{y}.tif'  
                output_path = os.path.join(output_path, chip_filename)


                # Save the chip to a new raster file
                with rasterio.open(output_path, 'w', driver='GTiff', width=chip_size, height=chip_size,
                                    count=src.count, dtype=chip.dtype,crs = crs, transform=chip_transform) as dst:
                    dst.write(chip)
                print(f'{chip_filename} ....... Saved')
                c = c+1
print(c)