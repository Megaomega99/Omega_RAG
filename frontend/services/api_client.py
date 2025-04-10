import httpx
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class ApiClient:
    """
    API client for communicating with the backend REST API.
    """
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            base_url (str): Base URL of the API
            token (Optional[str]): Authentication token
        """
        self.base_url = base_url
        self.token = token
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers including authentication if available.
        
        Returns:
            Dict[str, str]: Headers dictionary
        """
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api{endpoint}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers(), timeout=30.0)
                
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", response.text)
                    except:
                        error_detail = response.text
                        
                    return {"error": error_detail, "status_code": response.status_code}
                    
                return response.json()
        except httpx.RequestError as e:
            return {"error": f"Connection error: {str(e)}", "status_code": 500}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "status_code": 500}
        
    async def post(self, endpoint: str, data: Dict[str, Any] = None, files: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a POST request to the API.
        
        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any], optional): Request data
            files (Dict[str, Any], optional): Files to upload
            
        Returns:
            Dict[str, Any]: API response
        """
        url = f"{self.base_url}/api{endpoint}"
        
        if files:
            # For file uploads, don't use JSON content type
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
                
            # Convert data to form data
            form_data = {}
            if data:
                form_data.update(data)
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=headers, 
                    data=form_data,
                    files=files
                )
                
                if response.status_code >= 400:
                    return {"error": response.text, "status_code": response.status_code}
                    
                return response.json()
        else:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=self._get_headers(), 
                    json=data
                )
                
                if response.status_code >= 400:
                    return {"error": response.text, "status_code": response.status_code}
                    
                return response.json()
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request to the API.
        
        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any]): Request data
            
        Returns:
            Dict[str, Any]: API response
        """
        url = f"{self.base_url}/api{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url, 
                headers=self._get_headers(), 
                json=data
            )
            
            if response.status_code >= 400:
                return {"error": response.text, "status_code": response.status_code}
                
            return response.json()
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a DELETE request to the API.
        
        Args:
            endpoint (str): API endpoint
            
        Returns:
            Dict[str, Any]: API response
        """
        url = f"{self.base_url}/api{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self._get_headers())
            
            if response.status_code >= 400:
                return {"error": response.text, "status_code": response.status_code}
                
            return response.json()
            
    # Authentication methods
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Log in a user and obtain an authentication token.
        
        Args:
            email (str): User email
            password (str): User password
            
        Returns:
            Dict[str, Any]: Login response with token
        """
        # For login, we need to use form data
        url = f"{self.base_url}/api/auth/login"
        form_data = {"username": email, "password": password}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code >= 400:
                return {"error": response.text, "status_code": response.status_code}
                
            result = response.json()
            # Update token for subsequent requests
            self.token = result.get("access_token")
            return result
    
    async def register(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email (str): User email
            password (str): User password
            full_name (str): User's full name
            
        Returns:
            Dict[str, Any]: Registration response
        """
        data = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        
        return await self.post("/auth/register", data)
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the current user's profile.
        
        Returns:
            Dict[str, Any]: User profile
        """
        return await self.get("/auth/me")
    
    # Document methods
    async def get_documents(self) -> List[Dict[str, Any]]:
        """
        Get the user's documents.
        
        Returns:
            List[Dict[str, Any]]: List of documents
        """
        response = await self.get("/documents")
        if "error" in response:
            return []
        return response
    
    async def get_document(self, document_id: int) -> Dict[str, Any]:
        """
        Get a specific document.
        
        Args:
            document_id (int): Document ID
            
        Returns:
            Dict[str, Any]: Document data
        """
        return await self.get(f"/documents/{document_id}")
    
    async def upload_document(self, title: str, description: str, file_path: str) -> Dict[str, Any]:
        """
        Upload a new document.
        
        Args:
            title (str): Document title
            description (str): Document description
            file_path (str): Path to the file to upload
            
        Returns:
            Dict[str, Any]: Upload response
        """
        # Prepare file for upload
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        file_name = file_path.split("/")[-1]
        
        files = {"file": (file_name, file_content)}
        data = {"title": title, "description": description}
        
        return await self.post("/documents", data=data, files=files)
    
    # RAG methods
    async def query_rag(
        self, 
        query: str, 
        conversation_id: Optional[int] = None,
        document_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            query (str): User query
            conversation_id (Optional[int]): Conversation ID for context
            document_ids (Optional[List[int]]): Document IDs to use for context
            
        Returns:
            Dict[str, Any]: RAG response
        """
        data = {"query": query}
        
        if conversation_id is not None:
            data["conversation_id"] = conversation_id
            
        if document_ids is not None:
            data["document_ids"] = document_ids
            
        return await self.post("/rag/query", data)
    
    async def get_conversations(self) -> List[Dict[str, Any]]:
        """
        Get the user's conversations.
        
        Returns:
            List[Dict[str, Any]]: List of conversations
        """
        response = await self.get("/rag/conversations")
        if "error" in response:
            return []
        return response
    
    async def get_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """
        Get a specific conversation.
        
        Args:
            conversation_id (int): Conversation ID
            
        Returns:
            Dict[str, Any]: Conversation data with messages
        """
        return await self.get(f"/rag/conversations/{conversation_id}")