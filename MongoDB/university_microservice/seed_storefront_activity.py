"""Load fictional store website activity into the configured Redis database."""
import json
from pathlib import Path

from redis_app import STOREFRONT_ACTIVITY_KEY, activity_field, redis_client


def main():
    fixture = Path(__file__).with_name('storefront_activity.json')
    rows = json.loads(fixture.read_text(encoding='utf-8'))

    with redis_client.pipeline() as batch:
        for row in rows:
            field = activity_field(row['location'], row['year'])
            batch.hsetnx(STOREFRONT_ACTIVITY_KEY, field, json.dumps(row))
        inserted = sum(batch.execute())

    print(f'Storefront activity: {inserted} rows added, {len(rows) - inserted} already present.')


if __name__ == '__main__':
    main()
