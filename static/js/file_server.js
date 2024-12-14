// 全局变量
let currentXHR = null; // 用于存储当前的 XMLHttpRequest 对象

// 文件删除函数
function deleteFile(filename, button) {
    if (!confirm('确定要删除这个文件吗？')) {
        return;
    }

    fetch(`/delete/${filename}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.closest('tr').remove();
        } else {
            alert(data.message || '删除失败');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('删除失败');
    });
}

// 文件夹删除函数
function deleteFolder(path, button) {
    if (!confirm('确定要删除这个文件夹吗？文件夹内的所有内容都会被删除！')) {
        return;
    }

    fetch(`/delete_folder/${path}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.closest('.folder-item').remove();
        } else {
            alert(data.message || '删除失败');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('删除失败');
    });
}

// 下拉菜单控制
function toggleDropdown() {
    const dropdownMenu = document.getElementById('dropdownMenu');
    dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
}

// 点击其他地方关闭下拉菜单
window.onclick = function(event) {
    if (!event.target.matches('.dropdown-btn')) {
        const dropdowns = document.getElementsByClassName("dropdown-content");
        for (let dropdown of dropdowns) {
            if (dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
            }
        }
    }
}

// 新建文件夹相关函数
function showCreateFolderDialog() {
    document.getElementById('createFolderDialog').style.display = 'flex';
    document.getElementById('folderName').focus();
    toggleDropdown();
}

function closeCreateFolderDialog() {
    document.getElementById('createFolderDialog').style.display = 'none';
    document.getElementById('folderName').value = '';
}

function createFolder() {
    const name = document.getElementById('folderName').value.trim();
    if (!name) {
        alert('请输入目录名称');
        return;
    }

    const formData = new FormData();
    formData.append('name', name);
    formData.append('path', serverData.currentPath);

    fetch('/create_folder', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.message || '创建失败');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('创建失败');
    });
}

// 文件上传相关函数
async function uploadFiles(input) {
    if (!input.files || input.files.length === 0) return;

    // 将 FileList 转换为数组并创建副本
    let filesToUpload = Array.from(input.files);
    const totalFiles = filesToUpload.length;
    let uploadedFiles = 0;

    try {
        // 先检查所有文件
        for (let i = filesToUpload.length - 1; i >= 0; i--) {
            const file = filesToUpload[i];
            const checkFormData = new FormData();
            checkFormData.append('filename', file.name);
            checkFormData.append('path', serverData.currentPath);

            try {
                const checkResponse = await fetch('/check_file_exists', {
                    method: 'POST',
                    body: checkFormData
                });
                const checkResult = await checkResponse.json();

                if (checkResult.success && checkResult.exists) {
                    if (!confirm(`文件 "${file.name}" 已存在，是否覆盖？`)) {
                        filesToUpload.splice(i, 1); // 从后向前移除不需要上传的文件
                    }
                }
            } catch (error) {
                console.error('检查文件失败:', error);
                alert(`检查文件 "${file.name}" 失败`);
                filesToUpload.splice(i, 1); // 移除检查失败的文件
            }
        }

        // 如果没有要上传的文件了，就返回
        if (filesToUpload.length === 0) {
            input.value = '';
            return;
        }

        // 显示进度对话框
        const progressDialog = document.getElementById('uploadProgressDialog');
        const progressBar = document.getElementById('uploadProgress');
        const progressText = document.getElementById('uploadPercent');
        progressDialog.style.display = 'flex';

        // 逐个上传文件
        for (let i = 0; i < filesToUpload.length; i++) {
            const file = filesToUpload[i];
            try {
                await uploadSingleFile(file, i + 1, filesToUpload.length);
                uploadedFiles++;
            } catch (error) {
                if (error.message === 'Upload cancelled') {
                    // 用户取消上传，终止后续上传
                    break;
                }
                console.error('上传失败:', error);
                alert(`文件 "${file.name}" 上传失败: ${error.message}`);
            }
        }

        // 全部完成后刷新页面
        if (uploadedFiles > 0) {
            location.reload();
        }
    } finally {
        // 清理工作
        const progressDialog = document.getElementById('uploadProgressDialog');
        progressDialog.style.display = 'none';
        input.value = '';
    }
}

// 单文件上传函数
async function uploadSingleFile(file, currentIndex, totalFiles) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', serverData.currentPath);

        const xhr = new XMLHttpRequest();
        currentXHR = xhr;

        // 获取进度显示元素
        const progressBar = document.getElementById('uploadProgress');
        const progressText = document.getElementById('uploadPercent');
        const speedText = document.getElementById('uploadSpeed');

        // 用于计算上传速度
        let startTime = Date.now();
        let lastLoaded = 0;

        xhr.upload.onprogress = function(event) {
            if (event.lengthComputable) {
                const percent = (event.loaded / event.total * 100).toFixed(2);
                progressBar.style.width = percent + '%';
                progressText.textContent = `${file.name} (${currentIndex}/${totalFiles}): ${percent}%`;

                // 计算上传速度
                const currentTime = Date.now();
                const timeElapsed = (currentTime - startTime) / 1000;
                if (timeElapsed > 0) {
                    const loaded = event.loaded - lastLoaded;
                    const speed = loaded / timeElapsed;
                    lastLoaded = event.loaded;
                    startTime = currentTime;

                    // 格式化速度显示
                    let speedDisplay = '';
                    if (speed < 1024) {
                        speedDisplay = speed.toFixed(2) + ' B/s';
                    } else if (speed < 1024 * 1024) {
                        speedDisplay = (speed / 1024).toFixed(2) + ' KB/s';
                    } else {
                        speedDisplay = (speed / (1024 * 1024)).toFixed(2) + ' MB/s';
                    }

                    speedText.textContent = speedDisplay;
                }
            }
        };

        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        resolve();
                    } else {
                        reject(new Error(response.message || '上传失败'));
                    }
                } catch (e) {
                    reject(new Error('上传失败'));
                }
            } else {
                reject(new Error('上传失败: ' + xhr.status));
            }
            currentXHR = null;
        };

        xhr.onerror = function() {
            reject(new Error('网络错误'));
            currentXHR = null;
        };

        xhr.onabort = function() {
            reject(new Error('Upload cancelled'));
            currentXHR = null;
        };

        xhr.open('POST', '/upload', true);
        xhr.send(formData);
    });
}

// 取消上传函数
function cancelUpload() {
    if (currentXHR) {
        if (confirm('确定要取消上传吗？\n注意：这将取消当前文件及后续所有文件的上传。')) {
            currentXHR.abort();
            currentXHR = null;
        }
    }
}

// 时间显示函数
function updateCurrentTime() {
    const currentTimeElement = document.getElementById('current-time');
    const now = new Date();
    const options = { 
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    };
    currentTimeElement.textContent = now.toLocaleString('zh-CN', options);
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化时间显示
    updateCurrentTime();
    // 定时更新
    setInterval(updateCurrentTime, 1000);
});