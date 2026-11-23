"""Read fictional online storefront activity from Redis."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from redis import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

load_dotenv(Path(__file__).with_name('.env'), interpolate=False)

redis_host = os.getenv('REDIS_HOST')
if not redis_host:
    raise RuntimeError('Set REDIS_HOST in .env to your Redis Cloud endpoint hostname')

redis_tls = os.getenv('REDIS_TLS', 'true').lower()
if redis_tls not in {'true', 'false'}:
    raise RuntimeError('Set REDIS_TLS to true or false')

app = Flask(__name__)
STOREFRONT_ACTIVITY_KEY = 'supply_lab:storefront_activity'
redis_client = Redis(
    host=redis_host,
    port=int(os.getenv('REDIS_PORT', '6379')),
    db=int(os.getenv('REDIS_DB', '0')),
    username=os.getenv('REDIS_USERNAME', 'default'),
    password=os.getenv('REDIS_PASSWORD'),
    ssl=redis_tls == 'true',
    ssl_check_hostname=True,
    ssl_ca_certs=os.getenv('REDIS_CA_FILE') or None,
    socket_connect_timeout=2,
    socket_timeout=2,
    retry=Retry(NoBackoff(), 0),
)


def activity_field(location: str, year: int) -> str:
    return f'{location.strip().casefold()}:{year}'


@app.get('/statistics/storefront_activity')
def statistics():
    location = request.args.get('location', '').strip()
    year = request.args.get('year', type=int)
    if not location or len(location) > 100:
        return jsonify(error='location must contain 1 to 100 characters'), 400
    if year is None or not 1 <= year <= 9998:
        return jsonify(error='year must be an integer between 1 and 9998'), 400

    field = activity_field(location, year)
    try:
        raw_value = redis_client.hget(STOREFRONT_ACTIVITY_KEY, field)
    except RedisError:
        app.logger.exception('Redis storefront activity lookup failed')
        return jsonify(error='Redis unavailable'), 503

    if raw_value is None:
        return jsonify(error='No storefront activity found for that location and year'), 404
    try:
        activity = json.loads(raw_value)
    except ValueError:
        app.logger.error('Redis contains invalid storefront activity data')
        return jsonify(error='Invalid storefront activity data in Redis'), 503

    return jsonify(activity=activity, synthetic=True)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002)
