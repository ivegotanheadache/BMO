from sentence_transformers import SentenceTransformer, util

import numpy as np
import os
from datetime import datetime

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
BASEPATH = os.path.dirname(os.path.abspath(__file__))


with open(f"{BASEPATH}/memories/diary.txt", "r") as f:
    diary_list = f.read().split("[page]\n")

diary_embs= model.encode(diary_list,convert_to_tensor=True)
diary_db={}
for i in diary_list:
    day, s = i.split("[date]")
    d = datetime.strptime(day, "%Y-%m-%d")
    diary_db.update({d:s})


def cosine(prompt):
    print("hello")
    probe_emb=model.encode(prompt,convert_to_tensor=True)
    cosine_scores = util.cos_sim(probe_emb,diary_embs)
    top = 0 
    for i,sentence in enumerate(diary_list):
        print(sentence, cosine_scores[0][i].item())
        if cosine_scores[0][i].item() > cosine_scores[0][top].item():
            top = i
    print(cosine_scores[0], diary_list[top])
    
    if cosine_scores[0][top]>0.6:
        return f"Hai traccia del tempo. Per rispondere alla domanda, ecco quello che ricordi:{diary_list[top]}"
    else:
        print("Not very similar event found")
        
def extractday(date):
    d = datetime.strptime(date, "%Y-%m-%d")
    try:
        return f"Hai traccia del tempo. Per rispondere alla domanda, ecco quello che ricordi di aver fatto: {diary_db[d]}"
    except:
        pass    

   
print("cic")     
#cosine("Hai mai letto un libro di Umberto Eco?")        
extractday("2026-01-15")
