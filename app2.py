import os
import sys
from flask import Flask, render_template, send_from_directory, abort, request,  current_app
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
            entry_path = os.path.join(directory, entry)
            if os.path.isfile(entry_path):
                file_stats = os.stat(entry_path)
                files.append({
                    'name': entry,
                    'size': f"{file_stats.st_size / 1024:.2f} KB",
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
    
    return render_template('file_list.html', files=files, folders=folders, current_path=path,  app=current_app)

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
    filepath = os.path.normpath(os.path.join(directory, filename))
    
    # 安全检查：确保下载文件在指定目录内
    if not filepath.startswith(directory):
        abort(403)  # forbidden
    
    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        return "文件未找到", 404

def create_template(directory):
    """
    创建文件列表页面模板
    
    Args:
        directory (str): 模板保存目录
    """
    template = '''
<!DOCTYPE html>
<html>
<head>
    <title>文件浏览器 - {{ current_path }}</title>
    <meta charset="UTF-8">
    <style>
        /* 此处省略样式代码 */
    </style>
</head>
<body>
    <h1>文件浏览器 - {{ current_path }}</h1>
    <p>
        {% if current_path %}
        <a href="{{ url_for('browse_files', path=current_path.rsplit('/', 1)[0] or '/') }}">[返回上一级]</a>
        {% endif %}
    </p>
    
    {% if folders %}
    <h2>文件夹</h2>
    <ul>
        {% for folder in folders %}
        <li><a href="{{ url_for('browse_files', path=folder.path[len(app.config['DOWNLOAD_FOLDER']):].lstrip('/')) }}">{{ folder.name }}</a></li>
        {% endfor %}
    </ul>
    {% endif %}
    
    {% if files %}
    <h2>文件</h2>
    <table>
        <thead>
            <tr>
                <th>文件名</th>
                <th>大小</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for file in files %}
            <tr>
                <td>{{ file.name }}</td>
                <td>{{ file.size }}</td>
                <td>
                    <a href="{{ url_for('download_file', filename=file.path[len(app.config['DOWNLOAD_FOLDER']):].lstrip('/')) }}" class="download-link">下载</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    {% if not folders and not files %}
    <p>目录为空或不可访问</p>
    {% endif %}
</body>
</html>
    '''
    
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, 'file_list.html'), 'w', encoding='utf-8') as f:
        f.write(template)

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
    
    # 创建模板目录和文件
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    create_template(template_dir)
    
    # 配置下载文件夹
    app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
    
    # 运行应用
    print(f"浏览目录：{DOWNLOAD_FOLDER}")
    print("访问 http://127.0.0.1:5000 查看文件列表")
    app.run(host='127.0.0.1', port=5000, debug=True)