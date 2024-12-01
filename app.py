from flask import Flask, send_from_directory

app = Flask(__name__)

# 设置下载文件夹路径
DOWNLOAD_FOLDER = '/usr/pdf'  # 请将 'downloads' 替换为实际的文件夹路径
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

@app.route('/pdf/<filename>')
def download_file(filename):
  """
  下载文件路由

  Args:
    filename: 文件名

  Returns:
    文件下载响应
  """
  try:
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=False)
  except FileNotFoundError:
    return "文件未找到", 404

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
