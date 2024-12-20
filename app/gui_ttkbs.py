import ttkbootstrap as ttk
from retrieval_models import VectorSpaceModel
from ttkbootstrap.constants import *

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

        self.__user_query: str = None
        self.__can_search: bool = True
        self.__vsm_top_n = None

        self.search_frame = ttk.Frame(self, padding = 10)
        self.search_frame.pack(pady = 20)

        self.text_bar = ttk.Entry(self.search_frame, width = 50)
        self.text_bar.pack(side = LEFT, padx = (0, 10))

        self.search_button = ttk.Button(self.search_frame,
                                        text = "Search",
                                        command = self.set_query)
        self.search_button.pack(side = LEFT)

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
                      documents: dict[str, str],
                      top_n: int = 10):
        vsm_instance = VectorSpaceModel(documents)

        self.set_vsm_topn(vsm_instance.return_top_n(q, top_n))
