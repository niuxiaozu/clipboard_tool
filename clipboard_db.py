import json
import os
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class ClipboardItem:
    content: str
    format: str
    timestamp: float
    metadata: dict = None

class ClipboardDB:
    def __init__(self, file_path="clipboard_history.json"): 
        self.file_path  = file_path
        self.history  = []
        self.favorites  = []
        self.load() 

    def save(self):
        data = {
            "history": [asdict(item) for item in self.history[-100:]], 
            "favorites": [asdict(item) for item in self.favorites] 
        }
        with open(self.file_path,  'w') as f:
            json.dump(data,  f)

    def load(self):
        if os.path.exists(self.file_path): 
            with open(self.file_path)  as f:
                data = json.load(f) 
                self.history  = [ClipboardItem(**item) for item in data.get('history',  [])]
                self.favorites  = [ClipboardItem(**item) for item in data.get('favorites',  [])]

    def add_history(self, item: ClipboardItem):
        if not any(i.content  == item.content  for i in self.history): 
            self.history.append(item) 
            self.save() 

    def add_favorite(self, item: ClipboardItem):
        if not any(i.content  == item.content  for i in self.favorites): 
            self.favorites.append(item) 
            self.save()