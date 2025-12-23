# scripts/quick_search.py
import os, json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import google.generativeai as genai

load_dotenv()
es = Elasticsearch(os.getenv("ES_URL","http://localhost:9200"))
IDX = os.getenv("ES_INDEX","school_knowledge")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("EMBED_MODEL","text-embedding-004")

question = "Điều kiện để thí sinh đăng ký xét tuyển đại học là gì?"
keyword = "điều kiện"

# embed câu hỏi
emb = genai.embed_content(model=MODEL, content=question)["embedding"]

# hybrid: must keyword (BM25) + knn vector
body = {
  "size": 5,
  "query": {
    "bool": {
      "must": [{"match": {"text": keyword}}],
      "should": [
        {"match": {"text": question}},
        {"knn": {"vector": {"vector": emb, "k": 50}}}
      ]
    }
  },
  "_source": ["text","title","page_from","page_to"]
}
res = es.search(index=IDX, body=body)
for i, hit in enumerate(res["hits"]["hits"], 1):
    src = hit["_source"]
    print(f"#{i} score={hit['_score']:.3f}  {src['title']} p.{src['page_from']}-{src['page_to']}")
    print(src["text"][:300], "...\n")
