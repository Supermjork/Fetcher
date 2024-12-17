import tkinter as tk
import customtkinter as ctk

APP_TITLE = "Bootleg IR System"
MIN_WIDTH = 480
MIN_HEIGHT = 650
DEFAULT_W_H = "1200x720"

class IR_GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.minsize(MIN_HEIGHT,MIN_WIDTH)
        self.resizable(True, True)
        self.geometry(DEFAULT_W_H)
