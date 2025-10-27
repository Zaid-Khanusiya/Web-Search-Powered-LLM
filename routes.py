from app import app,api
from views import *

api.add_resource(Home,'/')
api.add_resource(WebSearchResponse,'/web-search-response')