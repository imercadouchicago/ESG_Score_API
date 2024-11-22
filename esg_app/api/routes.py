from esg_app.utils.route_utils import home_response

def all_routes(app):
    @app.route('/', methods=['GET'])
    def home():
        return home_response()