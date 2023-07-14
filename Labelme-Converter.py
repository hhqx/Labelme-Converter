import datetime
from queue import Queue
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading

from labelme_tools import create_json_zip, export_labelme_format_pairs


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        # 创建控件
        self.pack()
        self.create_widgets()

        self.dir_json = None
        self.dir_img = None
        self.path_jsonzip = None

        # self.dir_json = r'../Converter_output\OUTER'
        # self.dir_img = r'../OUTER'

        # 定义log_queue
        self.log_queue = Queue()

        self.updater = threading.Thread(target=self.update_log, daemon=True)
        self.updater.start()

    def warning(self, text):
        messagebox.showwarning('警告', text)

    def get_threaded(self, func):
        """ 返回线程修饰过的函数 """

        def f():
            thread = threading.Thread(target=func, daemon=True)
            thread.start()

        return f

    def create_widgets(self):
        # 创建选择JSON目录的控件
        self.dir_json_frame = tk.Frame(self)
        self.dir_json_frame.pack(side="top", pady=5)
        self.dir_json_label = tk.Label(self.dir_json_frame, text="选择JSON文件目录：")
        self.dir_json_label.pack(side="left")
        # self.dir_json_button = tk.Button(self.dir_json_frame, text="选择", command=self.select_json_directory)
        self.dir_json_button = tk.Button(self.dir_json_frame, text="选择",
                                         command=self.get_threaded(self.select_json_directory))
        self.dir_json_button.pack(side="left")

        # 创建选择图像目录的控件
        self.dir_img_frame = tk.Frame(self)
        self.dir_img_frame.pack(side="top", pady=5)
        self.dir_img_label = tk.Label(self.dir_img_frame, text="选择图像文件目录：")
        self.dir_img_label.pack(side="left")
        self.dir_img_button = tk.Button(self.dir_img_frame, text="选择",
                                        command=self.get_threaded(self.select_img_directory))
        self.dir_img_button.pack(side="left")

        # 创建导出json的控件
        self.json_zip_frame = tk.Frame(self)
        self.json_zip_frame.pack(side="top", pady=5)
        self.json_zip_label = tk.Label(self.json_zip_frame, text="导出json压缩包：")
        self.json_zip_label.pack(side="left")
        self.json_zip_button = tk.Button(self.json_zip_frame, text="输入",
                                         command=self.get_threaded(self.export_json_zip))
        self.json_zip_button.pack(side="left")

        # 创建运行按钮
        self.run_button = tk.Button(self, text="运行", bg="green", command=self.get_threaded(self.run_export))
        self.run_button.pack(side="top", pady=10, fill=tk.BOTH, expand=True)

        # 创建输出log的窗口
        self.log_output = ScrolledText(self.master, height=20)
        self.log_output.pack(side="top", pady=5)

    def print(self, text):
        self.log_queue.put(text)

    def update_log(self):
        cache = []
        while not self.log_queue.empty():
            text = self.log_queue.get()
            cache.append(text)
        if cache:
            self.log_output.insert(tk.END, '\n'.join(cache) + '\n')
            self.log_output.see(tk.END)
        self.after(500, self.update_log)
        current_time = datetime.datetime.now()
        print("Current time is:", current_time)

    def select_json_directory(self):
        # 打开文件选择对话框并获取选择的目录路径
        self.dir_json = filedialog.askdirectory()
        self.dir_json_label.config(text="选择JSON文件目录：" + self.dir_json)

    def select_img_directory(self):
        # 打开文件选择对话框并获取选择的目录路径
        self.dir_img = filedialog.askdirectory()
        self.dir_img_label.config(text="选择图像文件目录：" + self.dir_img)

    def export_json_zip(self):
        if not self.dir_json:
            # 弹出一个警告框
            self.warning('请先选择要保存的json文件目录！')
            return

        # 弹出一个对话框，让用户选择zip文件的保存路径和名称
        zip_file_path = filedialog.asksaveasfilename(defaultextension='.zip', filetypes=[('Zip files', '*.zip')])
        self.path_jsonzip = zip_file_path
        self.json_zip_label.config(text="导出json压缩包：" + zip_file_path)

        # 如果用户取消了对话框，则退出函数
        if not zip_file_path:
            return
        self.print("保存到: {}".format(zip_file_path))

        create_json_zip(self.dir_json, self.path_jsonzip, log_func=self.print)

    def run_export(self):
        for name, para in [('json', self.dir_json), ('img', self.dir_img)]:
            if not para:
                # 弹出一个警告框
                self.warning(f'请先选择要保存的{name}文件目录！')
                return

        # 调用export_labelme_format_pairs函数并将输出写入log窗口
        # self.log_output.delete(1.0, tk.END)  # 清空 Text 文本
        self.print("开始转换...\n")
        try:
            export_labelme_format_pairs(self.dir_img, self.dir_json, log_func=self.print)
            self.print("转换完成！\n")
        except Exception as e:
            self.print("转换失败：" + str(e) + "\n")


# 创建主窗口并启动GUI
root = tk.Tk()
root.title("LabelMe Converter")
# 读取ICO图标文件
icon_path = os.path.join(os.path.dirname(__file__), 'resources/icon.ico')
root.iconbitmap(default=icon_path)
root.update()
app = Application(master=root)
app.mainloop()

"""
# 打包命令: 
# pip install pyinstaller
pyinstaller --onefile --windowed --icon resources/icon.ico --add-data "resources/icon.ico;./resources/" Labelme-Converter.py

"""
