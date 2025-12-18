import os
from elasticsearch import Elasticsearch

ES_HOST = os.environ.get("ES_HOST", "http://disasterlens_es:9200")
ES_CLIENT = Elasticsearch(ES_HOST)

def create_indexes():
    # 1. Index for Social Media Posts
    es.indices.create(index="posts", body={
        "mappings": {
            "properties": {
                "post_text": {"type": "text"},
                "disaster_type": {"type": "keyword"},
                "start_time": {"type": "date"},
                "location": {
                    "properties": {
                        "state": {"type": "keyword"},
                        "district": {"type": "keyword"},
                        "lat_lon": {"type": "geo_point"} # Important! [lon, lat]
                    }
                }
            }
        }
    }, ignore=400)

    # 2. Index for Consolidated Events
    es.indices.create(index="events", body={
        "mappings": {
            "properties": {
                "classification_type": {"type": "keyword"},
                "location_state": {"type": "keyword"},
                "start_time": {"type": "date"},
                "geometry": {
                    "properties": {
                        "coordinates": {"type": "geo_point"}
                    }
                }
            }
        }
    }, ignore=400)

if __name__ == "__main__":
    create_indexes()