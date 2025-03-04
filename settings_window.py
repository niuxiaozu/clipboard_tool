import tkinter as tk
from tkinter import ttk, messagebox
from clipboard_db import ClipboardDB, ClipboardItem
import time

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, db: ClipboardDB):
        super().__init__()
        self.parent = parent
        self.db = db
        
        # 设置窗口属性
        self.title("设置")
        self.geometry("500x400")
        self.resizable(True, True)
        self.attributes('-topmost', True)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # 创建常用内容编辑选项卡
        self.favorites_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.favorites_frame, text="常用内容")
        
        # 初始化常用内容编辑界面
        self.init_favorites_ui()
        
        # 窗口关闭时的处理
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def init_favorites_ui(self):
        # 创建左右布局
        left_frame = ttk.Frame(self.favorites_frame)
        right_frame = ttk.Frame(self.favorites_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        right_frame.pack(side='right', fill='y', padx=5, pady=5)
        
        # 左侧：常用内容列表
        list_frame = ttk.LabelFrame(left_frame, text="常用内容列表")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建列表和滚动条
        self.favorites_listbox = tk.Listbox(list_frame, height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.favorites_listbox.yview)
        self.favorites_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.favorites_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 绑定选择事件
        self.favorites_listbox.bind('<<ListboxSelect>>', self.on_favorite_selected)
        
        # 右侧：编辑区域
        edit_frame = ttk.LabelFrame(right_frame, text="编辑内容")
        edit_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 内容编辑框
        ttk.Label(edit_frame, text="内容:").pack(anchor='w', padx=5, pady=2)
        self.content_text = tk.Text(edit_frame, height=10, width=30)
        self.content_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        # 添加按钮
        ttk.Button(button_frame, text="新增", command=self.add_favorite).pack(side='left', padx=5)
        ttk.Button(button_frame, text="更新", command=self.update_favorite).pack(side='left', padx=5)
        ttk.Button(button_frame, text="删除", command=self.delete_favorite).pack(side='left', padx=5)
        
        # 加载常用内容
        self.load_favorites()
    
    def load_favorites(self):
        """加载常用内容到列表"""
        self.favorites_listbox.delete(0, tk.END)
        for item in self.db.favorites:
            self.favorites_listbox.insert(tk.END, item.content)
    
    def on_favorite_selected(self, event):
        """当选择常用内容时"""
        if not self.favorites_listbox.curselection():
            return
        
        index = self.favorites_listbox.curselection()[0]
        content = self.db.favorites[index].content
        
        # 清空并设置内容
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, content)
    
    def add_favorite(self):
        """添加新的常用内容"""
        content = self.content_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "内容不能为空！")
            return
        
        # 检查是否已存在
        if any(item.content == content for item in self.db.favorites):
            messagebox.showinfo("提示", "该内容已存在于常用内容中！")
            return
        
        # 创建新项并添加
        new_item = ClipboardItem(
            content=content,
            format='text',
            timestamp=time.time(),
            metadata={"source": "manual_add"}
        )
        self.db.favorites.append(new_item)
        self.db.save()
        
        # 刷新列表
        self.load_favorites()
        messagebox.showinfo("成功", "已添加到常用内容！")
        self.content_text.delete(1.0, tk.END)
    
    def update_favorite(self):
        """更新选中的常用内容"""
        if not self.favorites_listbox.curselection():
            messagebox.showwarning("警告", "请先选择一个常用内容！")
            return
        
        index = self.favorites_listbox.curselection()[0]
        content = self.content_text.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showwarning("警告", "内容不能为空！")
            return
        
        # 更新内容
        self.db.favorites[index].content = content
        self.db.favorites[index].timestamp = time.time()
        self.db.favorites[index].metadata = {"source": "manual_update"}
        self.db.save()
        
        # 刷新列表
        self.load_favorites()
        messagebox.showinfo("成功", "常用内容已更新！")
    
    def delete_favorite(self):
        """删除选中的常用内容"""
        if not self.favorites_listbox.curselection():
            messagebox.showwarning("警告", "请先选择一个常用内容！")
            return
        
        index = self.favorites_listbox.curselection()[0]
        
        # 确认删除
        if messagebox.askyesno("确认", "确定要删除这个常用内容吗？"):
            del self.db.favorites[index]
            self.db.save()
            
            # 刷新列表
            self.load_favorites()
            self.content_text.delete(1.0, tk.END)
            messagebox.showinfo("成功", "常用内容已删除！")
    
    def on_close(self):
        """窗口关闭时的处理"""
        # 通知父窗口刷新显示
        if hasattr(self.parent, 'update_lists') and callable(self.parent.update_lists):
            self.parent.update_lists(
                favorites=[item.content for item in self.db.favorites],
                history=[item.content for item in self.db.history]
            )
        self.destroy()