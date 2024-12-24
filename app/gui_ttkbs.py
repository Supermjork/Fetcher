import os
import queue
import threading
import pandas as pd
import seaborn as sns
import ttkbootstrap as ttk
import matplotlib.pyplot as plt

from wordcloud import WordCloud
from collections import Counter
from preprocessing import preprocess
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from retrieval_models import VectorSpaceModel, BooleanIR, BM25
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class IR_GUI(ttk.Window):
    def __init__(self, title: str = None, themename: str = "darkly", size: str = "820x720", **kwargs):
        super().__init__(title=title, themename=themename, **kwargs)
        self.geometry(size)
        self.minsize(720, 480)
        self.__setup_state()
        self.__setup_gui()

        # Start progress monitoring thread
        self.progress_monitor = threading.Thread(target=self.monitor_progress, daemon=True)
        self.progress_monitor.start()

    def __setup_state(self):
        self.__path = None
        self.__user_query = None
        self.__can_search = True
        self.__vsm_top_n = None
        self.__bool_results = None
        self.__bm25_results = None
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.active_threads = []

    def __setup_gui(self):
        self.style.configure('Results.TFrame', background='#2f3640')

        main_container = ttk.Frame(self, padding="20")
        main_container.pack(fill=BOTH, expand=True)

        # Enhanced header with status indicator
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=X, pady=(0, 20))

        title = ttk.Label(header_frame, text="Information Retrieval System",
                         font=("Helvetica", 16, "bold"))
        title.pack(side=LEFT)

        self.status_label = ttk.Label(header_frame, text="Ready", 
                                    bootstyle="success")
        self.status_label.pack(side=RIGHT)

        # Directory selector with validation
        directory_frame = ttk.LabelFrame(main_container, text="Document Directory", 
                                       padding=10)
        directory_frame.pack(fill=X, pady=(0, 20))

        self.directory_entry = ttk.Entry(directory_frame)
        self.directory_entry.pack(side=LEFT, expand=True, fill=X, padx=(5, 10))

        self.directory_button = ttk.Button(directory_frame, text="Browse",
                                         command=self.select_directory,
                                         bootstyle="info-outline")
        self.directory_button.pack(side=LEFT)

        # Search section with auto-disable
        search_frame = ttk.LabelFrame(main_container, text="Search Query", 
                                    padding=10)
        search_frame.pack(fill=X, pady=(0, 20))

        self.text_bar = ttk.Entry(search_frame)
        self.text_bar.pack(side=LEFT, expand=True, fill=X, padx=(5, 10))
        self.text_bar.bind('<Return>', lambda e: self.set_query())

        self.search_button = ttk.Button(search_frame, text="Search",
                                      command=self.set_query,
                                      bootstyle="primary")
        self.search_button.pack(side=LEFT)

        # Enhanced results section
        results_frame = ttk.LabelFrame(main_container, text="Search Results", 
                                     padding=10)
        results_frame.pack(fill=BOTH, expand=True)

        models = [
            ("Vector Space Model", 3, "primary"),
            ("Boolean Model", 3, "success"),
            ("BM25 Model", 3, "info")
        ]

        self.boxes = []
        self.progress_bars = {}

        for name, weight, style in models:
            box_frame = ttk.Frame(results_frame)
            box_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

            header = ttk.Label(box_frame, text=name, font=("Helvetica", 10, "bold"))
            header.pack(fill=X)

            # Add status label above progress bar
            status_label = ttk.Label(box_frame, text="Ready")
            status_label.pack(fill=X)

            progress = ttk.Progressbar(box_frame, mode='determinate',
                                    length=100, bootstyle=style)
            progress.pack(fill=X, pady=2)

            self.progress_bars[name] = {
                'bar': progress,
                'status': status_label
            }

            box = ttk.Frame(box_frame, style='Results.TFrame')
            box.pack(fill=BOTH, expand=True)
            self.boxes.append(box)

    def select_directory(self):
        try:
            directory = filedialog.askdirectory()
            if directory:
                if not any(f.endswith('.txt') for f in os.listdir(directory)):
                    messagebox.showwarning("No Text Files", 
                                         "Selected directory contains no .txt files")
                    return

                self.set_path(directory + "/*.txt")
                self.directory_entry.delete(0, 'end')
                self.directory_entry.insert(0, directory)
                self.status_label.configure(text="Directory loaded", 
                                          bootstyle="success")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load directory: {str(e)}")
            self.status_label.configure(text="Error loading directory", 
                                      bootstyle="danger")


    def set_path(self, input_path: str):
        self.__path = input_path

    def get_path(self):
        return self.__path

    def set_query(self):
        if not self.__can_search:
            messagebox.showinfo("Processing", "Please wait for current search to complete")
            return

        if not self.__path:
            messagebox.showwarning("No Directory", "Please select a directory first")
            return

        query = self.text_bar.get().strip()
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a search query")
            return

        self.__user_query = query
        self.text_bar.delete(0, "end")
        self.cannot_search()
        self.status_label.configure(text="Searching...", bootstyle="warning")

        # Reset progress bars
        for progress_bar in self.progress_bars.values():
            progress_bar['value'] = 0

        # Start search threads
        self.active_threads = [
            threading.Thread(target=self.vector_search, args=(query,), daemon=True),
            threading.Thread(target=self.bool_search, args=(query,), daemon=True),
            threading.Thread(target=self.BM25_search, args=(query,), daemon=True)
        ]

        for thread in self.active_threads:
            thread.start()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_searches, 
                                             daemon=True)
        self.monitor_thread.start()

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

    def BM25_search(self, q: str):
        try:
            self.progress_queue.put(('BM25 Model', 0, 'Loading documents'))
            bm25_instance = BM25(self.get_path())

            self.progress_queue.put(('BM25 Model', 50, 'Processing query'))
            results = bm25_instance.compute_bm25(q)

            self.progress_queue.put(('BM25 Model', 100, 'Complete'))
            self.result_queue.put(('bm25', results))
        except Exception as e:
            self.progress_queue.put(('BM25 Model', 0, f'Error: {str(e)}'))

    def monitor_searches(self):
        while any(thread.is_alive() for thread in self.active_threads):
            self.update()

        self.active_threads.clear()
        self.update_boxes()
        self.can_search()
        self.status_label.configure(text="Ready", bootstyle="success")

    def monitor_progress(self):
        while True:
            try:
                model, progress, status = self.progress_queue.get(timeout=0.1)
                if model in self.progress_bars:
                    self.progress_bars[model]['bar']['value'] = progress
                    self.progress_bars[model]['status'].configure(text=status)
            except queue.Empty:
                continue

    def update_boxes(self):
        while not self.result_queue.empty():
            result_type, results = self.result_queue.get()
            if result_type == 'vsm':
                self.__vsm_top_n = results
            elif result_type == 'bool':
                self.__bool_results = results
            elif result_type == 'bm25':
                self.__bm25_results = results

        # Update VSM Results
        vsm_content = self.__vsm_top_n or []
        self.update_box(self.boxes[0], "VSM Results", vsm_content, has_score=True)

        # Update Boolean Results
        bool_content = [(doc, 1.0) for doc in (self.__bool_results or [])]
        self.update_box(self.boxes[1], "Boolean Results", bool_content, has_score=False)

        # BM25 Results
        bm25_content = self.__bm25_results or []
        self.update_box(self.boxes[2], "BM25 Results", bm25_content, has_score=True)

    def update_box(self, box, title, content, has_score=True):
        for widget in box.winfo_children():
            widget.destroy()

        container = ttk.Frame(box)
        container.pack(fill=BOTH, expand=True, padx=1, pady=1)

        text = ttk.Text(container, wrap=WORD, width=40, height=15)
        scrollbar = ttk.Scrollbar(container, orient=VERTICAL, command=text.yview)

        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        text.pack(side=LEFT, fill=BOTH, expand=True)

        # Add instruction text at the top
        text.tag_configure("instruction", foreground="gray")
        text.insert(END, "Click 📊 to view visualizations\n\n", "instruction")

        if not content:
            text.insert(END, "No results found.")
        else:
            for item in content:
                if isinstance(item, tuple):
                    doc_name, score = item
                    frame = ttk.Frame(text)
                    text.window_create(END, window=frame)

                    # Document name (truncated if too long)
                    doc_label = ttk.Label(frame, text=f"{doc_name[:25]}...", font=("Helvetica", 9))
                    doc_label.pack(side=LEFT)

                    # Score (if applicable)
                    if has_score:
                        score_label = ttk.Label(frame, text=f"{score:.3f}", bootstyle="success")
                        score_label.pack(side=LEFT, padx=5)

                    # Visualization button
                    viz_btn = ttk.Button(frame, text="📊", 
                                       command=lambda d=doc_name: self.create_doc_menu(d, frame),
                                       bootstyle="info-outline")
                    viz_btn.pack(side=RIGHT, padx=2)

                    text.insert(END, '\n')
                else:
                    text.insert(END, f"{item}\n")

        text.configure(state=DISABLED)

    def get_query(self):
        return self.__user_query

    def can_search(self):
        self.__can_search = True

    def cannot_search(self):
        self.__can_search = False

    def create_doc_menu(self, doc_name, parent):
        menu = ttk.Menu(parent)
        menu.add_command(label="Word Cloud", 
                        command=lambda: self.show_wordcloud(doc_name))
        menu.add_command(label="Word Frequency", 
                        command=lambda: self.show_frequency(doc_name))
        menu.add_command(label="Query Similarity", 
                        command=lambda: self.show_similarity(doc_name))

        # Show the menu at the current mouse position
        try:
            menu.tk_popup(parent.winfo_pointerx(), parent.winfo_pointery())
        finally:
            menu.grab_release()

    def show_wordcloud(self, doc_name):
        with open(f"{os.path.dirname(self.get_path())}/{doc_name}", 'r') as f:
            text = f.read()

        wordcloud = WordCloud(width=800, height=400, 
                            background_color='white').generate(text)

        self.show_plot_window("Word Cloud", wordcloud)

    def show_frequency(self, doc_name, len_lim: int = 100_000):
        try:
            with open(f"{os.path.dirname(self.get_path())}/{doc_name}", 'r') as f:
                if len_lim:
                    text = f.read(len_lim)
                else:
                    text = f.read()

                word_freq = {}
                text_preprocessed = preprocess(text)
                for word in text_preprocessed:
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Get top 20 words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            df = pd.DataFrame(top_words, columns=['Word', 'Frequency'])

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=df, x='Frequency', y='Word', ax=ax)
            plt.tight_layout()

            self.show_plot_window("Word Frequency", fig)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate word frequency: {str(e)}")

    def show_similarity(self, doc_name):
        if not self.__user_query:
            messagebox.showwarning("No Query", 
                                "Please perform a search first.")
            return

        # Get similarity score from VSM results
        score = next((score for doc, score in self.__bm25_results 
                    if doc == doc_name), 0)

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(['Similarity'], [score])
        ax.set_ylim(0, 1)

        self.show_plot_window("Query Similarity", fig)

    def show_plot_window(self, title, plot_obj):
        window = ttk.Toplevel(self)
        window.title(title)
        window.geometry("800x600")

        # Handle window closing
        def on_closing():
            plt.close('all')  # Close all matplotlib figures
            window.destroy()  # Destroy the window

        window.protocol("WM_DELETE_WINDOW", on_closing)

        toolbar_frame = ttk.Frame(window)
        toolbar_frame.pack(fill=X)

        save_btn = ttk.Button(toolbar_frame, text="Save Plot",
                             command=lambda: self.save_plot(plot_obj),
                             bootstyle="info-outline")
        save_btn.pack(side=RIGHT, padx=5, pady=5)

        if isinstance(plot_obj, WordCloud):
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(plot_obj)
            ax.axis('off')
        else:
            fig = plot_obj  # For pre-created figures

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
