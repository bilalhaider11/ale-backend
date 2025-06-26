from flask_restx import Namespace, Resource
from app.helpers.response import get_success_response
import toml


# Create the version namespace
version_api = Namespace('version', description="Version-related APIs")

@version_api.route('')
class Version(Resource):
    def get(self):

        # Read the version from pyproject.toml
        try:
            with open("pyproject.toml", "r") as toml_file:
                pyproject = toml.load(toml_file)
            VERSION = pyproject["tool"]["poetry"]["version"]
        except Exception as e:
            VERSION = f"Error reading version: {str(e)}"

        return get_success_response(version=VERSION)