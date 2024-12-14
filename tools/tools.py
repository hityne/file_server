def is_browser_viewable(filename):
    """
    判断文件是否可以在浏览器中直接查看
    """
    viewable_extensions = {
        # 文档类型
        'pdf', 'txt', 'md',
        # 图片类型 
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',
        # 视频类型
        'mp4', 'webm', 'ogg',
        # 音频类型
        'mp3', 'wav',
    }
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    return ext in viewable_extensions

def get_file_icon(filename):
    """根据文件扩展名返回对应的Font Awesome图标类名"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # 文件类型图标映射
    icon_mapping = {
        # 图片文件
        'jpg': 'fa-image',
        'jpeg': 'fa-image',
        'png': 'fa-image',
        'gif': 'fa-image',
        'bmp': 'fa-image',
        'svg': 'fa-image',
        
        # 文档文件
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'pdf': 'fa-file-pdf',
        'txt': 'fa-file-lines',
        'md': 'fa-file-lines',
        'rtf': 'fa-file-lines',
        
        # 电子表格
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'csv': 'fa-file-csv',
        
        # 演示文稿
        'ppt': 'fa-file-powerpoint',
        'pptx': 'fa-file-powerpoint',
        
        # 压缩文件
        'zip': 'fa-file-zipper',
        'rar': 'fa-file-zipper',
        '7z': 'fa-file-zipper',
        'gz': 'fa-file-zipper',
        
        # 音频文件
        'mp3': 'fa-file-audio',
        'wav': 'fa-file-audio',
        'ogg': 'fa-file-audio',
        'flac': 'fa-file-audio',
        
        # 视频文件
        'mp4': 'fa-file-video',
        'avi': 'fa-file-video',
        'mkv': 'fa-file-video',
        'mov': 'fa-file-video',
        
        # 代码文件
        'py': 'fa-file-code',
        'js': 'fa-file-code',
        'html': 'fa-file-code',
        'css': 'fa-file-code',
        'java': 'fa-file-code',
        'php': 'fa-file-code',
        'cpp': 'fa-file-code',
        'c': 'fa-file-code',
        
        # 可执行文件
        'exe': 'fa-gears',
        'msi': 'fa-gears',
        'app': 'fa-gears',
    }
    
    return icon_mapping.get(ext, 'fa-file')  # 默认返回普通文件图标

def safe_filename(filename):
    """自定义的文件名安全检查，保留中文字符"""
    # 替换不安全的字符
    unsafe_chars = '/\\:*?"<>|'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename.strip()