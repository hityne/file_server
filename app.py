import os, sys
from flask import Flask, render_template, send_from_directory, abort, request, current_app
from builtins import len  # 导入 len 函数
import time

app = Flask(__name__)

def get_directory_contents(directory):
    """
    获取目录下的文件和文件夹列表

    Args:
        directory (str): 目录路径

    Returns:
        tuple: 包含文件和文件夹信息的字典列表
    """
    files = []
    folders = []
    try:
        for entry in os.listdir(directory):
            if entry.startswith('.'):  # 跳过以 . 开头的文件和文件夹
                continue

            entry_path = os.path.join(directory, entry)
            if os.path.isfile(entry_path):
                file_stats = os.stat(entry_path)
                files.append({
                    'name': entry,
                    'size': f"{file_stats.st_size / 1024:.2f} KB",
                    'mtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_stats.st_mtime)),  # 添加修改时间
                    'path': entry_path
                })
            elif os.path.isdir(entry_path):
                folders.append({
                    'name': entry,
                    'path': entry_path
                })
    except PermissionError:
        print(f"权限错误：无法访问目录 {directory}")
    except OSError as e:
        print(f"读取目录时发生错误: {e}")

    return files, folders

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def browse_files(path):
    """
    浏览文件和文件夹
    
    Args:
        path (str): 要浏览的相对路径
    
    Returns:
        str: 渲染的HTML页面
    """
    current_directory = os.path.join(app.config['DOWNLOAD_FOLDER'], path)
    
    # 检查目录是否存在且为目录
    if not os.path.exists(current_directory):
        return "指定的目录不存在", 404
    if not os.path.isdir(current_directory):
        return "指定的路径不是一个目录", 404
    
    files, folders = get_directory_contents(current_directory)
    
    return render_template('file_list.html', files=files, folders=folders, current_path=path, app=current_app)


@app.route('/download/<path:filename>')
def download_file(filename):
    """
    下载文件
    
    Args:
        filename (str): 要下载的文件名
    
    Returns:
        文件下载响应
    """
    directory = app.config['DOWNLOAD_FOLDER']
    filename = filename.replace("\\", "/")  # 将反斜杠替换为正斜杠
    filepath = os.path.normpath(os.path.join(directory, filename))
    print(f"filename: {filename}")  # 打印 filename
    print(f"filepath: {filepath}")  # 打印 filepath
    
    # 安全检查：确保下载文件在指定目录内
    if not filepath.startswith(directory):
        abort(403)  # forbidden
    
    try:
        print('here')
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        return "文件未找到", 404


if __name__ == '__main__':
    # 检查是否提供了目录路径参数
    if len(sys.argv) < 2:
        print("请提供文件目录路径，例如：python app.py /path/to/directory")
        sys.exit(1)
    
    # 获取命令行传入的目录路径
    DOWNLOAD_FOLDER = os.path.abspath(sys.argv[1])
    
    # 检查目录是否存在且为目录
    if not os.path.exists(DOWNLOAD_FOLDER):
        print(f"错误：路径 {DOWNLOAD_FOLDER} 不存在")
        sys.exit(1)
    
    if not os.path.isdir(DOWNLOAD_FOLDER):
        print(f"错误：路径 {DOWNLOAD_FOLDER} 不是有效的目录")
        sys.exit(1)
    
    # 配置下载文件夹
    app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
    app.jinja_env.globals.update(len=len)  # 将 len 函数添加到 Jinja2 环境
    app.jinja_env.globals.update(os=os)  # 将 os 模块添加到 Jinja2 环境
    
    # 运行应用
    print(f"浏览目录：{DOWNLOAD_FOLDER}")
    print("访问 http://127.0.0.1:5000 查看文件列表")
    app.run(host='127.0.0.1', port=5000, debug=True)