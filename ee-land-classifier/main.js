
const ee = require('@google/earthengine');
const PRIVATE_KEY = require('./privatekey.json');

x = 121.4737
y = 31.2304
year_start = "2011"
year_end = "2013"

ee.data.authenticateViaPrivateKey(PRIVATE_KEY, () => {
  ee.initialize(null, null, () => {

    var roi = ee.Geometry.Point(x, y);

    // Load Landsat 5 input imagery.
    var landsat = ee.Image(ee.ImageCollection('LANDSAT/LT05/C01/T1_TOA')
      // Filter to get only one year of images.
      .filterDate('${year_start}-01-01', '${year_end}-12-31')
      // Filter to get only images under the region of interest.
      .filterBounds(roi)
      // Sort by scene cloudiness, ascending.
      .sort('CLOUD_COVER')
      // Get the first (least cloudy) scene.
      .first());
    
    // Compute cloud score.
    var cloudScore = ee.Algorithms.Landsat.simpleCloudScore(landsat).select('cloud');
    
    // Mask the input for clouds.  Compute the min of the input mask to mask
    // pixels where any band is masked.  Combine that with the cloud mask.
    var input = landsat.updateMask(landsat.mask().reduce('min').and(cloudScore.lte(50)));
    
    // Use MODIS land cover, IGBP classification, for training.
    var modis = ee.Image('MODIS/051/MCD12Q1/2011_01_01')
        .select('Land_Cover_Type_1');
    
    // Sample the input imagery to get a FeatureCollection of training data.
    var training = input.addBands(modis).sample({
      numPixels: 5000,
      seed: 0
    });
    
    // Make a Random Forest classifier and train it.
    var classifier = ee.Classifier.smileRandomForest(10)
        .train({
          features: training,
          classProperty: 'Land_Cover_Type_1',
          inputProperties: ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
        });
    
    // Classify the input imagery.
    var classified = input.classify(classifier);
    
    // Get a confusion matrix representing resubstitution accuracy.
    var trainAccuracy = classifier.confusionMatrix();
    console.log('Resubstitution error matrix: ', trainAccuracy);
    console.log('Training overall accuracy: ', trainAccuracy.accuracy());
    
    // Sample the input with a different random seed to get validation data.
    var validation = input.addBands(modis).sample({
      numPixels: 5000,
      seed: 1
      // Filter the result to get rid of any null pixels.
    }).filter(ee.Filter.neq('B1', null));
    
    // Classify the validation data.
    var validated = validation.classify(classifier);
    
    // Get a confusion matrix representing expected accuracy.
    var testAccuracy = validated.errorMatrix('Land_Cover_Type_1', 'classification');
    console.log('Validation error matrix: ', testAccuracy);
    console.log('Validation overall accuracy: ', testAccuracy.accuracy());
    
    // Define a palette for the IGBP classification.
    var igbpPalette = [
      'aec3d4', // water
      '152106', '225129', '369b47', '30eb5b', '387242', // forest
      '6a2325', 'c3aa69', 'b76031', 'd9903d', '91af40',  // shrub, grass
      '111149', // wetlands
      'cdb33b', // croplands
      'cc0013', // urban
      '33280d', // crop mosaic
      'd7cdcc', // snow and ice
      'f7e084', // barren
      '6f6f6f'  // tundra
    ];
    
    // Display the input and the classification.
    // Map.centerObject(roi, 10);
    // Map.addLayer(input, {bands: ['B3', 'B2', 'B1'], max: 0.4}, 'landsat');
    // Map.addLayer(classified, {palette: igbpPalette, min: 0, max: 17}, 'classification');


  });
});
