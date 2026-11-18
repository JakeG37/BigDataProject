"""Read the demo application's active-user count from Redis."""
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
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


@app.get('/statistics/<key>')
def statistics(key: str):
    if key != 'active_users':
        return jsonify(error='Unsupported statistic'), 404

    try:
        raw_value = redis_client.get('active_users')
    except RedisError:
        app.logger.exception('Redis statistic lookup failed')
        return jsonify(error='Redis unavailable'), 503

    if raw_value is None:
        return jsonify(error='Active-user count has not been set in Redis'), 404
    try:
        value = int(raw_value)
        if value < 0:
            raise ValueError
    except ValueError:
        app.logger.error('Redis contains an invalid active-user count')
        return jsonify(error='Invalid active-user count in Redis'), 503

    return jsonify(key=key, value=value)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002)
