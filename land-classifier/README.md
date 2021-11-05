# Land Classifier

## Local Setup

### GCLOUD auth

```bash
gcloud auth login
or
gcloud auth application-default login
```

### Virtual environment

Create a virtual environment and install the relevant packages

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Run
Execute the following command to start the Flask app on '127.0.0.1:5000/'

```bash
python app/app.py
```

## Environmet variables

Local env variables are read in through the .env file at the root of each function. 

Uses the python-dotenv framework. Use:

```python
from dotenv import load_dotenv
load_dotenv()

variable_name = os.environ.get('Env_Var_Name', 'Specified environment variable is not set.')
```

More info: <https://pypi.org/project/python-dotenv/>

NOTE env vars for cloud are set in the app.yaml file

### Manual Deployment

```bash

sudo docker build -t land-classifier . --no-cache

docker tag land-classifier gcr.io/adtech-contino/land-classifier

docker push gcr.io/adtech-contino/land-classifier

# gcloud builds submit --tag gcr.io/adtech-contino/land-classifier

gcloud run deploy land-classifier --image gcr.io/adtech-contino/land-classifier --platform managed --region europe-west1
```

