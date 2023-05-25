import base64
import boto3
import json
import uuid
from datetime import datetime
import dateutil


QUEUE = ''
BUCKET = ''
TOPIC = ''
TABLE = ''
REGION = ''


def get_messages():
    return boto3.client(
        'sqs',
        region_name=REGION
    ).receive_message(
        QueueUrl=QUEUE,
        MaxNumberOfMessages=1
    )


def delete_message(receipt_handle):
    return boto3.client(
        'sqs',
        region_name=REGION
    ).delete_message(
        QueueUrl=QUEUE,
        ReceiptHandle=receipt_handle
    )


def write_picture(sqs_messages):
    pic_uuid = str(uuid.uuid4())
    pic_path = f'/tmp/{pic_uuid}.jpg'

    encoded_image = base64.b64decode(
        json.loads(
            sqs_messages['Messages'][0]['Body']
        )['encoded_img']
    )

    with open(pic_path, 'wb') as f:
        f.write(encoded_image)

    return pic_uuid, pic_path


def run_rekognition(pic_path):
    with open(pic_path, 'rb') as image:
        return boto3.client(
            'rekognition',
            region_name=REGION
        ).detect_labels(
            Image={
                'Bytes': image.read()
            },
            MaxLabels=10,
        )['Labels']


def detect_person(pic_path):
    rekognition_labels = run_rekognition(pic_path)

    is_person = False
    for label in rekognition_labels:
        label_name = label['Name'].lower()
        label_confidence = label['Confidence']

        if label_name in ['human', 'person'] and label_confidence >= 90:
            is_person = True
    return is_person, rekognition_labels


def add_to_dynamoDB(pic_uuid, labels, pic_path):
    table = boto3.resource(
        'dynamodb',
        region_name=REGION
    ).Table(TABLE)

    table.put_item(
        Item={
            'timestamp': str(datetime.now(
                            dateutil.tz.gettz('Europe/Sofia')
                        ).isoformat()),
            'picID': pic_uuid,
            'pic_path': pic_path,
            'rekognition_result': [
                ','.join([label['Name'], str(label['Confidence'])])
                for label
                in labels
            ]
        }
    )


def add_to_bucket(img, pic_path):
    boto3.client(
        's3',
        region_name=REGION
    ).upload_file(
        img,
        BUCKET,
        pic_path
    )


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
        Message=f'A person was detected!'
                f'\nFor more information: {get_public_url(img_path)}'
    )


def lambda_handler(event, context):
    sqs_messages = get_messages()

    if "Messages" in sqs_messages:
        pic_uuid, pic_path = write_picture(sqs_messages)
        is_person, rekognition_labels = detect_person()

        if is_person:
            saved_pic_path = pic_path.replace("/tmp/", "people/")
            add_to_dynamoDB(
                pic_uuid=pic_uuid,
                pic_path=saved_pic_path,
                labels=rekognition_labels
            )
            add_to_bucket(
                img=pic_path,
                pic_path=saved_pic_path
            )
            publish_to_topic(
                saved_pic_path
            )
        delete_message(sqs_messages['Messages'][0]['ReceiptHandle'])
    else:
        print("No pictures in queue")
