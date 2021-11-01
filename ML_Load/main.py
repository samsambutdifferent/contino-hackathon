import re
import ee
import folium
import geehydro
import json

service_account = ' ee-service-account@adtech-contino.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, './ee-privatekey.json')
keys = ["year","roi","water","forest","shrub, grass","wetlands","croplands","urban","crop mosaic","snow and ice","barren","tundra"]
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

        area_classified = ee.Image.pixelArea().divide(1e6).addBands(classified).reduceRegion(
            reducer= ee.Reducer.sum().group(1, 'group'),
            geometry= landsat.geometry(),
            scale= 1000
        )

        outputReducers = ee.List(area_classified.get('groups'))
        get_groups = area_classified.getInfo()
        group_dict ={'year':year, 'roi':', '.join(map(str, input_point))}
        group_dict.update({groups[int(x['group'])]:x['sum'] for x in get_groups['groups']})

        result = keys - group_dict.keys()
        for r in result:
            group_dict[r] = 0.0

        json_to_write.extend([group_dict])

    write_blob_from_string(
        json.dumps(json_to_write),
        "ml_load",
        "landsat_07_historical",
        "text/json",
    )

    from google.cloud import bigquery

    # Construct a BigQuery client object.
    #service_account = ' ee-service-account@adtech-contino.iam.gserviceaccount.com'
    #credentials = ee.ServiceAccountCredentials(service_account, './ee-privatekey.json')
    client = bigquery.Client.from_service_account_json('./ee-privatekey.json')

    table_id = "adtech-contino.hackathon.landsat-07-historical"

    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("year", "INTEGER"),
            bigquery.SchemaField("roi", "STRING"),
            bigquery.SchemaField("water", "DECIMAL"),
            bigquery.SchemaField("forest", "DECIMAL"),
            bigquery.SchemaField("shrub_grass", "DECIMAL"),
            bigquery.SchemaField("wetlands", "DECIMAL"),
            bigquery.SchemaField("croplands", "DECIMAL"),
            bigquery.SchemaField("urban", "DECIMAL"),
            bigquery.SchemaField("crop_mosaic", "DECIMAL"),
            bigquery.SchemaField("snow_ice", "DECIMAL"),
            bigquery.SchemaField("barren", "DECIMAL"),
            bigquery.SchemaField("tundra", "DECIMAL")
        ],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    uri = "gs://ml_load/landsat_07_historical.json"

    load_job = client.load_table_from_uri(
        uri,
        table_id,
        job_config=job_config,
    )  # Make an API request.

    load_job.result()  # Waits for the job to complete.

    destination_table = client.get_table(table_id)
    print("Loaded {} rows.".format(destination_table.num_rows))

from google.cloud import storage

def write_blob_from_string(source, output_bucket_name, output_file_name, file_type):
    """
    process for writing output files for run_id to gcs bucket from an input string
    """

    storage_client = storage.Client.from_service_account_json('./ee-privatekey.json')
    bucket = storage_client.get_bucket(output_bucket_name)
    bucket.blob(output_file_name).upload_from_string(source, file_type)


if __name__ == "__main__":
    main()