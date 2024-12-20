# --- Installation Shennanigains ---
from pack_installer import install_nltk_spacy

install_nltk_spacy()

# --- Hopefully it installed with no errors ---

# --- Load the preprocessing stuff ---
from preprocessing import preprocess

# testing
print(preprocess("it's ya boi, big mjørkurion, here with u <3"))

# --- GUI? ---
# Swapping out CustomTKinter for TTKBootStrap
from gui_ttkbs import IR_GUI

app = IR_GUI(title = "Definitely Professional IR System",
             themename = "darkly",
             size = "1200x720")

app.mainloop()
