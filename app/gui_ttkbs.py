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
        self.progress_queue = queue.Queue()
        self.active_threads = []

    def __setup_gui(self):
        main_container = ttk.Frame(self, padding="20")
        main_container.pack(fill=BOTH, expand=True)

        title = ttk.Label(main_container, text="Information Retrieval System", 
                        font=("Helvetica", 16, "bold"))
        title.pack(pady=(0, 20))

        # Directory selector
        directory_frame = ttk.LabelFrame(main_container, text="Document Directory", padding=10)
        directory_frame.pack(fill=X, pady=(0, 20))

        self.directory_entry = ttk.Entry(directory_frame)
        self.directory_entry.pack(side=LEFT, expand=True, fill=X, padx=(5, 10))

        self.directory_button = ttk.Button(directory_frame, text="Browse",
                                        command=self.select_directory,
                                        width=10)
        self.directory_button.pack(side=LEFT)

        # Search section
        search_frame = ttk.LabelFrame(main_container, text="Search Query", padding=10)
        search_frame.pack(fill=X, pady=(0, 20))

        self.text_bar = ttk.Entry(search_frame)
        self.text_bar.pack(side=LEFT, expand=True, fill=X, padx=(5, 10))

        self.search_button = ttk.Button(search_frame, text="Search",
                                    command=self.set_query,
                                    width=10)
        self.search_button.pack(side=LEFT)

        # Results section with fixed width ratios
        results_frame = ttk.LabelFrame(main_container, text="Search Results", padding=10)
        results_frame.pack(fill=BOTH, expand=True)

        # Set width ratios: VSM (5), Boolean (3), BM25 (2)
        self.boxes = []
        self.progress_bars = {}
        models = [
            ("Vector Space Model", 5),
            ("Boolean Model", 3),
            ("BM25 Model", 2)
        ]

        for name, weight in models:
            box_frame = ttk.Frame(results_frame)
            box_frame.pack(side=LEFT, fill=BOTH, expand=True, 
                        padx=2, pady=2, ipadx=2, ipady=2)
            box_frame.configure(width=weight)  # Set relative width

            header = ttk.Label(box_frame, text=name, anchor=CENTER)
            header.pack(fill=X)

            progress = ttk.Progressbar(box_frame, mode='determinate', 
                                    length=100, bootstyle="info")
            progress.pack(fill=X, pady=2)
            self.progress_bars[name] = progress

            # Results box with fixed width text
            box = ttk.Frame(box_frame, borderwidth=1, relief="solid")
            box.pack(fill=BOTH, expand=True)
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
        try:
            self.progress_queue.put(('Vector Space Model', 0, 'Loading documents'))
            vsm_instance = VectorSpaceModel(self.get_path())

            self.progress_queue.put(('Vector Space Model', 50, 'Processing query'))
            results = vsm_instance.return_top_n(q, top_n)

            self.progress_queue.put(('Vector Space Model', 100, 'Complete'))
            self.result_queue.put(('vsm', results))
        except Exception as e:
            self.progress_queue.put(('Vector Space Model', 0, f'Error: {str(e)}'))

    def bool_search(self, q: str):
        try:
            self.progress_queue.put(('Boolean Model', 0, 'Loading documents'))
            bool_instance = BooleanIR(self.get_path())

            self.progress_queue.put(('Boolean Model', 50, 'Processing query'))
            results = bool_instance.query(q)

            self.progress_queue.put(('Boolean Model', 100, 'Complete'))
            self.result_queue.put(('bool', results))
        except Exception as e:
            self.progress_queue.put(('Boolean Model', 0, f'Error: {str(e)}'))

    def monitor_progress(self):
        while True:
            try:
                model, progress, status = self.progress_queue.get(timeout=0.1)
                if model in self.progress_bars:
                    self.progress_bars[model]['value'] = progress
                    self.progress_bars[model]['text'] = status
            except queue.Empty:
                continue

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

        container = ttk.Frame(box)
        container.pack(fill=BOTH, expand=True, padx=1, pady=1)

        text = ttk.Text(container, wrap=WORD, width=40)
        scrollbar = ttk.Scrollbar(container, orient=VERTICAL, command=text.yview)

        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        text.pack(side=LEFT, fill=BOTH, expand=True)

        for line in content:
            text.insert(END, f"{line}\n")
        text.configure(state=DISABLED)

    def get_query(self):
        return self.__user_query

    def can_search(self):
        self.__can_search = True

    def cannot_search(self):
        self.__can_search = False