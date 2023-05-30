import cv2
import cvlib as cv
import urllib.request
import numpy as np

url = 'http://192.168.83.153/cam-mid.jpg'
im = None


if __name__ == '__main__':
    while True:
        img_resp = urllib.request.urlopen(url)
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        im = cv2.imdecode(imgnp, -1)

        bbox, label, conf = cv.detect_common_objects(im)
        print(label, conf)