"""Shared MongoDB configuration. Credentials belong in .env."""
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).with_name('.env'))

uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI')
if not uri:
    raise RuntimeError('Set MONGO_URI or MONGODB_URI in the .env file beside db.py')

# Accept separate credentials too; PyMongo handles their encoding.
credentials = {}
if os.getenv('MONGODB_USERNAME') and os.getenv('MONGODB_PASSWORD'):
    credentials = {
        'username': os.environ['MONGODB_USERNAME'],
        'password': os.environ['MONGODB_PASSWORD'],
    }
client = MongoClient(uri, serverSelectionTimeoutMS=5000, **credentials)
collection = client[os.getenv('MONGO_DB', 'sample_supplies')][os.getenv('MONGO_COLLECTION', 'sales')]
