from flask import Flask
from flask_restful import Api
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
api = Api(app)

from routes import *

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=7435)