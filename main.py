import argparse
import shutil

import requests
from tqdm import tqdm
import zipfile
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import glob
import json
import time
import webbrowser

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tkinter as tk
from tkinter import messagebox

def popup_msg(msg):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showinfo("信息", msg)
    root.destroy()

popup_msg("Hello, World! 这是一个弹出对话框喵。")

class StoppableHTTPServer(HTTPServer):
    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()


def LoadMods(mods_path):
    # Ensure the mods directory exists in the site directory
    mods_dir = os.path.join('site', 'mods')
    os.makedirs(mods_dir, exist_ok=True)
    print(f"ModPath: {mods_path}")

    # List of all mod file paths to be included in modlist.json
    mod_files_list = []

    # Copy "*.mod.zip" files from mods_path to site/mods directory
    for mod_file in glob.glob(os.path.join(mods_path, '**/*.mod.zip'), recursive=True):
        mod_file_name = os.path.basename(mod_file)
        dest_file = os.path.join(mods_dir, mod_file_name)
        shutil.copy(mod_file, dest_file)
        mod_files_list.append(f"mods/{mod_file_name}")
        print(f"Found Mod: {mod_file_name}")

    # Write the modlist.json file
    with open(os.path.join('site', 'modlist.json'), 'w') as json_file:
        json.dump(mod_files_list, json_file, indent=4)

    print("Mods loaded and modlist.json created successfully喵! 😸")


def StartServer(port):
    os.chdir('site')
    server = StoppableHTTPServer(('127.0.0.1', port), SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.run)
    server_thread.daemon = True
    server_thread.start()
    print(f"Starting HTTP server on port {port} with 'site' as the root directory喵! 🐾")
    print("Press Enter to stop the server喵.")
    time.sleep(1.5)  # 等待1.5秒
    webbrowser.open(f"http://127.0.0.1:{8080}")
    input()
    server.shutdown()
    server_thread.join()
    print("Server stopped喵! 😸")


def CheckAndDownloadDoLContent(check_only=False):
    # 如果只是检查，则不执行下载和解压操作

    if os.path.exists('site'):
        print("目录已存在，无需更新喵！🐾")
        return
    else:
        print("目录不存在，需要更新喵！😿")
        if check_only and os.path.exists('site/style.css'):
            return

    # GitHub API的URL
    api_url = "https://api.github.com/repos/Lyoko-Jeremie/DoLModLoaderBuild/releases/latest"

    # 发送请求获取最新的release数据
    response = requests.get(api_url)
    response.raise_for_status()  # 如果请求失败，将抛出异常

    # 解析JSON数据
    data = response.json()
    latest_version = data.get('tag_name', '')

    # 读取VERSION文件以检查已缓存的版本号
    cached_version = ''
    if os.path.exists('VERSION'):
        with open('VERSION', 'r') as version_file:
            cached_version = version_file.read().strip()

    # 检查版本号是否发生变化
    if cached_version == latest_version and os.path.exists('site/style.css'):
        print("当前版本已是最新，无需下载喵！🐾")
        return
    else:
        # 更新VERSION文件
        with open('VERSION', 'w') as version_file:
            version_file.write(latest_version)


    # 查找以"Dol"开头的zip文件
    zip_url = None
    for asset in data.get('assets', []):
        if asset['name'].startswith('DoL') and asset['name'].endswith('.zip'):
            zip_url = asset['browser_download_url']
            break

    if not zip_url:
        raise ValueError("未找到以'DoL'开头的zip文件喵！😿")

    # 下载zip文件，显示进度条
    response = requests.get(zip_url, stream=True)
    response.raise_for_status()

    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open('temp_dol.zip', 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        raise ValueError("下载时发生错误，文件大小不匹配喵！😿")

    # 创建 site 目录，如果它不存在的话
    if not os.path.exists('site'):
        os.mkdir('site')

    # 解压zip文件到 site 目录
    with zipfile.ZipFile('temp_dol.zip') as zip_ref:
        zip_ref.extractall('site')

    # 清理临时zip文件
    os.remove('temp_dol.zip')

    print(f"下载并解压最新版本 {latest_version} 完毕喵！🐾")

# 设置命令行参数
parser = argparse.ArgumentParser(description='检查并下载DolModLoader的内容')
parser.add_argument('-p', '--port', type=int, default=8080, help='指定HTTP服务的端口，默认为8080')
parser.add_argument('-r', action='store_true', help='是否检测最新版，设置这个选项时不会检测最新版')
parser.add_argument('--mods-path', help='Mods文件的路径，将从这里加载mods')

args = parser.parse_args()


# 根据参数调用函数
CheckAndDownloadDoLContent(check_only=args.r)


# If --mods-path is provided, call LoadMods
if args.mods_path:
    LoadMods(args.mods_path)
else:
    if os.path.exists(os.path.join('site', 'modlist.json')):
        os.remove(os.path.join('site', 'modlist.json'))

StartServer(port=args.port)
