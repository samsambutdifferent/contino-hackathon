# contino-hackathon

## Website Tree

```text
├── Dockerfile
├── html
│   └── index.html
└── nginx
    └── default.conf
```

### Build and deploy the container

```gcloud builds submit --tag eu.gcr.io/adtech-contino/hello```

```gcloud beta run deploy --image eu.gcr.io/adtech-contino/hello```

### Google Cloud Usage

* Google Cloud Run

* Google Maps Places API

* Google Maps Geocoding API
