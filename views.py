from flask import request
from flask_restful import Resource
import os
import json
from google import genai
import requests
from bs4 import BeautifulSoup

GOOGLE_GENAI_API_KEY=os.getenv("GOOGLE_GENAI_API_KEY")
GOOGLE_SEARCH_API_KEY=os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID=os.getenv("GOOGLE_SEARCH_ENGINE_ID")

GC_CLIENT = genai.Client(api_key=GOOGLE_GENAI_API_KEY)
GC_MODEL = 'gemini-2.5-flash-lite'



def get_token_spending(response):
    print(f"Input Tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Output Tokens: {response.usage_metadata.candidates_token_count}")
    print(f"Total Tokens: {response.usage_metadata.total_token_count}")

class Home(Resource):
    def get(self):
        return {'msg':'This is home page!'}


class WebSearchResponse(Resource):
    def post(self):
        json_data = request.get_json()

        user_prompt = json_data.get("user_prompt")

        no_of_top_links = json_data.get("no_of_top_links")
        if not no_of_top_links:
            no_of_top_links = 10

        page = json_data.get("page")
        if not page:
            page = 1
        
        fast_search = json_data.get("fast_search",'enable')

        base_url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_SEARCH_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': user_prompt,
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

            return {'links_visited':links_list,'response':response.text}