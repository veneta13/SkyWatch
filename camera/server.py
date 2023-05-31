import base64
import json
import time

import cv2
import cvlib as cv
import urllib.request
import numpy as np

import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

from aws import \
    TOPIC, \
    CLIENT_ID, \
    ENDPOINT, \
    PATH_TO_AMAZON_ROOT_CA_1, \
    PATH_TO_PRIVATE_KEY, \
    PATH_TO_CERTIFICATE, \
    CAMERA_URL


def accept_photo():
    img_resp = urllib.request.urlopen(CAMERA_URL)
    img_read = img_resp.read()
    imgnp = np.array(bytearray(img_read), dtype=np.uint8)
    im = cv2.imdecode(imgnp, -1)

    _, labels, _ = cv.detect_common_objects(im)
    if 'person' in labels:
        return base64.b64encode(img_read).decode('utf-8')
    return None


def send_to_AWS(image):
    myAWSIoTMQTTClient.connect()
    message = {'encoded_img': image}
    myAWSIoTMQTTClient.publish(TOPIC, json.dumps(message), 1)
    print('Published')
    time.sleep(0.1)
    myAWSIoTMQTTClient.disconnect()


if __name__ == '__main__':
    myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(CLIENT_ID)
    myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
    myAWSIoTMQTTClient.configureCredentials(PATH_TO_AMAZON_ROOT_CA_1, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE)
    while True:
        image = accept_photo()
        if image is not None:
            send_to_AWS(image)
