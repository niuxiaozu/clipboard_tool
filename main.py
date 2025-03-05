import os
from re import error
import sys
import time
import keyboard
import pyperclip
import threading
import pyautogui
import pystray
from PIL import Image
from pywinauto.keyboard import send_keys
from pywinauto import Application
import win32com.client,win32api,win32con,win32gui
import io
import winreg
from clipboard_db import ClipboardDB
from clipboard_db import ClipboardItem
from floating_window_tk import FloatingWindow
from settings_window import SettingsWindow

# 输入方式常量
INPUT_METHOD = "pyautogui"  # 可选值: "pyautogui" 或 "pywinauto" 或 "win32"
# 定义所需的常量
WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_UNLOCK = 0x8

class ClipboardWorker(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.last_content = None
        self.stop_event = threading.Event()
        self.daemon = True  # 设置为守护线程

    def run(self):
        while not self.stop_event.is_set():
            try:
                content = pyperclip.paste()
                if content != self.last_content:
                    print("剪贴板内容已改变：", content)
                    self.callback(content)
                    self.last_content = content
                    print("内容已改变：", self.last_content)
            except:
                pass
            time.sleep(0.5)  # 减少检查间隔以提高响应速度

    def stop(self):
        self.stop_event.set()

class ClipboardManager:
    def __init__(self):
        self.ignore_next_paste = False
        self.db = ClipboardDB()
        self.window = FloatingWindow()
        # 设置 pyautogui 的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        # 初始化 pywinauto
        if INPUT_METHOD == "pywinauto":
            self.app = Application()
        elif INPUT_METHOD == "win32":
            self.shell = win32com.client.Dispatch("WScript.Shell")

        self.window.set_item_selected_callback(self.on_item_selected)
        self.window.set_settings_callback(self.open_settings)
        self.hotkey_id = 1
        # 添加系统事件监听
        self.setup_system_event_handler()
        self.init_hotkeys()
        # 初始化剪贴板监控线程
        self.clipboard_worker = ClipboardWorker(self.on_clipboard_changed)
        self.clipboard_worker.start()
        self.settings = None
        
        # 初始化系统托盘图标
        self.init_tray_icon()

    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 创建图标
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            base_path = sys._MEIPASS
        else:
            # 如果是直接运行的py文件
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_path, "icon.png")
        
        # 创建图标
        icon_image = Image.open(icon_path)
        
        # 创建菜单
        menu = (
            pystray.MenuItem('显示主窗口', self.show_main_window),
            pystray.MenuItem('设置', self.open_settings),
            pystray.MenuItem('开机启动', self.toggle_autostart, checked= lambda _:self.is_autostart_enabled()),
            pystray.MenuItem('退出', self.stop)
        )
        
        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "clipboard_tool",
            icon_image,
            "剪贴板工具",
            menu
        )
                
        # 在单独的线程中启动托盘图标
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def on_tray_icon_click(self, icon, button):
        """处理托盘图标点击事件"""
        if str(button) == "Button.left":
            self.show_main_window()
    
    def show_main_window(self, *args):
        """显示主窗口"""
        # 在显示窗口前更新列表内容，按时间降序排列
        sorted_history = sorted(self.db.history, key=lambda x: x.timestamp, reverse=True)
        self.window.update_lists(
            favorites=[item.content for item in self.db.favorites],
            history=[item.content for item in sorted_history]
        )

        x = self.window.winfo_pointerx()
        y = self.window.winfo_pointery()
        self.window.show_at_position(x, y)

    def is_autostart_enabled(self):
        """检查是否已设置开机启动"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            winreg.QueryValueEx(key, "NIUXZ_ClipboardTool")
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_autostart(self):
        """切换开机启动状态"""
        if self.is_autostart_enabled():
            self.disable_autostart()
        else:
            self.enable_autostart()
        
        # 更新菜单项的选中状态
        self.tray_icon.update_menu()

    def enable_autostart(self):
        """启用开机启动"""
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE
        )
        exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
        winreg.SetValueEx(key, "NIUXZ_ClipboardTool", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)

    def disable_autostart(self):
        """禁用开机启动"""
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE
        )
        try:
            winreg.DeleteValue(key, "NIUXZ_ClipboardTool")
        except WindowsError:
            pass
        winreg.CloseKey(key)

    def setup_system_event_handler(self):
        """设置系统事件处理"""
        # 注册系统事件监听
        try:
            import win32ts
            import win32con
            import win32gui
            
            def wndproc(hwnd, msg, wparam, lparam):
                print("监听到系统事件",msg,wparam,lparam)
                if msg == WM_WTSSESSION_CHANGE:
                    if wparam == WTS_SESSION_UNLOCK:
                        self.init_hotkeys()
                elif msg == win32con.WM_HOTKEY:
                    if wparam == self.hotkey_id:
                        self.toggle_window()
                return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
            
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = wndproc
            wc.lpszClassName = "ClipboardToolEventHandler"
            win32gui.RegisterClass(wc)
            self.hwnd = win32gui.CreateWindow(
                wc.lpszClassName, 
                "ClipboardTool",
                0, 0, 0, 0, 0,
                0, 0, 0, None
            )
            win32ts.WTSRegisterSessionNotification(self.hwnd, win32ts.NOTIFY_FOR_THIS_SESSION)
        except Exception as e:
            print(f"注册系统事件监听失败: {e}")

    def init_hotkeys(self):
        """使用 Windows API 注册全局热键"""
        print("设置快捷键")
        try:
            # 先注销已有的热键
            win32gui.UnregisterHotKey(self.hwnd, self.hotkey_id)
        except Exception as e:
            pass        # 注册新的热键 (MOD_CONTROL | MOD_ALT + V)
        try:
            win32gui.RegisterHotKey(self.hwnd, self.hotkey_id, win32con.MOD_CONTROL | win32con.MOD_ALT, ord('V'))
        except Exception as e:
            print(f"注册热键失败: {e}")
        
    def toggle_window(self):
        state = self.window.state()
        if state == 'normal':
            # self.window.hide_window()
            pass
        else:
            self.show_main_window()

    def open_settings(self, *args):
        """打开设置窗口"""
        if not self.settings or not self.settings.winfo_exists():
            self.settings = SettingsWindow(self, self.db)
            self.settings.db = self.db
        
        self.settings.load_favorites()
        self.settings.deiconify()
        self.settings.lift()
        self.settings.focus_force()

    def on_clipboard_changed(self, content):
        if self.ignore_next_paste:
            self.ignore_next_paste = False
        else:
            item = ClipboardItem(content=content, format='text', timestamp=time.time(), metadata={"source": "clipboard"})
            self.db.add_history(item)
            # 更新窗口显示内容，按时间降序排列
            sorted_history = sorted(self.db.history, key=lambda x: x.timestamp, reverse=True)
            self.window.update_lists(
                favorites=[item.content for item in self.db.favorites],
                history=[item.content for item in sorted_history]
            )
    def _pywinauto_type(self, content: str):
        """使用 pywinauto 的底层按键方式输入文本"""
        for char in content:
            if char.isupper():
                # 使用 pywinauto 的特殊语法：+ 表示按下，- 表示释放
                send_keys('+{SHIFT}' + char.lower() + '-{SHIFT}')
            else:
                send_keys(char)
            time.sleep(0.01)
    def _pyautogui_type(self, content: str):
        """使用 pyautogui 的底层按键方式输入文本"""
        for char in content:
            if char.isupper():
                pyautogui.keyDown('shift')
                pyautogui.press(char.lower())
                pyautogui.keyUp('shift')
            else:
                pyautogui.press(char)
            time.sleep(0.01)  # 添加小延迟确保输入稳定
    def _win32_type(self, text):
        """使用 win32api 实现键盘输入"""
        for char in text:
            # 获取字符的虚拟键码和扫描码
            vk = win32api.VkKeyScan(char)
            if vk == -1:
                continue
            
            # 处理组合键
            if vk > 0x100:
                # 按下 Shift
                win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            
            # 按下键
            win32api.keybd_event(vk & 0xFF, 0, 0, 0)
            # 释放键
            win32api.keybd_event(vk & 0xFF, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            if vk > 0x100:
                # 释放 Shift
                win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            time.sleep(0.01)  # 添加小延迟确保输入稳定

    def on_item_selected(self, content: str, is_keyboard_input: bool):
        time.sleep(0.2) #加点延迟好让窗口隐藏让原本窗口捕获输入
        # 处理选中的内容
        if is_keyboard_input:
            if INPUT_METHOD == "pywinauto":
                self._pywinauto_type(content)
            elif INPUT_METHOD == "win32":
                self._win32_type(content)
            else:
                self._pyautogui_type(content)
        else:
            self.ignore_next_paste = True
            pyperclip.copy(content)
            # 模拟粘贴
            if INPUT_METHOD == "pywinauto":
                send_keys('^v')
            elif INPUT_METHOD == "win32":
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                win32api.keybd_event(ord('V'), 0, 0, 0)
                win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            else:
                pyautogui.hotkey('ctrl', 'v')
    def start(self):
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            print("\n正在关闭程序...")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源并优雅退出"""
        try:
            win32gui.UnregisterHotKey(self.hwnd, self.hotkey_id)
        except:
            pass
        keyboard.unhook_all()
        if hasattr(self, 'clipboard_worker'):
            self.clipboard_worker.stop()
            self.clipboard_worker.join()

    def stop(self):
        if self.window:
            self.window.destroy()
            self.window.quit()
        self.cleanup()

    def __del__(self):
        self.stop()

if __name__ == "__main__":
    manager = None
    try:
        manager = ClipboardManager()
        manager.start()
    except KeyboardInterrupt:
        print("\n正在关闭程序...")
        if manager:
            manager.stop()
    sys.exit(0)