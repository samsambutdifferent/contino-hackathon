import re
import ee
from ee import geometry
import folium
import geehydro
import json
import calendar

service_account = ' ee-service-account@adtech-contino.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, './ML_Load/ee-privatekey.json')
keys = ["year","roi","water","forest","shrub_grass","wetlands","croplands","urban","crop_mosaic","snow_ice","barren","tundra"]
groups=['water','forest','forest','forest','forest','forest','shrub_grass','shrub_grass','shrub_grass','shrub_grass','shrub_grass','wetlands','croplands','urban', 'crop_mosaic', 'snow_ice', 'barren','tundra']
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
    .filterDate('2000-01-01', '2020-12-31')
    .filterBounds(roi)
    .filterMetadata('CLOUD_COVER', 'less_than', 20)
    .first())

    # Compute cloud score.
    cloudScore = ee.Algorithms.Landsat.simpleCloudScore(landsat).select('cloud')

    # Mask the input for clouds.  Compute the min of the input mask to mask
    # pixels where any band is masked.  Combine that with the cloud mask.
    #input = landsat.updateMask(landsat.mask().reduce('min'))
    #input= input.updateMask((cloudScore.lte(50)))

    # Use MODIS land cover, IGBP classification, for training.
    modis = ee.Image('MODIS/051/MCD12Q1/2011_01_01').select('Land_Cover_Type_1')
    #input = landsat.updateMask(landsat.mask().reduce('min'))
    #input = input.updateMask(cloudScore.lte(50))

    training = landsat.addBands(modis).sample(
    numPixels= 5000,
    seed= 0
    )

    #landsatComposite = ee.Algorithms.Landsat.simpleComposite(
    #collection= landsat,
    #asFloat= True
    #)

    #training = modis.addBands(landsatComposite).sample(
    #        numPixels= 5000,
    #        seed= 0
    #)

    classifier = ee.Classifier.smileRandomForest(10).train(
      features= training,
      classProperty= 'Land_Cover_Type_1',
      inputProperties= ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
    )

    image_types = ['T1_SR', 'T1_TOA']
    for image_type in image_types:

        L4 = ee.ImageCollection(f'LANDSAT/LT04/C01/{image_type}')   
        L5 = ee.ImageCollection(f'LANDSAT/LT05/C01/{image_type}')
        L7 = ee.ImageCollection(f'LANDSAT/LE07/C01/{image_type}')
        L8 = ee.ImageCollection(f'LANDSAT/LC08/C01/{image_type}')
        merged = L7
        #for each year, grab the image, classify, then write out the values
        for year in range(1983, 2019):
            for month in range(1,12):
                    calendar_days=calendar.monthrange(year, month)[1]
                    month_string = "{:02d}".format(month)
                    for day in range(1,calendar_days):
                        if day != calendar_days:
                            end_day = day +14
                            if end_day>calendar_days:
                                end_day = calendar_days
                            end_day_string = "{:02d}".format(end_day)
                            day_string = "{:02d}".format(day)
                            #L457 = merged.filterDate(f'{str(year)}-{month_string}-{day_string}', f'{str(year)}-{month_string}-{calendar_days}').filterBounds(roi)
                            L457_image= ee.Image(merged.filterDate(f'{str(year)}-{month_string}-{day_string}', f'{str(year)}-{month_string}-{end_day_string}')
                                    .filterBounds(roi)
                                    .first())

                            if L457_image.getInfo() == None:
                                continue

                            classified = L457_image.classify(classifier)

                            area_classified = ee.Image.pixelArea().divide(1e6).addBands(classified).reduceRegion(
                                                reducer= ee.Reducer.sum().group(1, 'group'),
                                                geometry= classified.geometry(),
                                                scale= 1000
                                            )

                            outputReducers = ee.List(area_classified.get('groups'))
                            group_dict ={'year':f'{str(year)}-{month_string}-{end_day_string}', 'roi':', '.join(map(str, input_point))}
                            try:
                                get_groups = area_classified.getInfo()
                                
                                group_dict.update({groups[int(x['group'])]:x['sum'] for x in get_groups['groups']})

                                result = keys - group_dict.keys()
                                for r in result:
                                    group_dict[r] = None
                                json_to_write.extend([group_dict])
                            except Exception as ex:
                                group_dict = {}
                                for r in keys:
                                    group_dict[r] = None
                                json_to_write.extend([group_dict])
                                pass
    write_blob_from_string(
                    '\n'.join([json.dumps(record) for record in json_to_write]),
                    "ml_load",
                    "landsat_merged_historical_monthly_None",
                    "text/json",
                )


def is_img_none(img, gs):
    if img != None:
        return img 

from google.cloud import storage

def write_blob_from_string(source, output_bucket_name, output_file_name, file_type):
    """
    process for writing output files for run_id to gcs bucket from an input string
    """

    storage_client = storage.Client.from_service_account_json('./ee-privatekey.json')
    bucket = storage_client.get_bucket(output_bucket_name)
    bucket.blob(output_file_name).upload_from_string(source, file_type)


def download_images():
    pass

if __name__ == "__main__":
    main()