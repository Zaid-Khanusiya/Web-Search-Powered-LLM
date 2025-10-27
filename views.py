from flask import request
from flask_restful import Resource
import os
import json
from google import genai
import requests
from bs4 import BeautifulSoup
from models import *
# from database import db
import uuid

# ------------------------------------------------------------

GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

GC_CLIENT = genai.Client(api_key = GOOGLE_GENAI_API_KEY)
GC_MODEL = 'gemini-2.5-flash-lite'

# ------------------------------------------------------------

def get_token_spending(response):
    print(f"Input Tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Output Tokens: {response.usage_metadata.candidates_token_count}")
    print(f"Total Tokens: {response.usage_metadata.total_token_count}")

# ------------------------------------------------------------

def add_chat_to_db(data_dict):
    new_chat = ChatHistory(chat_id=data_dict['chat_id'],
                           entity=data_dict['entity'],
                           message=data_dict['message'])
    db.session.add(new_chat)
    db.session.commit()
    return True

# ------------------------------------------------------------

def get_chat_history(chat_id):
    chats = ChatHistory.query.filter_by(chat_id=chat_id).all()
    chat_list = []
    for chat in chats:
        chat_list.append({
            'entity': chat.entity,
            'message': chat.message
        })
    # print(chat_list)
    return chat_list

# ------------------------------------------------------------

def get_search_query(user_query, previous_chats_list=[]):
    prompt = f"""
User: {user_query}
History: {previous_chats_list}
Output only a short, clear search query.
Try to keep it as near as what a real user would search considering their previous chat
context & other variables. Just try to keep search query as near as possible to a real world user.
Examples:
Q: what is release date of new iphone? → Latest iPhone release date
Q: tell me elon musk age → Elon Musk age
Q: who won last fifa world cup? → FIFA World Cup 2022 winner
Query:
"""
    response = GC_CLIENT.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt
    )
    return response.text

# ------------------------------------------------------------

class Home(Resource):
    def get(self):
        return {'msg':'This is home page!'}

# ------------------------------------------------------------

class WebSearchResponse(Resource):
    def post(self):
        """
        Fast search enabled will get results within 4-6 sec depending on internet speed.
        With fast search it only takes in the title and top content of web page instead
        of full web-page. but is still accurate upto maybe around 85% +- 5%

        And with fast search disable it will get content of all top web pages and then respond,
        it takes approx 15-20 sec also depending on your internet speed.

        Use fast search mostly it will work, but for detailed queries consider disabling it.
        """
        json_data = request.get_json()

        user_prompt = json_data.get("user_prompt")
        no_of_top_links = json_data.get("no_of_top_links",10)
        page = json_data.get("page",1)
        chat_id = json_data.get("chat_id")
        fast_search = json_data.get("fast_search",'enable')
        
        if not chat_id:
            chat_id = uuid.uuid4().hex[:8]
        
        previous_chats_list = get_chat_history(chat_id=chat_id)
        
        search_query = get_search_query(user_query=user_prompt,previous_chats_list=previous_chats_list)
        print("SEARCH_QUERY:::",search_query)

        base_url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_SEARCH_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': search_query,
            'num': no_of_top_links,
            'page': page
        }
        data = requests.get(base_url,params=params).json()

        search_items = data.get("items")

        if fast_search == 'enable':
            content_list = []
            for item in search_items:
                content_list.append({
                    'link':item['link'],
                    'title':item['title'],
                    'snippet':item['snippet']
                })
            
            response = GC_CLIENT.models.generate_content(
                model=GC_MODEL,
                contents=json.dumps([{
                    'user_query': user_prompt,
                    'web_search_content': content_list
                }])
            )
            get_token_spending(response=response)
            add_chat_to_db({'chat_id':chat_id,'entity':'user','message':user_prompt})
            add_chat_to_db({'chat_id':chat_id,'entity':'model','message':response.text})

            return {'web_content':content_list,'response':response.text}
            
        else:
            links_list = []
            for item in search_items:
                links_list.append(item['link'])

            content_list = []
            for link in links_list:
                try:
                    html = requests.get(link, timeout=5).text
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                    content_list.append({
                        'url': link,
                        'content': text
                    })
                except Exception:
                    print("Error getting link:", link)

            response = GC_CLIENT.models.generate_content(
                model=GC_MODEL,
                contents=json.dumps([{
                    'user_query': user_prompt,
                    'web_search_content': content_list
                }])
            )
            get_token_spending(response=response)
            add_chat_to_db({'chat_id':chat_id,'entity':'user','message':user_prompt})
            add_chat_to_db({'chat_id':chat_id,'entity':'model','message':response.text})

            return {'links_visited':links_list,'response':response.text}

# ------------------------------------------------------------