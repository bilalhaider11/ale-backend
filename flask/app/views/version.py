from flask_restx import Namespace, Resource
from app.helpers.response import get_success_response
from common.repositories.factory import RepositoryFactory
from common.app_config import config
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

        repo_factory = RepositoryFactory(config)
        connection = repo_factory.get_db_connection()

        with connection:
            query = "SELECT * FROM db_version"
            results = connection.execute_query(query)
            db_version = results[0].get('version')

        return get_success_response(version=VERSION, db_version=db_version)