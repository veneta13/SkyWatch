import boto3


BUCKET = ''
TOPIC = ''
REGION = ''


def last_updated_file():
    paginator = boto3.client(
        's3'
    ).get_paginator(
        "list_objects_v2"
    ).paginate(
        Bucket=BUCKET
    )

    result = None
    for page in paginator:
        if "Contents" in page:
            obj = sorted(
                page['Contents'],
                key=lambda x: x['LastModified']
            )[-1]
            if result is None or obj['LastModified'] > result['LastModified']:
                result = obj
    return result['Key']


def get_public_url(file):
    return boto3.client(
        's3',
        region_name=REGION
    ).generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': BUCKET,
            'Key': file
        },
        ExpiresIn=86400
    )


def publish_to_topic(img_path):
    boto3.client(
        'sns',
        region_name=REGION
    ).publish(
        TopicArn=TOPIC,
        Message=f'Weekly backup of dynamoDB is now available.'
                f'\nFor more information: {get_public_url(img_path)}'
    )


def lambda_handler(event, context):
    file_key = last_updated_file()
    publish_to_topic(file_key)
