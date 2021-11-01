import ee
import folium
import geehydro

service_account = ' ee-service-account@adtech-contino.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, './ee-privatekey.json')
groups=['water','forest','forest','forest','forest','forest','shrub, grass','shrub, grass','shrub, grass','shrub, grass','shrub, grass','wetlands','croplands','urban', 'crop mosaic', 'snow and ice', 'barren','tundra']
def main():
    ee.Initialize(credentials)

    json_to_write = []
    #Define a region of interest as a point.  Change the coordinates
    #to get a classification of any place where there is imagery.
    input_point = [121.4737, 31.2304]
    roi = ee.Geometry.Point(input_point)
    start_date = "1999"
    end_date = "2020"
    # Load Landsat 5 input imagery.
    landsat = ee.Image(ee.ImageCollection('LANDSAT/LT05/C01/T1_TOA')
     .filterDate('2000-01-01', '2011-12-31')
    .filterBounds(roi)
    .sort('CLOUD_COVER')
    .first())

    # Compute cloud score.
    cloudScore = ee.Algorithms.Landsat.simpleCloudScore(landsat).select('cloud')

    # Mask the input for clouds.  Compute the min of the input mask to mask
    # pixels where any band is masked.  Combine that with the cloud mask.
    input = landsat.updateMask(landsat.mask().reduce('min'))
    input= input.updateMask((cloudScore.lte(50)))

    # Use MODIS land cover, IGBP classification, for training.
    modis = ee.Image('MODIS/051/MCD12Q1/2011_01_01').select('Land_Cover_Type_1')

    # Sample the input imagery to get a FeatureCollection of training data.
    training = input.addBands(modis).sample(
    numPixels= 5000,
    seed= 0
    )

    #this classifier will be used on the historical images
    classifier = ee.Classifier.smileRandomForest(10).train(
        features= training,
        classProperty= 'Land_Cover_Type_1',
        inputProperties= ['B1', 'B2', 'B3', 'B4', 'B5', 'B7']
        )


    #for each year, grab the image, classify, then write out the values
    for year in range(1999, 2020):

        landsat = ee.Image(ee.ImageCollection('LANDSAT/LE07/C01/T1_TOA')
        .filterDate((f'{str(year)}-01-01'), (f'{str(year)}-12-31'))
        .filterBounds(roi)
        .sort('CLOUD_COVER')
        .first())

        # Compute cloud score.
        cloudScore = ee.Algorithms.Landsat.simpleCloudScore(landsat).select('cloud')

        # Mask the input for clouds.  Compute the min of the input mask to mask
        # pixels where any band is masked.  Combine that with the cloud mask.
        input = landsat.updateMask(landsat.mask().reduce('min'))
        input= input.updateMask((cloudScore.lte(50)))

        # Classify the input imagery.
        classified = input.classify(classifier)

        # Sample the input with a different random seed to get validation data.
        validation = input.addBands(modis).sample(
        numPixels= 5000,
        seed= 1
        # Filter the result to get rid of any null pixels.
        ).filter(ee.Filter.neq('B1', None))

        # Classify the validation data.
        validated = validation.classify(classifier)

        # Define a palette for the IGBP classification.
        #igbpPalette = [
        #  'aec3d4', # water
        #  '152106', '225129', '369b47', '30eb5b', '387242', # forest
        #  '6a2325', 'c3aa69', 'b76031', 'd9903d', '91af40',  # shrub, grass
        #  '111149', # wetlands
        #  'cdb33b', # croplands
        #  'cc0013', # urban
        #  '33280d', # crop mosaic
        #  'd7cdcc', # snow and ice
        #  'f7e084', # barren
        #  '6f6f6f'  # tundra
        #]

        area_classified = ee.Image.pixelArea().divide(1e6).addBands(classified).reduceRegion(
            reducer= ee.Reducer.sum().group(1, 'group'),
            geometry= landsat.geometry(),
            scale= 1000
        )

        outputReducers = ee.List(area_classified.get('groups'))
        get_groups = area_classified.getInfo()
        group_dict ={'year':year, 'roi':', '.join(map(str, input_point))}
        group_dict.update({groups[int(x['group'])]:x['sum'] for x in get_groups['groups']})
        json_to_write.extend([group_dict])

if __name__ == "__main__":
    main()