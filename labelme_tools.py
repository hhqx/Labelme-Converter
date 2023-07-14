import time
from datetime import timedelta
from io import BytesIO
from PIL import Image
import json
import cv2
import numpy as np
import base64
import shutil
import glob
from builtins import print as print_std
import os
import tempfile
import zipfile


def b642img(imagedata: str):
    img_bytes = base64.b64decode(imagedata)
    img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    return img


def img2b64(img):
    retval, buffer = cv2.imencode('.jpg', img)
    b64_img = base64.b64encode(buffer)
    return b64_img.decode()


def imgfile2b64(path, quality=75):
    # 打开图像文件并读取二进制数据
    with open(path, 'rb') as f:
        img_data = f.read()

    # 将二进制图像数据转换为Image对象
    img = Image.open(BytesIO(img_data))
    W, H = img.size

    # 将Image对象转换为Base64编码
    # 创建BytesIO对象，用于保存JPEG图像数据
    img_buffer = BytesIO()

    # 以指定质量级别保存JPEG图像数据到BytesIO对象
    img_jpeg = img.convert('RGB')
    img_jpeg.save(img_buffer, 'JPEG', quality=quality)

    # 获取JPEG图像数据并进行Base64编码
    img_data_jpeg = img_buffer.getvalue()
    b64_data = base64.b64encode(img_data_jpeg).decode('utf-8')

    # # 打印Base64编码的数据和压缩质量级别
    # print('Quality {0}: {1}'.format(quality, b64_data))
    return b64_data, (H, W)


def get_json(file='test_labelme/folder1/1820.json'):
    with open(file, 'r', encoding='utf-8') as f:
        annotation = json.load(f)
    return annotation


def save_json(file, json_data):
    with open(file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(json_data, indent=4))
    return True


def get_file_name_without_extension(file_path):
    """
    获取文件名（不包含扩展名）
    :param file_path: 文件路径
    :return: 文件名（不包含扩展名）
    """
    # 获取文件名（包含扩展名）
    file_name_with_extension = os.path.basename(file_path)

    # 分离文件名和扩展名
    file_name, file_extension = os.path.splitext(file_name_with_extension)

    return file_name


def get_image_paths(directory):
    """
    获取目录中所有图片文件的路径
    :param directory: 目录路径
    :return: 包含所有图片文件路径的列表
    """
    # 定义支持的图像文件扩展名
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp")

    # 生成包含所有图像文件路径的列表
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(directory, "**", ext), recursive=True))

    return image_paths


def get_wrapped_print(print_func, log_func):
    def wrapped_print(*args, **kwargs):
        print_func(*args, **kwargs)
        log_func(" ".join(map(str, args)))

    return wrapped_print


def add_img_to_json(p, db_img, ):
    json_data = get_json(p)

    name = get_file_name_without_extension(p)
    des_path = os.path.join(os.path.dirname(p), name + ".jpg")

    img_path = db_img.get(name, "")
    if not img_path:
        return None
    # img = cv2.imread(img_path)
    # H, W = img.shape[:2]
    # img_b64 = img2b64(img)
    img_b64, (H, W) = imgfile2b64(img_path)
    shutil.copy(img_path, des_path)
    json_data['imageData'] = img_b64
    json_data['imagePath'] = os.path.basename(des_path)
    json_data['imageWidth'] = W
    json_data['imageHeight'] = H
    info = "Copy file: '{}' To '{}' \nAdd image data to: {}".format(img_path, des_path, des_path)

    return json_data, [info]


def export_labelme_format_pairs(dir_img, dir_json, log_func=None):
    print = get_wrapped_print(print_std, log_func) if log_func else print_std
    origin_jsons = glob.glob(os.path.join(dir_json, '**/*.json'), recursive=True)
    db_imgs = get_image_paths(dir_img)
    name2img = {get_file_name_without_extension(p): p for p in reversed(db_imgs)}

    total_cnt = len(origin_jsons)
    start = time.time()
    for i, p in enumerate(origin_jsons):
        json_out, info = add_img_to_json(p, name2img)
        status = save_json(p, json_out)
        remain = (time.time() - start) * (total_cnt - i - 1) / (i + 1)
        print("\n".join(info))
        print("iter: {1}/{2}, time remaining: {0}\n".format(timedelta(seconds=remain), i + 1, total_cnt))

    return True


def remove_imageData_from_jsonFile(p):
    json_data = get_json(p)
    json_data['imageData'] = ""
    return json_data


def create_json_zip(dir_json, zip_file, exts=['.json'], log_func=None):
    print = get_wrapped_print(print_std, log_func) if log_func else print_std
    json_path_list = []
    for ext in exts:
        json_path_list.extend(glob.glob(os.path.join(dir_json, f'**/*{ext}'), recursive=True))

    cnt = len(json_path_list)
    # 创建一个zip文件对象
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历json数据列表
        start = time.time()
        for i, p in enumerate(json_path_list):
            name = os.path.basename(p)
            json_data = remove_imageData_from_jsonFile(p)
            json_str = json.dumps(json_data, indent=4)

            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=exts[0], delete=False) as tmpf:
                # 将json数据写入临时文件中
                tmpf.write(json_str.encode('utf-8'))
                tmpf.close()

                # 将临时文件添加到zip压缩包中
                # tmp_name = f'jsons/{name}'
                tmp_name = os.path.normpath(os.path.relpath(p, os.path.dirname(dir_json)))
                zipf.write(tmpf.name, tmp_name)

                # 删除临时文件
                os.remove(tmpf.name)

            remain = (time.time() - start) * (len(json_path_list) - i - 1) / (i + 1)
            print("iter: {1}/{2}, time remaining: {0}".format(timedelta(seconds=remain), i + 1, len(json_path_list)))
            # print(i, cnt)

    print("压缩完成！")


def create_img_zip(dir_json, zip_file, exts=['.jpg'], log_func=None):
    print = get_wrapped_print(print_std, log_func) if log_func else print_std
    json_path_list = []
    for ext in exts:
        json_path_list.extend(glob.glob(os.path.join(dir_json, f'**/*{ext}'), recursive=True))

    # 创建一个zip文件对象
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历json数据列表
        start = time.time()
        for i, p in enumerate(json_path_list):
            # 将临时文件添加到zip压缩包中
            tmp_name = os.path.normpath(os.path.relpath(p, os.path.dirname(dir_json)))
            zipf.write(p, tmp_name)
            remain = (time.time() - start) * (len(json_path_list) - i - 1) / (i + 1)
            print("iter: {1}/{2}, time remaining: {0}".format(timedelta(seconds=remain), i + 1, len(json_path_list)))

    print("压缩完成！")


if __name__ == '__main__':
    dir_json = 'test_gui'
    # dir_json = 'json'
    dir_img = 'image_database'

    # create_json_zip(dir_json, 'test_labelme.zip')

    # create zip of images
    # create_json_zip('../OUTER', '../OUTER_Jsons.zip')
    # create_img_zip('../OUTER', '../OUTER_Images.zip', exts=['.jpg', '.jpeg'])

    export_labelme_format_pairs('../OUTER', '../Converter_output/OUTER')
    exit(0)
