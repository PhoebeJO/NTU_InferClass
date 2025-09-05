from llama_index.readers.file import PDFReader
from llama_index.core import VectorStoreIndex, Document, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
import os, time

query_engine = None

#資料路徑
def _abs_data_path(filename: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "data", filename))
#確保路徑
def _ensure_file(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到檔案：{path}")

def build_concept_engine(embed_model, llm, persist_dir: str):
    global query_engine
    os.makedirs(persist_dir, exist_ok=True)

    # 已有storage
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        sc = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(sc, embed_model=embed_model)
        query_engine = index.as_query_engine(llm=llm, similarity_top_k=3)
        return index

    reader = PDFReader()
    p_book = _abs_data_path("MIS.pdf"); _ensure_file(p_book)
    #分句
    docs = reader.load_data(file=p_book)
    splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=150)

    #建立
    index = VectorStoreIndex.from_documents(
        documents=docs, 
        embed_model=embed_model, 
        transformations=[splitter]
    )

    index.storage_context.persist(persist_dir=persist_dir)
    query_engine = index.as_query_engine(
        llm=llm, 
        similarity_top_k=5
    )
    return index

def search_concept(query):
    res = query_engine.query(query)
    return res.response
