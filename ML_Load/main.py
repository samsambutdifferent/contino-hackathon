import re
import ee
import folium
import geehydro
import json
import calendar
import os
import time

service_account = ' ee-service-account@adtech-contino.iam.gserviceaccount.com'
#print(os.listdir())
credentials = ee.ServiceAccountCredentials(service_account, 'ML_Load\ee-privatekey.json')
keys = ["year","roi","water","forest","shrub_grass","wetlands","croplands","urban","crop_mosaic","snow_ice","barren","tundra"]
groups=['water','forest','forest','forest','forest','forest','shrub_grass','shrub_grass','shrub_grass','shrub_grass','shrub_grass','wetlands','croplands','urban', 'crop_mosaic', 'snow_ice', 'barren','tundra']
def main():
    #ee.Initialize(credentials=credentials,project='adtech-contino')
    ee.Authenticate()
    ee.Initialize()
    json_to_write = []
    #Define a region of interest as a point.  Change the coordinates
    #to get a classification of any place where there is imagery.
    input_point = [121.4737, 31.2304]
    roi = ee.Geometry.Point(input_point)
    start_date = "1999"
    end_date = "2020"
    # Load Landsat 5 input imagery.
    landsat = ee.Image(ee.ImageCollection('LANDSAT/LT05/C01/T1_TOA')
    .filterDate('2000-01-01', '2019-12-31')
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
    for year in range(1990, 2020):
        #for month in range(1,12):
                    #calendar_days=calendar.monthrange(year, month)[1]
                    #month_string = "{:02d}".format(month)
            #for day in range(1,calendar_days):
                #if day != calendar_days:
                   # end_day = day +21
                    #end_day_string = "{:02d}".format(end_day)
                    #day_string = "{:02d}".format(day)
                    #print((f'{str(year)}-{month_string}-{day_string}'))
                    #print((f'{str(year)}-{month_string}-{day_string}'))
                    landsat = ee.Image(ee.ImageCollection('LANDSAT/LT05/C01/T1_TOA')
                    .filterDate((f'{str(year)}-01-01'), (f'{str(year)}-12-31'))
                    .filterBounds(roi)
                    .first())

                    # Compute cloud score.
                    cloudScore = ee.Algorithms.Landsat.simpleCloudScore(landsat).select('cloud')

                    # Mask the input for clouds.  Compute the min of the input mask to mask
                    # pixels where any band is masked.  Combine that with the cloud mask.
                    input = landsat.updateMask(landsat.mask().reduce('min'))
                    input= input.updateMask((cloudScore.lte(50)))

                    # Classify the input imagery.
                    classified = input.classify(classifier)
                    classified = classified.addBands(modis)
                    # Sample the input with a different random seed to get validation data.
                    validation = input.addBands(modis).sample(
                    numPixels= 5000,
                    seed= 1
                    # Filter the result to get rid of any null pixels.
                    ).filter(ee.Filter.neq('B1', None))

                    try:
                        igbpPalette = [
                            'aec3d4', 
                            '152106', '225129', '369b47', '30eb5b', '387242',
                            '6a2325', 'c3aa69', 'b76031', 'd9903d', '91af40',
                            '111149', 
                            'cdb33b',
                            'cc0013',
                            '33280d',
                            'd7cdcc',
                            'f7e084',
                            '6f6f6f'
                            ]
                        
                        visParams = {'palette':igbpPalette, 'min': 0, 'max': 1, 'bands': ['Land_Cover_Type_1']}
                        # Display the input and the classification.
                        #ee.Map.centerObject(roi, 10)
                        #ee.Map.addLayer(input, {'bands': ['B3', 'B2', 'B1'], 'max': 0.4}, 'landsat')
                        #ee.Map.addLayer(classified, , 'classification')

                        #image is produced in greyscale
                        # more investigation needed into why palette not applied
                        banded_image = classified.visualize(**visParams)
                        task_config = {'image': banded_image,
                            'description': f'{str(year)}',
                            'scale':30,
                            'maxPixels': 1e13,
                            'bucket':"hackathon_images"}
                        task=ee.batch.Export.image.toCloudStorage(**task_config)
                        task.start()

                        while task.active() == True:
                            print('status for task (id: {} status {}).'.format(task.id, task.state))
                            time.sleep(5)

                    except Exception as e:
                        pass


if __name__ == "__main__":
    main()