# NIUXZ_clipboard_tool

一个简单的 Windows 剪贴板扩展工具，支持剪贴板历史记录、常用文本管理、模拟键盘键入(开发时主要目的)。

## 功能特性

- 剪贴板历史记录
- 常用文本管理
- 支持键盘模拟输入，通过模拟键盘事件来实现模拟用户键入，一般程序场景都可以，也可以实现向一些特殊目标键入内容，比如某些虚拟机内、某些远程桌面等。
- 系统托盘图标
- 开机自启动选项
- 无焦点悬浮窗设计

## 使用说明
运行后，在系统可捕获快捷键的情况下，可通过Ctrl+Alt+V打开主窗口，通过鼠标点击可将文本复制到剪贴板并粘贴到目标输入框，也可通过右键点击模拟键盘输入。
开机自启动：运行后，在系统托盘图标上右键点击，选择“开机自启动”即可。

### 快捷键

- `Ctrl + Alt + V`: 打开主窗口 （暂不支持设置，但可在代码中修改了自己打包）
- 左键点击: 复制到剪切板并粘贴
- 右键点击: 使用键盘模拟输入（仅支持内容中键盘上存在的字符）

### 系统托盘

右键点击系统托盘图标可以：
- 显示主窗口
- 打开设置
- 设置开机启动
- 退出程序

## 安装方法

### 使用预编译版本

1. 从 Releases 页面下载最新版本的 `clipboard_tool.zip`
2. 解压到任意目录，双击clipboard_tool文件夹运行其中的clipboard_tool.exe即可。（整个clipboard_tool都有用，剪切板历史记录也会保存在clipboard_tool.exe同级目录。）

### 从源码调试运行

1. 确保已安装 Python 3.7 或更高版本
2. 克隆仓库：

```bash
git clone [repository-url]
pip install -r requirements.txt
py main.py
```

### 从源码打包

1. 安装 PyInstaller

```bash
pip install pyinstaller
```

2. 运行以下命令：

```bash
git clone [repository-url]
pip install -r requirements.txt
py build.py
```

3. dist\clipboard_tool 即为打包好的可执行文件包，文件夹内都有用，将clipboard_tool文件夹复制到任意目录双击内部的clipboard_tool.exe即可。

### 扯两句
靠AI帮忙搞的，比较省脑子，我的python就只有阅读、调整代码的水平，跟大模型反复拉扯，用到了Deepseek、Claude等模型，十几个小时就搞的差不多可用了。但放心，没什么垃圾代码，代码全部经过了我的审查。名称前缀"NIUXZ_"只是代码中内防止与其他程序冲突用的标识。