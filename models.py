from database import db

class ChatHistory(db.Model):
    __tablename__ = 'web_search_llm_history'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(20))
    entity = db.Column(db.String(20))
    message = db.Column(db.Text)