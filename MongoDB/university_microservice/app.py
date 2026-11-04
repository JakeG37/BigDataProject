"""HTTP client -> Flask -> Atlas sample_supplies.sales."""
from datetime import datetime, timezone
from decimal import Decimal
import re

from bson import ObjectId
from bson.decimal128 import Decimal128
from flask import Flask, jsonify, request
from pymongo.errors import PyMongoError

from db import collection

app = Flask(__name__)


def json_ready(value):
    """Convert nested BSON values without losing decimal price precision."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (Decimal128, Decimal)):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    return value


@app.get('/sales')
def sales():
    """Example: GET /sales?location=Seattle&year=2015&limit=5"""
    location = request.args.get('location', '').strip()
    year_text = request.args.get('year', '').strip()
    method = request.args.get('purchase_method', '').strip()
    if not location or len(location) > 100:
        return jsonify(error='location must contain 1 to 100 characters'), 400
    if method and method not in {'Online', 'Phone', 'In store'}:
        return jsonify(error='purchase_method must be Online, Phone, or In store'), 400
    try:
        limit = int(request.args.get('limit', '5'))
        if not 1 <= limit <= 100:
            raise ValueError
    except ValueError:
        return jsonify(error='limit must be an integer between 1 and 100'), 400

    query = {'storeLocation': {'$regex': f'^{re.escape(location)}$', '$options': 'i'}}
    if year_text:
        try:
            year = int(year_text)
            if not 1 <= year <= 9998:
                raise ValueError
        except ValueError:
            return jsonify(error='year must be an integer between 1 and 9998'), 400
        # The dataset has saleDate, not a separate year field.
        query['saleDate'] = {
            '$gte': datetime(year, 1, 1, tzinfo=timezone.utc),
            '$lt': datetime(year + 1, 1, 1, tzinfo=timezone.utc),
        }
    if method:
        query['purchaseMethod'] = method
    try:
        records = list(collection.find(query).sort([('saleDate', -1), ('_id', 1)]).limit(limit))
    except PyMongoError:
        app.logger.exception('Sales query failed')
        return jsonify(error='Database unavailable'), 503
    return jsonify(count=len(records), limit=limit, sales=json_ready(records))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
