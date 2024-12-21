import ttkbootstrap as ttk
from retrieval_models import VectorSpaceModel, BooleanIR
from ttkbootstrap.constants import *
from tkinter import filedialog

class IR_GUI(ttk.Window):
    def __init__(self,
                 title: str = None,
                 themename: str = "default",
                 size: str = "720x480",
                 **kwargs):
        super().__init__(title = title, themename = themename, **kwargs)

        self.geometry(size)

        for k, v in kwargs.items():
            setattr(self, k, v)

        # Directory selector components
        self.directory_frame = ttk.Frame(self, padding=10)
        self.directory_frame.pack(pady=(10, 0))

        self.directory_entry = ttk.Entry(self.directory_frame, width=50)
        self.directory_entry.pack(side=LEFT, padx=(0, 10))

        self.directory_button = ttk.Button(
            self.directory_frame, text="Browse", command=self.select_directory
        )
        self.directory_button.pack(side=LEFT)

        self.__path: str = None
        self.__user_query: str = None
        self.__can_search: bool = True
        self.__vsm_top_n = None
        self.__bool_results = None

        self.search_frame = ttk.Frame(self, padding = 10)
        self.search_frame.pack(pady = 20)

        self.text_bar = ttk.Entry(self.search_frame, width = 50)
        self.text_bar.pack(side = LEFT, padx = (0, 10))

        self.search_button = ttk.Button(self.search_frame,
                                        text = "Search",
                                        command = self.set_query)
        self.search_button.pack(side = LEFT)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=TOP, fill=BOTH, expand=True)

        # Create three horizontal boxes
        self.boxes = []
        for i in range(3):
            box_names = ["VSM Results", "Boolean Results", "BM25 Results"]
            box = ttk.Frame(bottom_frame, borderwidth=2, relief="solid", padding=10)
            box.pack(side=LEFT, fill=BOTH, expand=True, padx=5)  # Stacks boxes horizontally
            self.boxes.append(box)

            # Add label to indicate the box number (for testing purposes)
            ttk.Label(box, text=f"{box_names[i]}", anchor=CENTER).pack()

    def select_directory(self):
        # Open directory dialog and set the directory entry
        directory = filedialog.askdirectory()
        self.set_path(directory + "/*.txt")
        if directory:
            self.directory_entry.delete(0, 'end')
            self.directory_entry.insert(0, directory)

    def set_path(self, input_path: str):
        self.__path = input_path

    def get_path(self):
        return self.__path

    def set_query(self):
        if self.__can_search:
            # Store the user query to be passed
            # To the retrieval models
            self.__user_query = self.text_bar.get()

            # Clear the search bar
            self.text_bar.delete(0, "end")

            # Halt the ability to input another query
            # Until later (i.e. when the searching finishes)
            self.cannot_search()

            # Print what the user's query was (in terminal)
            print(f"Set instance query: {self.__user_query}")

            self.vector_search(self.get_query())

            self.bool_search(self.get_query())

            self.can_search()
        else:
            print("Cannot Search, Halted.")

    def get_query(self):
        return self.__user_query

    def can_search(self):
        self.__can_search = True

    def cannot_search(self):
        self.__can_search = False

    def set_vsm_topn(self, top_n):
        self.__vsm_top_n = top_n

    def get_vsm_topn(self):
        return self.__vsm_top_n

    def vector_search(self,
                      q: str,
                      top_n: int = 10):
        vsm_instance = VectorSpaceModel(self.get_path())

        self.set_vsm_topn(vsm_instance.return_top_n(q, top_n))

    def set_bool_results(self, results):
        self.__bool_results = results

    def get_bool_results(self):
        return self.__bool_results

    def bool_search(self,
                    q: str):
        bool_instance = BooleanIR(self.get_path())

        self.set_bool_results(bool_instance.query(q))
