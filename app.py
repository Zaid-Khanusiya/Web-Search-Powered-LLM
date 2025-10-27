from flask import Flask
from flask_restful import Api
from dotenv import load_dotenv
from database import db
import os

load_dotenv()

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

from routes import *

from models import ChatHistory
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=7435)