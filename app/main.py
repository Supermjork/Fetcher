# --- Installation Shennanigains ---
#from pack_installer import install_nltk_spacy

#install_nltk_spacy()

# --- Hopefully it installed with no errors ---

# --- VSM testing ---
from tfidf_fn import doc_to_dict, doc_processor
#docs_ig = doc_to_dict("data/*.txt")
#docs_processed = doc_processor(docs_ig)

# --- VSM ---
from retrieval_models import VectorSpaceModel, BooleanIR

# pls work
#myvsm = VectorSpaceModel(docs_ig)
#query = "computer"
#top_5_v1 = myvsm.return_top_n(query, 5)
#print(f"Top 5 for {query} query: \n")
#for i, doc_score in enumerate(top_5_v1):
#    print(f"{i + 1}. Score of: {doc_score[1]:.3f}. Document Being: \'{doc_score[0]}\'")

mybool = BooleanIR("data/*.txt")

result = mybool.query("(computer or screen)")

print(result)


# --- GUI? ---
# Swapping out CustomTKinter for TTKBootStrap
#from gui_ttkbs import IR_GUI

#app = IR_GUI(title = "Definitely Professional IR System",
#             themename = "darkly")

#app.mainloop()
