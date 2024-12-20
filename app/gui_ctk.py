from PIL import Image
import tkinter as tk
import customtkinter as ctk

APP_TITLE = "Bootleg IR System"
MIN_WIDTH = 480
MIN_HEIGHT = 650
DEFAULT_W_H = "1200x720"

class IR_GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        # App Title
        self.title(APP_TITLE)

        # Minimum Size of the window
        self.minsize(MIN_HEIGHT,MIN_WIDTH)

        # Decide if Width or Height are resizeable
        self.resizable(True, True)

        # Default starting size of window
        self.geometry(DEFAULT_W_H)

        self.grid_columnconfigure((0, 1, 2, 3), weight = 1)
        self.grid_rowconfigure((0, 1, 2), weight = 1)

        self.yours_truly = ctk.CTkImage(light_image = Image.open('app/media/miguel.png'),
                                        dark_image = Image.open('app/media/miguel.png'),
                                        size = (300, 250))

        self.miguel = ctk.CTkLabel(master = self,
                                   text = '',
                                   image = self.yours_truly)
        
        self.miguel.grid(row = 0, column = 3)

        # Making a search bar to take query from
        self.search_bar = ctk.CTkTextbox(master = self,
                                         corner_radius = 20,
                                         width = self.winfo_width() / 3,
                                         height = 30)
        self.search_bar.grid(row = 1, column = 1, sticky = "we", columnspan = 2)

        # Making a display to the directory with documents
        self.doc_frame = ctk.CTkScrollableFrame(master = self,
                                                height = self.winfo_height())
        self.doc_frame.grid(row = 0, column = 0,
                            sticky = "nsw", rowspan = 3)

        # Retrieved Docs (amen)
        self.retr_frame = ctk.CTkScrollableFrame(master = self,
                                                 width = self.winfo_width() / 3)
        self.retr_frame.grid(row = 2, column = 1,
                             sticky = "nswe", columnspan = 3, rowspan = 1)
