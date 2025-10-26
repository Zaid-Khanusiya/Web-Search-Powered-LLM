from flask_restful import Resource

class Home(Resource):
    def get(self):
        return {'msg':'This is home page!'}