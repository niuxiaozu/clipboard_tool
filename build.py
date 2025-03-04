import os
import PyInstaller.__main__

def get_requirements():
    """从requirements.txt读取依赖包"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(current_dir, 'requirements.txt')
    with open(req_path, 'r') as f:
        # 读取每行并去除版本号
        return [line.split('==')[0] for line in f.readlines() if line.strip()]

def build_exe():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, 'icon.png')
    
    # 基础参数
    params = [
        'main.py',
        '--noconsole',
        '--icon=' + icon_path,
        '--add-data', f'{icon_path};.',
        '--name=clipboard_tool',
        '--clean',
        '--strip',
        '--noupx',
        '--exclude-module=build',
        '--noconfirm'
    ]
    
    # 添加requirements.txt中的包
    for package in get_requirements():
        if package != 'pyinstaller':  # 排除pyinstaller本身
            params.extend(['--hidden-import', package])
    
    # 执行打包
    PyInstaller.__main__.run(params)

if __name__ == "__main__":
    build_exe()