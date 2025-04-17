import flet as ft
import requests
import os
import traceback
import sys

# API configuration with environment variable support
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1")

def main(page: ft.Page):
    # Configure basic page properties
    page.title = "RAG SaaS"
    page.padding = 20
    
    # Error display for debugging
    error_text = ft.Text("", color="red", selectable=True)
    
    try:
        # Basic login form components
        email_input = ft.TextField(label="Email")
        password_input = ft.TextField(label="Password", password=True)
        login_button = ft.ElevatedButton("Login")
        register_button = ft.ElevatedButton("Register")
        
        # Add components to page with minimal nesting
        page.add(
            ft.Text("RAG SaaS - Login", size=24),
            email_input,
            password_input,
            ft.Row([login_button, register_button]),
            error_text
        )
        
        # Simple login handler
        def handle_login(e):
            try:
                error_text.value = "Attempting login..."
                page.update()
                
                response = requests.post(
                    f"{API_BASE_URL}/auth/token",
                    data={
                        "username": email_input.value,
                        "password": password_input.value
                    }
                )
                
                if response.status_code == 200:
                    error_text.value = "Login successful!"
                    page.update()
                else:
                    error_text.value = f"Login failed: {response.status_code}"
                    page.update()
            except Exception as ex:
                error_text.value = f"Error: {str(ex)}\n{traceback.format_exc()}"
                page.update()
        
        # Connect handlers
        login_button.on_click = handle_login
        
    except Exception as ex:
        # Capture initialization errors
        error_details = f"Initialization error: {str(ex)}\n{traceback.format_exc()}"
        page.add(ft.Text(error_details, selectable=True))

if __name__ == "__main__":
    try:
        ft.app(target=main, view=ft.WEB_BROWSER, port=7000)
    except Exception as ex:
        # Log top-level errors to stderr
        print(f"Critical error: {str(ex)}", file=sys.stderr)
        traceback.print_exc()