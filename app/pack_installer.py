import os
import nltk
import spacy
import spacy.cli
import spacy.cli.download

NLTK_LIB_PATH = os.path.join("venv_ir", "Lib", "nltk_data")

# Defining download function
def download_nltk_libs():
    libraries = {
        os.path.join("corpora", "stopwords"): "stopwords",
        os.path.join("corpora","wordnet"): "wordnet",
        os.path.join("tokenizers", "punkt"): "punkt"
    }

    for _, package in libraries.items():
        try:
            nltk.data.find(package)
            print(f"{package.capitalize()} data exists.")
        except LookupError:
            print(f"Downloading {package}...")

            nltk.download(package, download_dir=NLTK_LIB_PATH)
        except Exception as e:
            print(f"Unexpected error checking {package}: {e}")

def install_nltk_spacy():
    try:
        os.makedirs(NLTK_LIB_PATH, exist_ok=True)
        print(f"Using NLTK data directory: {NLTK_LIB_PATH}")
        download_nltk_libs()
    except PermissionError:
        print(f"Permission denied: Unable to create or write to directory \
              '{NLTK_LIB_PATH}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Won't bother error checking tbh
    # path for curiousity
    # "venv_ir\Lib\site-packages\en_core_web_sm\en_core_web_sm-3.8.0"
    try:
        loaded_model = spacy.load("en_core_web_sm")
        print(f"SpaCy's \"en_core_web_sm\" model is at: {loaded_model._path}")
        del loaded_model
    except OSError:
        spacy.cli.download("en_core_web_sm")
        print(f"SpaCy downloaded \"en_core_web_sm\" at: {spacy.load("en_core_web_sm")._path}")
