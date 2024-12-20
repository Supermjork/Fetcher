import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class IR_GUI(ttk.Window):
    def __init__(self,
                 title: str = None,
                 themename: str = "default",
                 size: str = "1200x720",
                 **kwargs):
        super().__init__(title = title, themename = themename, **kwargs)

        self.geometry(size)

        for k, v in kwargs.items():
            setattr(self, k, v)
