import os, json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ES_URL   = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "school_knowledge")
EMBED_DIMS = int(os.getenv("EMBED_DIMS", "3072"))  # bạn có thể đổi nếu model khác

def build_index_body(dims: int):
    return {
        "settings": {
            "analysis": {
                "analyzer": {
                    "vn_icu": {
                        "type": "custom",
                        "tokenizer": "icu_tokenizer",
                        "filter": ["lowercase", "icu_folding"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id":   {"type": "keyword"},
                "title":    {"type": "keyword"},
                "text":     {"type": "text", "analyzer": "vn_icu"},
                "vector": {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": "cosine",
                    "index_options": {"type": "hnsw", "m": 16, "ef_construction": 128}
                },
                "page_from":      {"type": "integer"},
                "page_to":        {"type": "integer"},
                "effective_date": {"type": "date"},
                "version":        {"type": "keyword"},
                "tags":           {"type": "keyword"}
            }
        }
    }

def reset_index():
    es = Elasticsearch(ES_URL)

    if es.indices.exists(index=ES_INDEX):
        print(f"🗑️  Xóa index cũ: {ES_INDEX}")
        es.indices.delete(index=ES_INDEX, ignore_unavailable=True)

    print(f"📦 Tạo lại index: {ES_INDEX} (dims={EMBED_DIMS})")
    body = build_index_body(EMBED_DIMS)
    es.indices.create(index=ES_INDEX, body=body)
    print("✅ Done.")

if __name__ == "__main__":
    reset_index()
