import ttkbootstrap as ttk
from retrieval_models import VectorSpaceModel, BooleanIR
from ttkbootstrap.constants import *
from tkinter import filedialog
import threading
import queue

class IR_GUI(ttk.Window):
    def __init__(self, title: str = None, themename: str = "default", size: str = "720x480", **kwargs):
        super().__init__(title=title, themename=themename, **kwargs)
        self.geometry(size)
        self.__setup_gui()
        self.__setup_state()
        
    def __setup_state(self):
        self.__path = None
        self.__user_query = None
        self.__can_search = True
        self.__vsm_top_n = None
        self.__bool_results = None
        self.result_queue = queue.Queue()
        self.active_threads = []

    def __setup_gui(self):
        # Directory selector
        self.directory_frame = ttk.Frame(self, padding=10)
        self.directory_frame.pack(pady=(10, 0))
        self.directory_entry = ttk.Entry(self.directory_frame, width=50)
        self.directory_entry.pack(side=LEFT, padx=(0, 10))
        self.directory_button = ttk.Button(self.directory_frame, text="Browse", command=self.select_directory)
        self.directory_button.pack(side=LEFT)

        # Search components
        self.search_frame = ttk.Frame(self, padding=10)
        self.search_frame.pack(pady=20)
        self.text_bar = ttk.Entry(self.search_frame, width=50)
        self.text_bar.pack(side=LEFT, padx=(0, 10))
        self.search_button = ttk.Button(self.search_frame, text="Search", command=self.set_query)
        self.search_button.pack(side=LEFT)

        # Results area
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=TOP, fill=BOTH, expand=True)
        self.boxes = []
        box_names = ["VSM Results", "Boolean Results", "BM25 Results"]
        for name in box_names:
            box = ttk.Frame(bottom_frame, borderwidth=2, relief="solid", padding=10)
            box.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
            ttk.Label(box, text=name, anchor=CENTER).pack()
            self.boxes.append(box)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.set_path(directory + "/*.txt")
            self.directory_entry.delete(0, 'end')
            self.directory_entry.insert(0, directory)

    def set_path(self, input_path: str):
        self.__path = input_path

    def get_path(self):
        return self.__path

    def set_query(self):
        if not self.__can_search:
            print("Cannot Search, Halted.")
            return

        self.__user_query = self.text_bar.get()
        self.text_bar.delete(0, "end")
        self.cannot_search()
        
        # Start search threads
        threads = [
            threading.Thread(target=self.vector_search, args=(self.get_query(),), daemon=True),
            threading.Thread(target=self.bool_search, args=(self.get_query(),), daemon=True)
        ]
        
        for thread in threads:
            thread.start()
            self.active_threads.append(thread)
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_searches, daemon=True)
        self.monitor_thread.start()

    def monitor_searches(self):
        while any(thread.is_alive() for thread in self.active_threads):
            self.update()  # Keep GUI responsive
        
        self.active_threads.clear()
        self.update_boxes()
        self.can_search()

    def vector_search(self, q: str, top_n: int = 10):
        vsm_instance = VectorSpaceModel(self.get_path())
        results = vsm_instance.return_top_n(q, top_n)
        self.result_queue.put(('vsm', results))

    def bool_search(self, q: str):
        bool_instance = BooleanIR(self.get_path())
        results = bool_instance.query(q)
        self.result_queue.put(('bool', results))

    def update_boxes(self):
        while not self.result_queue.empty():
            result_type, results = self.result_queue.get()
            if result_type == 'vsm':
                self.__vsm_top_n = results
            elif result_type == 'bool':
                self.__bool_results = results

        # Update VSM Results
        vsm_content = [f"{doc:<50}{similarity:>10.3f}" for doc, similarity in (self.__vsm_top_n or [])] or ["No results found."]
        self.update_box(self.boxes[0], "VSM Results", vsm_content)

        # Update Boolean Results
        bool_content = [doc for doc in (self.__bool_results or [])] or ["No results found."]
        self.update_box(self.boxes[1], "Boolean Results", bool_content)

        # BM25 Results
        self.update_box(self.boxes[2], "BM25 Results", ["BM25 Results pending implementation."])

    def update_box(self, box, title, content):
        for widget in box.winfo_children():
            widget.destroy()
        ttk.Label(box, text=title, anchor="center", font=("Helvetica", 12, "bold")).pack()
        for line in content:
            ttk.Label(box, text=line, anchor="w", justify="left", wraplength=300).pack(fill=BOTH, expand=True)

    def get_query(self):
        return self.__user_query

    def can_search(self):
        self.__can_search = True

    def cannot_search(self):
        self.__can_search = False