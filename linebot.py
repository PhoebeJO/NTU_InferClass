import requests
import os, json
from dotenv import load_dotenv
class LineBot:
    def __init__(self):
        load_dotenv()
        self.line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.line_api_reply_endpoint = "https://api.line.me/v2/bot/message/reply"
    def extract_message(self, body): # 負責解析接收到的 LINE Bot 訊息
        parsed = json.loads(body)
        print(parsed)
        event = parsed["events"][0]
        reply_token = event["replyToken"]
        message_type = event["message"]["type"]
        message_text = event["message"].get("text", "")
        user_id = event["source"]["userId"]
        group_id = event["source"]["groupId"] if event["source"]["type"] == "group" else ""
        if message_type == "text":
            return {
                "message": message_text,
                "message_type": message_type,
                "reply_token": reply_token,
                "user_id": user_id,
                "group_id": group_id
            }
        return {}
        
    def reply_message(self, reply_token, message):# 負責回應接收到的 LINE Bot 訊息
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.line_channel_access_token}"
        }
        data = {
            "replyToken": reply_token,
            "messages": [
                {
                "type": "text",
                "text": message,
                }
            ]
        }
        
        response = requests.post(self.line_api_reply_endpoint, headers=headers,data=json.dumps(data))
        print("Response: " + response.text)

                    
        

