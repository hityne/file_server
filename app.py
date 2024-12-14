import os, sys
from flask import Flask, render_template, send_from_directory, abort, request, current_app, jsonify, Response
from builtins import len  # 导入 len 函数
import time, datetime, shutil
from werkzeug.utils import secure_filename
from tools.tools import is_browser_viewable, get_file_icon, safe_filename
from urllib.parse import quote

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
            if entry.startswith('.') or entry.startswith('_') or entry.startswith('$'):  # 跳过以 . 开头的文件和文件夹
                continue
            entry_path = os.path.join(directory, entry)
            if os.path.isfile(entry_path):
                file_stats = os.stat(entry_path)
                file_size = file_stats.st_size
                
                # 根据文件大小显示不同的单位并添加千分符
                if file_size < 1024 * 1024:  # 小于1MB
                    size_str = f"{file_size / 1024:,.2f} KB"
                else:  # 大于等于1MB
                    size_str = f"{file_size / (1024 * 1024):,.2f} MB"
                
                files.append({
                    'name': entry,
                    'size': size_str,
                    'mtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_stats.st_mtime)),  # 添加修改时间
                    'path': entry_path,
                    'icon': get_file_icon(entry),  # 添加图标类名
                    'viewable': is_browser_viewable(entry)  # 添加是否可预览标记
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

    visitor_ip = request.remote_addr
    
    # 获取当前时间（精确到秒）
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template('main.html', files=files, folders=folders, current_path=path, visitor_ip=visitor_ip, current_time=current_time, app=current_app)


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
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        return "文件未找到", 404

# 在 app.py 中添加新的路由和功能

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    """
    删除文件
    
    Args:
        filename (str): 要删除的文件名
    
    Returns:
        JSON响应
    """
    directory = app.config['DOWNLOAD_FOLDER']
    filename = filename.replace("\\", "/")  # 将反斜杠替换为正斜杠
    filepath = os.path.normpath(os.path.join(directory, filename))
    
    # 安全检查：确保要删除的文件在指定目录内
    if not filepath.startswith(directory):
        return {"success": False, "message": "访问被拒绝"}, 403
    
    try:
        if os.path.exists(filepath) and os.path.isfile(filepath):
            os.remove(filepath)
            return {"success": True, "message": "文件已删除"}
        else:
            return {"success": False, "message": "文件不存在"}, 404
    except Exception as e:
        return {"success": False, "message": str(e)}, 500


@app.route('/delete_folder/<path:folder_path>', methods=['POST'])
def delete_folder(folder_path):
    """
    删除文件夹
    
    Args:
        folder_path (str): 要删除的文件夹路径
    
    Returns:
        JSON响应
    """
    directory = app.config['DOWNLOAD_FOLDER']
    folder_path = folder_path.replace("\\", "/")
    full_path = os.path.normpath(os.path.join(directory, folder_path))
    
    # 安全检查：确保要删除的文件夹在指定目录内
    if not full_path.startswith(directory):
        return {"success": False, "message": "访问被拒绝"}, 403
    
    try:
        if os.path.exists(full_path) and os.path.isdir(full_path):
            shutil.rmtree(full_path)  # 递归删除文件夹及其内容
            return {"success": True, "message": "文件夹已删除"}
        else:
            return {"success": False, "message": "文件夹不存在"}, 404
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/create_folder', methods=['POST'])
def create_folder():
    """创建新文件夹"""
    parent_path = request.form.get('path', '')
    folder_name = request.form.get('name', '').strip()
    
    if not folder_name:
        return jsonify({"success": False, "message": "文件夹名称不能为空"}), 400
        
    # 构建完整路径
    directory = app.config['DOWNLOAD_FOLDER']
    full_path = os.path.normpath(os.path.join(directory, parent_path, folder_name))
    
    # 安全检查：确保新建的文件夹在指定目录内
    if not os.path.normpath(full_path).startswith(directory):
        return jsonify({"success": False, "message": "非法路径"}), 403
        
    try:
        if os.path.exists(full_path):
            return jsonify({"success": False, "message": "文件夹已存在"}), 400
            
        os.makedirs(full_path)
        return jsonify({"success": True, "message": "文件夹创建成功"})
    except Exception as e:
        print(f"创建文件夹失败: {str(e)}")  # 添加错误日志
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "没有文件被上传"}), 400
        
    file = request.files['file']
    current_path = request.form.get('path', '')
    
    if file.filename == '':
        return jsonify({"success": False, "message": "未选择文件"}), 400
        
    if file:
        # 使用原始文件名，不进行安全化处理
        filename = safe_filename(file.filename)
        upload_folder = os.path.join(app.config['DOWNLOAD_FOLDER'], current_path)
        
        # 确保上传路径存在
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
            except Exception as e:
                return jsonify({"success": False, "message": f"创建目录失败: {str(e)}"}), 500
        
        # 安全检查：确保上传路径在允许的目录内
        if not os.path.normpath(upload_folder).startswith(app.config['DOWNLOAD_FOLDER']):
            return jsonify({"success": False, "message": "非法上传路径"}), 403
            
        try:
            # 使用原始文件名保存文件
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            return jsonify({"success": True, "message": "文件上传成功"})
        except Exception as e:
            print(f"文件上传失败: {str(e)}")
            return jsonify({"success": False, "message": f"文件上传失败: {str(e)}"}), 500

    return jsonify({"success": False, "message": "未知错误"}), 400

@app.route('/check_file_exists', methods=['POST'])
def check_file_exists():
    """检查文件是否存在"""
    current_path = request.form.get('path', '')
    filename = request.form.get('filename', '')
    
    if not filename:
        return jsonify({"success": False, "message": "未提供文件名"}), 400
        
    full_path = os.path.join(app.config['DOWNLOAD_FOLDER'], current_path, filename)
    
    # 安全检查
    if not os.path.normpath(full_path).startswith(app.config['DOWNLOAD_FOLDER']):
        return jsonify({"success": False, "message": "非法路径"}), 403
        
    exists = os.path.exists(full_path)
    return jsonify({"success": True, "exists": exists})

@app.route('/view/<path:filename>')
def view_file(filename):
    """
    在浏览器中直接查看文件，使用流式传输并支持范围请求
    """
    directory = app.config['DOWNLOAD_FOLDER']
    filename = filename.replace("\\", "/")
    filepath = os.path.normpath(os.path.join(directory, filename))
    
    # 安全检查：确保文件在指定目录内
    if not filepath.startswith(directory):
        abort(403)
    
    try:
        # 如果不是可预览的文件类型，则转为下载
        if not is_browser_viewable(filename):
            return send_from_directory(directory, filename, as_attachment=True)

        # 获取文件 MIME 类型
        mime_type = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'txt': 'text/plain',
            'md': 'text/plain',
        }.get(filename.lower().split('.')[-1], 'application/octet-stream')
        
        file_size = os.path.getsize(filepath)
        
        # 处理范围请求
        range_header = request.headers.get('Range', None)
        if range_header:
            byte_start, byte_end = range_header.replace('bytes=', '').split('-')
            byte_start = int(byte_start)
            if byte_end:
                byte_end = int(byte_end)
            else:
                byte_end = file_size - 1
            
            if byte_start >= file_size:
                return 'Requested range not satisfiable', 416
            
            # 确保 byte_end 不超过文件大小
            byte_end = min(byte_end, file_size - 1)
            length = byte_end - byte_start + 1
            
            def generate_range():
                with open(filepath, 'rb') as f:
                    f.seek(byte_start)
                    remaining = length
                    while remaining > 0:
                        chunk_size = min(remaining, 1024 * 1024)  # 每次最多读取1MB
                        data = f.read(chunk_size)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
            
            response = Response(
                generate_range(),
                206,  # Partial Content
                mimetype=mime_type,
                direct_passthrough=True
            )
            response.headers['Content-Range'] = f'bytes {byte_start}-{byte_end}/{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = str(length)
        else:
            # 非范围请求，返回完整文件
            def generate():
                with open(filepath, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        yield chunk
            
            response = Response(
                generate(),
                mimetype=mime_type,
                direct_passthrough=True
            )
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = str(file_size)
        
        # 对文件名进行 URL 编码
        encoded_filename = quote(os.path.basename(filename))
        response.headers['Content-Disposition'] = f"inline; filename*=UTF-8''{encoded_filename}"
        
        return response
        
    except FileNotFoundError:
        return "文件未找到", 404
    except Exception as e:
        print(f"文件访问错误: {str(e)}")  # 打印具体错误信息以便调试
        return "文件访问错误", 500

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
    app.run(host='0.0.0.0', port=5000, debug=True)