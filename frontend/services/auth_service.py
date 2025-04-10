# frontend/services/auth_service.py
import flet as ft
from typing import Dict, Any, Optional
from frontend.services.api_client import ApiClient


class AuthService:
    """
    Authentication service for the frontend.
    """
    
    def __init__(self, page: ft.Page, api_client: ApiClient):
        """
        Initialize the authentication service.
        
        Args:
            page (ft.Page): The Flet page
            api_client (ApiClient): API client instance
        """
        self.page = page
        self.api_client = api_client
        
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user.
        
        Args:
            email (str): User email
            password (str): User password
            
        Returns:
            Dict[str, Any]: Login result
        """
        try:
            # Call login API
            result = await self.api_client.login(email, password)
            
            if "error" not in result:
                # Save token
                token = result.get("access_token")
                self.page.client_storage.set("auth_token", token)
                
                # Get user profile
                self.api_client.token = token
                user_profile = await self.api_client.get_user_profile()
                
                if "error" not in user_profile:
                    self.page.session.set("current_user", user_profile)
                    return {"success": True, "user": user_profile}
                    
            return {"success": False, "error": result.get("error", "Login failed")}
        except Exception as ex:
            return {"success": False, "error": str(ex)}
    
    async def register(
        self, 
        email: str, 
        password: str, 
        full_name: str
    ) -> Dict[str, Any]:
        """
        Register new user.
        
        Args:
            email (str): User email
            password (str): User password
            full_name (str): User full name
            
        Returns:
            Dict[str, Any]: Registration result
        """
        try:
            # Call register API
            result = await self.api_client.register(email, password, full_name)
            
            if "error" not in result:
                # Auto login after registration
                login_result = await self.login(email, password)
                if login_result["success"]:
                    return {"success": True, "user": login_result["user"]}
                return {"success": True, "message": "Registration successful"}
                
            return {"success": False, "error": result.get("error", "Registration failed")}
        except Exception as ex:
            return {"success": False, "error": str(ex)}
    
    def logout(self) -> None:
        """
        Logout user.
        """
        # Clear auth token
        self.page.client_storage.set("auth_token", None)
        
        # Clear session
        self.page.session.set("current_user", None)
        
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        token = self.page.client_storage.get("auth_token")
        return token is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current user.
        
        Returns:
            Optional[Dict[str, Any]]: Current user or None
        """
        return self.page.session.get("current_user")