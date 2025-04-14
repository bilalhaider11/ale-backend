from flask_restx import Namespace, Resource
from app.helpers.response import get_success_response
from app.helpers.decorators import login_required

# Create the organization blueprint
person_api = Namespace('person', description="Person-related APIs")


@person_api.route('/me')
class Me(Resource):
    
    @login_required()
    def get(self, person):
        return get_success_response(person=person)
