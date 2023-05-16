import csv
import boto3
from datetime import datetime
import dateutil


TABLE = ''
BUCKET = ''
TEMP_LOCATION = ''
REGION = ''


def scan_table(previous_response=None):
    table = boto3.resource(
        'dynamodb',
        region_name=REGION
    ).Table(
        TABLE
    )

    if previous_response is not None:
        return table.scan(
            ExclusiveStartKey=previous_response['LastEvaluatedKey']
        )
    else:
        return table.scan()


def add_to_bucket():
    boto3.resource(
        's3',
        region_name=REGION
    ).Bucket(
        BUCKET
    ).upload_file(
        TEMP_LOCATION,
        'dynamo_backup/' + str(
            datetime.now(
                dateutil.tz.gettz('Europe/Sofia')
            ).isoformat()
        ) + '.csv'
    )


def lambda_handler(event, context):
    with open(TEMP_LOCATION, 'w') as output_file:
        writer = csv.writer(output_file)
        is_start = True

        response = {'LastEvaluatedKey': []}

        while 'LastEvaluatedKey' in response:
            if is_start:
                response = scan_table()
            else:
                response = scan_table(response)
            for item in response['Items']:
                if is_start:
                    writer.writerow(item.keys())
                is_start = False
                writer.writerow(item.values())

    add_to_bucket()
