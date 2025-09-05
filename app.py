from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from linebot import LineBot
from fastapi import FastAPI, Request, Response, status
from practice.GenPractice import GenPractice,_load_or_build_index
from checkout.CheConcept import build_concept_engine,search_concept
import uvicorn
from dotenv import load_dotenv
import os
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter


load_dotenv()

llm = Ollama(model="llama3.2:3b", request_timeout=6000)
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
line_bot = LineBot()
app = FastAPI()
user_sessions: dict[str, dict] = {}
user_topics={}
user_state = {}

CONCEPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage_concepts")
def load_or_build_concept_engine(embed_model, llm):
    from checkout.CheConcept import build_concept_engine as _build
    # 已有storage
    if os.path.exists(CONCEPT_DIR) and os.listdir(CONCEPT_DIR):
        from llama_index.core import load_index_from_storage, StorageContext
        sc = StorageContext.from_defaults(persist_dir=CONCEPT_DIR)
        index = load_index_from_storage(sc, embed_model=embed_model)
        return index.as_query_engine(llm=llm, similarity_top_k=3)
    # 沒有storage
    index = _build(embed_model=embed_model, llm=llm, persist_dir=CONCEPT_DIR)
    return index.as_query_engine(llm=llm, similarity_top_k=3)

concept_qe = load_or_build_concept_engine(embed_model, llm)
@app.post("/webhook")
async def callback(request: Request):
    body = await request.body()
    try:
        payload = line_bot.extract_message(body=body)
        print(payload)
        user_id = payload["user_id"]
        message = payload["message"]
        reply_token = payload["reply_token"]
        topic = None
        res = ""

        # 選單
        if message ==  "選單" :
            return Response(content="OK", status_code=status.HTTP_200_OK)

        # 主題
        if message in set(["Find Data", "Practice"]):
            if message == "Find Data":
                topic = "Find Data"
                res = "請問要找什麼資訊？"
            elif message == "Practice":
                topic = "Practice"
                res = "請問想要練習哪次的題目 (1, 2, 或 3)？"
                user_state["user_id"]="choosing test"
            else:
                res = "請詢問小幫手擁有的功能"
            
            user_topics[user_id] = topic
            line_bot.reply_message(reply_token=reply_token, message=res)
            return Response(content="OK", status_code=status.HTTP_200_OK)
        
        #尚未選擇主題
        if user_id not in user_topics:
            line_bot.reply_message(reply_token=reply_token, message="請先選擇主題。(搜尋'選單'以獲得小幫手功能介紹)\n")
            return Response(content="OK", status_code=status.HTTP_200_OK)
                
        topic = user_topics[user_id]
        res = ""
        if topic == "Practice":
            if user_state["user_id"] == "choosing test":
                if(int(message)<1 or int(message)>3):
                    line_bot.reply_message(reply_token, "請問想要練習哪次的題目 (1, 2, 或 3)？")
                else:
                    line_bot.reply_message(reply_token, "請輸入要練習幾題(至多10，至少3)")
                    user_state["user_id"] = "how many"
                    user_state["test"] = int(message)
                    return Response(content="OK",status_code=status.HTTP_200_OK)
            elif user_state["user_id"] == "how many":
                if int(message) <= 10 and int(message)>=3:
                    user_state["number"]=int(message)
                else:
                    line_bot.reply_message(reply_token, "請輸入要練習幾題（至多10，至少3）")
                    return Response(content="OK", status_code=status.HTTP_200_OK)
            res_text = GenPractice(embed_model=embed_model, llm=llm, test=user_state["test"],number=int(message))
            del user_state["number"], user_state["user_id"], user_state["test"]
        elif topic == "Find Data":
            res = concept_qe.query(message)
            res_text = res.response


        del user_topics[user_id] #清除資料

        line_bot.reply_message(reply_token, res_text)
        return Response(content="OK",status_code=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error handling webhook from linebot: {e}")
        return Response(content="OK", status_code=status.HTTP_200_OK)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
