import numpy as np
from osgeo import gdal, osr

class GeoTools():
    def __init__(self):
        self.EARTH_RADIUS = 6378137
        
    def array2raster(self, newRasterfn,rasterOrigin,pixelWidth,pixelHeight, data, variables, rotate=0):
        '''Convert data dictionary (of arrays) into a multiband GeoTiff
        
        :param newRasterfn: filename to save to
        :param rasterOrigin: location of top left corner
        :param pixelWidth: e-w pixel size
        :param pixelHeight: n-s pixel size
        :param data: dictionary containing the data arrays
        :param variables: list of which keys from the dictionary to output
        :param rotate: Optional rotation angle (in radians)
        '''
        cols = len(data['longitude'])
        rows = len(data['latitude'])
        originX = rasterOrigin[0]
        originY = rasterOrigin[1]
    
        we_res = np.cos(rotate) * pixelWidth
        rotX = np.sin(rotate) * pixelWidth
        rotY = -np.sin(rotate) * pixelHeight
        ns_res = np.cos(rotate) * pixelHeight
    
        driver = gdal.GetDriverByName('GTiff')
        nbands = len(variables)
        outRaster = driver.Create(newRasterfn, cols, rows, nbands, gdal.GDT_UInt16)
        outRaster.SetGeoTransform((originX, we_res, rotX, originY, rotY, ns_res))
        for band,key in enumerate(variables, 1):
            outband = outRaster.GetRasterBand(band)
            outband.SetNoDataValue(0)
            outband.WriteArray(data[key])
            outband.FlushCache()
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromEPSG(4326)
        outRaster.SetProjection(outRasterSRS.ExportToWkt())
    
    def extract_region(self, lon_array, lat_array, region):
        """Find which points are inside the region of interest.
        
        Returns two slice objects: islice, jslice
        :param lon_array: A numpy array containing the longitudes
        :param lat_array: A numpy array containing the latitudes
        :param region: A list containing the ROI corners: min lat, max lat, min lon, max lon
        """
        i,j = np.where((region[0]<=lat_array) & (lat_array<=region[1]) &
                       (region[2]<=lon_array) & (lon_array<=region[3]))
        islice = slice(i.min(),i.max()+1)
        jslice = slice(j.min(),j.max()+1)
        return islice, jslice        
    
    def get_new_lat_lon(self, old_lon, old_lat, region):
        """
        Calculate new coordinate lists to use for regridding, such that the resolution is about the same as the old grid
        """
        min_lon = region[2]
        max_lon = region[3]
        min_lat = region[0]
        max_lat = region[1]

        # Calculate resolution using the old grid - use max value of old grid, to avoid any holes
        # nb use of np.abs is because lat/lon arrays can be 'backwards'
        dx = np.max(np.abs(np.diff(old_lon, axis=1)))
        dy = np.max(np.abs(np.diff(old_lat, axis=0)))

        # So how many points do we need in new grid?
        nx = np.floor((max_lon - min_lon)/dx)
        ny = np.floor((max_lat - min_lat)/dy)

        new_lon = np.linspace(min_lon, max_lon, nx)
        new_lat = np.linspace(min_lat, max_lat, ny)
        return new_lon, new_lat

    
    def extract_region_and_regrid(self, old_lon, old_lat, new_lon, new_lat, data):
        """
        Re-grid data to a regular grid, at the same time as extracting the region of interest
        
        Go through each point of the original grid, check if it is in the new grid, and if so append the 
        data value to the closest grid point in the new grid. 
        Returns the mean value for each new grid point.
        
        :param old_lon: Longitude for the original grid (2d)
        :param old_lat: Latitude for the original grid (2d)
        :param new_lon: Longitude for the new grid (1d)
        :param new_lat: Latitude for the new grid (1d)
        """
        dx = np.diff(new_lon)[0]
        dy = np.diff(new_lat)[0]
        
        new_data = np.zeros((len(new_lat), len(new_lon)))
        count = np.zeros((len(new_lat), len(new_lon)))
        
        # loop over all points in the OLD grid
        for j in np.arange(old_lon.shape[0]):
            for i in np.arange(old_lon.shape[1]):
                # Ignore points that aren't within the region of interest
                if ((np.min(new_lon) <= old_lon[j,i] <= np.max(new_lon)) &
                    (np.min(new_lat) <= old_lat[j,i] <= np.max(new_lat)) ):
            
                    # Find which point this corresponds to on the new grid, and add the data value
                    new_i = int((old_lon[j,i] - np.min(new_lon)) / dx)
                    new_j = int((old_lat[j,i] - np.min(new_lat)) / dy)
                    new_data[new_j, new_i] += data[j,i]
                    count[new_j, new_i] += 1
        count[count==0] = np.nan # Prevent division by zero warnings
        return new_data/count # Return the mean
                

    def latlon_distance_meters(self, lat, lon):
        """Calculate the great circle distance between two points on the earth using the Haversine equation
        
        :param lat: latitude pair in decimal degree as a list or scipy vec
        :param lon: longitude pair in decimal degree as a list or scipy vec
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(np.radians, [lon[0], lat[0], lon[1], lat[1]])
    
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a)) 
    
        distance = self.EARTH_RADIUS * c
        return distance
