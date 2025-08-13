import requests
from common.app_config import config
from common.app_logger import logger
import jwt


class OAuthClient:
    def __init__(self, config):
        self.config = config

    def get_google_token(self, code: str, redirect_uri: str, code_verifier: str):
        """
        Exchange Google OAuth authorization code for access token
        
        Args:
            code: Authorization code from Google OAuth
            redirect_uri: Redirect URI used in the OAuth flow
            
        Returns:
            dict: Token response from Google
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': self.config.GOOGLE_CLIENT_ID,
            'client_secret': self.config.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier
        }

        response = requests.post(token_url, data=token_data)
        logger.info(response.json())
        response.raise_for_status()
        
        return response.json()

    def get_google_user_info(self, access_token: str):
        """
        Get Google user info using access token
        
        Args:
            access_token: Access token from Google OAuth
            
        Returns:
            dict: User info response from Google
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        userinfo_url = 'https://openidconnect.googleapis.com/v1/userinfo'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(userinfo_url, headers=headers)
        logger.info(response.json())
        response.raise_for_status()
        
        return response.json()


    def get_microsoft_token(self, code: str, redirect_uri: str, code_verifier: str):
        """
        Exchange Microsoft OAuth authorization code for access token.
        Uses PKCE code_verifier if provided.
        """
        token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        token_data = {
            'client_id': self.config.MICROSOFT_CLIENT_ID,
            'client_secret': self.config.MICROSOFT_CLIENT_SECRET,
            'scope': 'User.Read',
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier
        }

        logger.info(token_data)

        response = requests.post(token_url, data=token_data)
        logger.info(response.json())
        response.raise_for_status()
        return response.json()


    def get_microsoft_user_info(self, id_token: str):
        claims = jwt.decode(id_token, options={"verify_signature": False})
        return {
            "email": claims.get("upn"),
            "name": claims.get("name", "")
        }