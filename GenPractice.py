from llama_index.readers.file import PDFReader
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
import os

def _abs_data_path(filename: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "data", filename))

def _ensure_file(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到檔案：{path}")

def _persist_dir(test: int) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "..", "storage_practice", f"t{test}")
    os.makedirs(d, exist_ok=True)
    return d

def _load_or_build_index(embed_model, docs, persist_dir: str):
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        sc = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(sc, embed_model=embed_model)
    splitter = SentenceSplitter(chunk_size=900, chunk_overlap=120)
    index = VectorStoreIndex.from_documents(documents=docs, embed_model=embed_model, transformations=[splitter])
    index.storage_context.persist(persist_dir=persist_dir)
    return index

def GenPractice(embed_model, llm, test:int ,number, return_evidence: bool=False):
    reader = PDFReader()
    docs = []
    if test == 1:
        p1 = _abs_data_path("test1.pdf"); _ensure_file(p1)
        docs = reader.load_data(file=p1)
    elif test == 2:
        p2 = _abs_data_path("test2.pdf"); _ensure_file(p2)
        docs = reader.load_data(file=p2)
    elif test == 3:
        p31 = _abs_data_path("test3_1.pdf"); _ensure_file(p31)
        p32 = _abs_data_path("test3_2.pdf"); _ensure_file(p32)
        docs = reader.load_data(file=p31) + reader.load_data(file=p32)
    else:
        return ("請輸入 1, 2, 或 3。", []) if return_evidence else "請輸入 1, 2, 或 3。"

    persist_dir = _persist_dir(test)
    index = _load_or_build_index(embed_model, docs, persist_dir)
    query_engine = index.as_query_engine(
        llm=llm, 
        similarity_top_k=2
    )

    query = (
        f"Generate exactly {number} practice questions in English based on the provided context. "
        "Include both True/False and Multiple Choice (at least 4 options). "
        "For each question, append the correct answer and a brief explanation of why it is correct, "
        "grounded strictly in the provided context. Use this format:\n"
        "Q1. <question>\n"
        "A. <option>\nB. <option>\nC. <option>\nD. <option>\n"
        "Answer: <letter or True/False>\n"
        "Explanation(using Tradionnal Chinese): <1–2 sentences citing the relevant idea from the context>\n"
        "Be concise and unambiguous. Do not invent facts not supported by the context."
    )
    res = query_engine.query(query)
    if return_evidence:
        evid = [sn.get_text() for sn in (res.source_nodes or [])]
        return res.response, evid
    return res.response
