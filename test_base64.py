

import json
import cv2
import numpy as np
import base64

def b642img(imagedata: str):
    img_bytes = base64.b64decode(imagedata)
    img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    return img
def img2b64(img):
    retval, buffer = cv2.imencode('.jpg', img)
    b64_img = base64.b64encode(buffer)
    return b64_img.decode()

# 读取json文件
with open('test_labelme/folder1/1820.json', 'r') as f:
    annotation = json.load(f)

# 获取imagedata
imagedata = annotation['imageData']

# 将imagedata转换为图像
# img = cv2.imdecode(np.fromstring(imagedata, np.uint8), cv2.IMREAD_COLOR)
img = b642img(imagedata)
s_img = img2b64(img)
assert s_img == imagedata

# 获取所有标注的形状
shapes = annotation['shapes']

# 遍历每个形状并画出bbox
for shape in shapes:
    points = shape['points']
    x1, y1 = int(points[0][0]), int(points[0][1])
    x2, y2 = int(points[1][0]), int(points[1][1])
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

# 显示图像
cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()