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
        array = data[data.keys()[0]]
        cols = array.shape[1]
        rows = array.shape[0]
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
