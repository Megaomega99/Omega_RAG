import os
import flet as ft
from dotenv import load_dotenv

# Import page modules
from frontend.pages.login import LoginPage
from frontend.pages.register import RegisterPage
from frontend.pages.dashboard import DashboardPage
from frontend.pages.document_upload import DocumentUploadPage
from frontend.pages.document_view import DocumentViewPage
from frontend.pages.chat import ChatPage

# Load environment variables
load_dotenv()

# Default API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

def main(page: ft.Page):
    """
    Main function for the Omega RAG frontend application.
    
    Args:
        page (ft.Page): The Flet page instance
    """
    # Configure page
    page.title = "Omega RAG"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1280
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    
    # Create app state
    page.client_storage.set("api_url", API_URL)
    
    # Authentication state
    if not page.client_storage.contains_key("auth_token"):
        page.client_storage.set("auth_token", None)
    
    # Session state
    page.session.set("current_user", None)
    page.session.set("current_document", None)
    page.session.set("current_conversation", None)
    
    # Initialize the router
    def route_change(e):
        page.views.clear()
        
        # Check authentication status
        auth_token = page.client_storage.get("auth_token")
        is_authenticated = auth_token is not None
        
        # Get route
        route = page.route
        
        # Route switching
        if route == "/login" or (route == "/" and not is_authenticated):
            page.views.append(
                LoginPage(page).build()
            )
            
        elif route == "/register":
            page.views.append(
                RegisterPage(page).build()
            )
            
        elif route == "/" or route == "/dashboard":
            if not is_authenticated:
                page.go("/login")
                return
                
            page.views.append(
                DashboardPage(page).build()
            )
            
        elif route == "/upload":
            if not is_authenticated:
                page.go("/login")
                return
                
            page.views.append(
                DocumentUploadPage(page).build()
            )
            
        elif route.startswith("/document/"):
            if not is_authenticated:
                page.go("/login")
                return
                
            document_id = int(route.split("/")[-1])
            page.session.set("current_document", document_id)
            
            page.views.append(
                DocumentViewPage(page, document_id).build()
            )
            
        elif route.startswith("/chat/"):
            if not is_authenticated:
                page.go("/login")
                return
                
            # May be /chat/new or /chat/123 (conversation ID)
            if route == "/chat/new":
                conversation_id = None
            else:
                conversation_id = int(route.split("/")[-1])
                
            page.session.set("current_conversation", conversation_id)
            
            page.views.append(
                ChatPage(page, conversation_id).build()
            )
            
        else:
            # Default to dashboard for authenticated users, login for others
            if is_authenticated:
                page.views.append(
                    DashboardPage(page).build()
                )
            else:
                page.views.append(
                    LoginPage(page).build()
                )
        
        # Update the page
        page.update()
    
    # Handle view pop
    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    # Register route change handlers
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Initialize the app
    page.go(page.route)

# Start the app
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)