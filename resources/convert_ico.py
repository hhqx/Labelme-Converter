from PIL import Image

# 加载JPG图像文件
image = Image.open("images.jpg")

# 转换图像大小
image = image.resize((256, 256))
# image = image.resize((16, 16))

# 保存为ICO图标文件
image.save("../icon.ico", format="ICO")