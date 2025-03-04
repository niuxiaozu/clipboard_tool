import tkinter as tk
from tkinter import ttk
from typing import Callable
import win32api
from ctypes import windll, wintypes

# 窗口样式常量
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CHILD = 0x40000000
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

# 窗口位置标志
SWP_FRAMECHANGED = 0x0020
SWP_NOACTIVATE = 0x0010
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

# 类型定义和函数原型
GetWindowLong = windll.user32.GetWindowLongW 
GetWindowLong.restype = wintypes.ULONG
GetWindowLong.argtypes = (wintypes.HWND, wintypes.INT)

SetWindowLong = windll.user32.SetWindowLongW 
SetWindowLong.restype = wintypes.ULONG
SetWindowLong.argtypes = (wintypes.HWND, wintypes.INT, wintypes.ULONG)

SetWindowPos = windll.user32.SetWindowPos 

class FloatingWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.overrideredirect(True)  # 无边框窗口
        self.attributes('-topmost', True)  # 置顶
        self.attributes('-alpha', 0.9)  # 透明度
        self.withdraw()
    
        self.init_ui()
        self._item_selected_callback = None
        
        # 创建常驻的右键菜单窗口
        self._init_context_menu()
        
        # 设置窗口为无焦点模式
        self.update()
        self._set_no_focus_window()

    def _init_context_menu(self):
        """初始化常驻右键菜单窗口"""
        self.context_menu = tk.Toplevel(self)
        self.context_menu.withdraw()
        self.context_menu.overrideredirect(True)
        self.context_menu.attributes('-topmost', True)
        
        # 创建菜单内容
        frame = ttk.Frame(self.context_menu, relief="raised", borderwidth=1)
        frame.pack(fill="both", expand=True)
        
        # 添加菜单项
        self.menu_button = ttk.Button(frame, text=" 模拟键盘输入")
        self.menu_button.pack(fill="x", padx=2, pady=2)
        
        # 绑定点击事件用于隐藏菜单
        self.bind('<Button-1>', self._hide_context_menu)
        
        # 设置无焦点模式
        self.context_menu.update()
        self._set_menu_no_focus(self.context_menu)

    def _show_context_menu(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        if index < 0:
            return
        widget.selection_clear(0, tk.END)
        widget.selection_set(index)
        selection = widget.get(index)
        
        # 更新菜单按钮命令
        self.menu_button.configure(
            command=lambda: [
                self.hide_window(),
                self._item_selected_callback(selection, True) if self._item_selected_callback else None
            ]
        )
        
        # 显示菜单
        self.context_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.context_menu.deiconify()
        self.context_menu.lift()

    def _hide_context_menu(self, event=None):
        """隐藏右键菜单"""
        if self.context_menu.winfo_viewable():
            self.context_menu.withdraw()

    # 删除原来的 _create_no_focus_menu 方法
    def _find_root_window(self):
        """查找并修改窗口样式以获取父窗口句柄"""
        w_id = self.winfo_id() 
        
        # 临时修改窗口样式
        style = GetWindowLong(w_id, GWL_STYLE)
        new_style = style & ~WS_CHILD
        SetWindowLong(w_id, GWL_STYLE, new_style)
        SetWindowPos(w_id, 0, 0, 0, 0, 0, 
                    SWP_FRAMECHANGED | SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE)
        
        # 获取父窗口句柄后恢复原样式
        hwnd = int(self.wm_frame(), 16)
        SetWindowLong(w_id, GWL_STYLE, style)
        SetWindowPos(w_id, 0, 0, 0, 0, 0,
                    SWP_FRAMECHANGED | SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE)
        
        return hwnd
        
    def _set_no_focus_window(self):
        """设置窗口为无焦点模式"""
        hwnd = self._find_root_window()
        if hwnd:
            style = GetWindowLong(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_NOACTIVATE | WS_EX_APPWINDOW
            SetWindowLong(hwnd, GWL_EXSTYLE, style)
            SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                        SWP_FRAMECHANGED | SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE)
        
    def init_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self)
        self.main_frame = main_frame
        main_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        # 添加标题栏
        title_bar = ttk.Frame(main_frame)
        title_bar.pack(fill='x', pady=(0, 5))
        
        # 拖动区域
        drag_area = ttk.Label(title_bar, text="   剪贴板工具   ")
        drag_area.pack(side='left', fill='x', expand=True)
        drag_area.bind('<Button-1>', self._start_drag)
        drag_area.bind('<B1-Motion>', self._on_drag)
        
        # 按钮区域
        buttons_frame = ttk.Frame(title_bar)
        buttons_frame.pack(side='right')
        
        # 设置按钮
        self.settings_button = ttk.Button(buttons_frame, text="⚙", width=3, command=self.open_settings)
        self.settings_button.pack(side='left', padx=2)
        
        # 关闭按钮
        close_button = ttk.Button(buttons_frame, text="×", width=3, command=self.hide_window)
        close_button.pack(side='left', padx=2)
        
        # 创建左右两个框架
        left_frame = ttk.Frame(main_frame)
        right_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        right_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        # 常用内容部分
        title_frame = ttk.Frame(left_frame)
        title_frame.pack(fill='x')
        
        # 常用内容部分
        ttk.Label(title_frame, text=" 常用内容").pack(side='left')
        self.favorites_list = tk.Listbox(left_frame, height=10)
        self.favorites_list.pack(fill='both', expand=True)
        
        # 剪贴历史部分
        ttk.Label(right_frame, text=" 剪贴历史").pack()
        self.history_list = tk.Listbox(right_frame, height=10)
        self.history_list.pack(fill='both', expand=True)
        
        # 绑定事件
        self.favorites_list.bind('<<ListboxSelect>>', self._on_item_select)
        self.favorites_list.bind('<Button-3>', self._show_context_menu)
        self.favorites_list.bind('<Motion>', self._show_tooltip)
        self.favorites_list.bind('<Leave>', self._hide_tooltip)
        
        self.history_list.bind('<<ListboxSelect>>', self._on_item_select)
        self.history_list.bind('<Button-3>', self._show_context_menu)
        self.history_list.bind('<Motion>', self._show_tooltip)
        self.history_list.bind('<Leave>', self._hide_tooltip)
        
        # 创建工具提示窗口
        self.tooltip = tk.Toplevel(self)
        self.tooltip.withdraw()
        self.tooltip.overrideredirect(True)
        self.tooltip_label = tk.Label(self.tooltip, justify=tk.LEFT, background="#ffffe0", 
                                    relief='solid', borderwidth=1)
        self.tooltip_label.pack()
        
    def _show_tooltip(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        if index < 0:
            return
            
        text = widget.get(index)
        self.tooltip_label.config(text=text)
        
        # 获取屏幕工作区尺寸（不包含任务栏）
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        try:
            work_area = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0,0)))['Work']
            screen_width = work_area[2]  # 工作区宽度
            screen_height = work_area[3]  # 工作区高度
        except:
            pass
        
        # 计算tooltip的尺寸
        self.tooltip.update_idletasks()
        tooltip_width = self.tooltip.winfo_reqwidth()
        tooltip_height = self.tooltip.winfo_reqheight()
        
        # 默认显示在列表右侧
        x = widget.winfo_rootx() + widget.winfo_width() + 10
        y = event.y_root - tooltip_height // 2  # 垂直居中对齐
        
        # 如果右侧空间不足，显示在窗口的左侧
        if x + tooltip_width > screen_width:
            x = self.winfo_rootx() - tooltip_width - 10
            
        # 确保tooltip不会超出屏幕底部（考虑任务栏）
        if y + tooltip_height > screen_height:
            y = screen_height - tooltip_height - 5
        
        # 确保tooltip不会超出屏幕顶部
        if y < 0:
            y = 5
            
        self.tooltip.geometry(f"+{x}+{y}")
        self.tooltip.deiconify()
        self.tooltip.lift()

    def _hide_tooltip(self, event):
        self.tooltip.withdraw()
        
    def _on_item_select(self, event):
        widget = event.widget
        if not widget.curselection():
            return
        self.hide_window()
        selection = widget.get(widget.curselection())
        if self._item_selected_callback:
            self._item_selected_callback(selection, False)
            
    
    def _set_menu_no_focus(self, menu_window):
        """为菜单窗口设置无焦点模式"""
        hwnd = int(menu_window.wm_frame(), 16)
        if hwnd:
            style = GetWindowLong(hwnd, GWL_EXSTYLE)
            style = style | WS_EX_NOACTIVATE
            SetWindowLong(hwnd, GWL_EXSTYLE, style)
            SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                        SWP_FRAMECHANGED | SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE)
    
        
    def set_item_selected_callback(self, callback: Callable[[str, bool], None]):
        """设置项目选择的回调函数"""
        self._item_selected_callback = callback
    def set_settings_callback(self, callback: Callable[[], None]):
        """设置项目选择的回调函数"""
        self._selected_callback = callback
    def open_settings(self):
        self._selected_callback()
    
    def update_lists(self, favorites=None, history=None):
        """更新列表内容"""
        if favorites is not None:
            self.favorites_list.delete(0, tk.END)
            for item in favorites:
                self.favorites_list.insert(tk.END, item)
                
        if history is not None:
            self.history_list.delete(0, tk.END)
            for item in history:
                self.history_list.insert(tk.END, item)
    
    def show_at_position(self, x, y):
        """在指定位置显示窗口，并确保窗口完全在屏幕内"""
        # 获取屏幕工作区尺寸（不包含任务栏）
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        try:
            work_area = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0,0)))['Work']
            screen_width = work_area[2]  # 工作区宽度
            screen_height = work_area[3]  # 工作区高度
        except:
            pass
        
        # 更新窗口以获取实际尺寸
        self.update_idletasks()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # 确保窗口不会超出屏幕右侧
        if x + window_width > screen_width:
            x = screen_width - window_width - 5
            
        # 确保窗口不会超出屏幕底部（考虑任务栏）
        if y + window_height > screen_height:
            y = screen_height - window_height - 5
            
        # 确保窗口不会超出屏幕左侧
        if x < 5:
            x = 5
            
        # 确保窗口不会超出屏幕顶部
        if y < 5:
            y = 5
            
        self.geometry(f'+{x}+{y}')
        self.deiconify()
        self.lift()
        
        # 重新应用无焦点设置
        self._set_no_focus_window()
        
    def hide_window(self):
        """隐藏窗口"""
        self.context_menu.withdraw()
        self.withdraw()

    def _start_drag(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._window_start_x = self.winfo_x()
        self._window_start_y = self.winfo_y()

    def _on_drag(self, event):
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        new_x = self._window_start_x + dx
        new_y = self._window_start_y + dy
        self.geometry(f'+{new_x}+{new_y}')