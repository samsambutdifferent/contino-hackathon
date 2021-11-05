import os
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS

# Imports the Google Cloud client library
from google.cloud import storage

# Instantiates a client
storage_client = storage.Client()


load_dotenv()

app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={
    r"/*": {
        "origins": "*"
    }
},
headers='Content-Type')


@app.route("/helloworld")
def helloworld():
    print("hello world")
    return "hello world"


@app.route("/", methods=["POST"])
def land_classifier():

    request_obj = request.get_json()
    N = request_obj.get("N")
    W = request_obj.get("W")
    Location = request_obj.get("location")

    bucket_name = "ee-current-images"
    bucket=storage_client.get_bucket(bucket_name)
    # List all objects that satisfy the filter.
    
    delimiter="/"
    folder="./"

    blobs=bucket.list_blobs(prefix=Location, delimiter=delimiter)

    image_url = ""
    for blob in blobs:
        print("Blobs: {}".format(blob.name))
        # destination_uri = "{}/{}".format(folder, blob.name) 
        # blob.download_to_filename(destination_uri)

        image_url = blob.public_url

    return (image_url, 200)
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)