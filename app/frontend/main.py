import flet as ft
import requests
import os
from typing import List, Dict

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def main(page: ft.Page):
    page.title = "RAG SaaS"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Define variables in function scope
    TOKEN = ""
    is_logged_in = False
    
    # Login form
    email_input = ft.TextField(label="Email", width=300)
    password_input = ft.TextField(label="Password", password=True, width=300)
    login_error_text = ft.Text("", color="red")
    
    # Document upload form
    title_input = ft.TextField(label="Document Title", width=300)
    picked_files = ft.Text()
    
    # Query input
    query_input = ft.TextField(
        label="Ask a question about your documents",
        multiline=True,
        min_lines=2,
        width=600
    )
    
    # Results containers
    documents_list = ft.Column(spacing=10)
    query_result = ft.Text("", selectable=True)
    query_history = ft.Column(spacing=10)
    
    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            picked_files.value = f"Selected file: {e.files[0].name}"
        else:
            picked_files.value = "No file selected"
        page.update()
        
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)
    
    def upload_files(e):
        if not picked_files.value or not title_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please select a file and enter a title"))
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            upload_file = file_picker.result.files[0]
            
            with open(upload_file.path, "rb") as file_data:
                files = {"file": (upload_file.name, file_data, "application/octet-stream")}
                response = requests.post(
                    f"{API_BASE_URL}/documents",
                    headers={"Authorization": f"Bearer {TOKEN}"},
                    files=files,
                    data={"title": title_input.value}
                )
                
                if response.status_code == 200:
                    page.snack_bar = ft.SnackBar(ft.Text("Document uploaded successfully"))
                    page.snack_bar.open = True
                    title_input.value = ""
                    picked_files.value = "No file selected"
                    fetch_documents()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Upload failed: {response.text}"))
                    page.snack_bar.open = True
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(e)}"))
            page.snack_bar.open = True
        
        page.update()
    
    def handle_login(e):
        # Use function scope variables instead of nonlocal
        nonlocal TOKEN, is_logged_in  # This is now valid since we're accessing parent function variables
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/token",
                data={
                    "username": email_input.value,
                    "password": password_input.value
                }
            )
            
            if response.status_code == 200:
                TOKEN = response.json().get("access_token")
                is_logged_in = True
                login_error_text.value = ""
                # Switch to main view
                page.clean()
                setup_main_view()
                page.update()
            else:
                login_error_text.value = "Invalid email or password"
                page.update()
        except Exception as ex:
            login_error_text.value = f"Error: {str(ex)}"
            page.update()
    
    def handle_register(e):
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/register",
                params={
                    "email": email_input.value,
                    "password": password_input.value
                }
            )
            
            if response.status_code == 201:
                login_error_text.value = "Registration successful. Please login."
                login_error_text.color = "green"
            else:
                login_error_text.value = response.json().get("detail", "Registration failed")
                login_error_text.color = "red"
            
            page.update()
        except Exception as ex:
            login_error_text.value = f"Error: {str(ex)}"
            page.update()
    
    def fetch_documents():
        try:
            response = requests.get(
                f"{API_BASE_URL}/documents",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            
            if response.status_code == 200:
                documents = response.json()
                documents_list.controls.clear()
                
                for doc in documents:
                    status = "Processed" if doc["processed"] else "Processing..."
                    doc_item = ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(doc["title"], weight=ft.FontWeight.BOLD),
                                ft.Text(f"Status: {status}")
                            ]),
                            ft.Row([
                                ft.TextButton("Delete", 
                                             on_click=lambda e, doc_id=doc["id"]: delete_document(doc_id))
                            ], alignment=ft.MainAxisAlignment.END)
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_400),
                        border_radius=5
                    )
                    documents_list.controls.append(doc_item)
                
                page.update()
        except Exception as ex:
            print(f"Error fetching documents: {str(ex)}")
    
    def delete_document(document_id):
        try:
            response = requests.delete(
                f"{API_BASE_URL}/documents/{document_id}",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            
            if response.status_code == 200:
                fetch_documents()  # Refresh the list
        except Exception as ex:
            print(f"Error deleting document: {str(ex)}")
    
    def ask_question(e):
        if not query_input.value:
            return
        
        query_result.value = "Thinking..."
        page.update()
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/queries",
                headers={"Authorization": f"Bearer {TOKEN}"},
                params={"question": query_input.value}
            )
            
            if response.status_code == 200:
                result = response.json()
                query_result.value = result["answer"]
                page.update()
                
                # Refresh query history
                fetch_query_history()
        except Exception as ex:
            query_result.value = f"Error: {str(ex)}"
            page.update()
    
    def fetch_query_history():
        try:
            response = requests.get(
                f"{API_BASE_URL}/queries/history",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            
            if response.status_code == 200:
                queries = response.json()
                query_history.controls.clear()
                
                for query in queries:
                    query_item = ft.Container(
                        content=ft.Column([
                            ft.Text(query["question"], weight=ft.FontWeight.BOLD),
                            ft.Text(query["answer"], selectable=True)
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_400),
                        border_radius=5
                    )
                    query_history.controls.append(query_item)
                
                page.update()
        except Exception as ex:
            print(f"Error fetching query history: {str(ex)}")
    
    def setup_login_view():
        login_view = ft.Column(
            [
                ft.Text("RAG SaaS - Login", size=25, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                email_input,
                password_input,
                login_error_text,
                ft.Container(height=20),
                ft.Row(
                    [
                        ft.ElevatedButton("Login", on_click=handle_login),
                        ft.ElevatedButton("Register", on_click=handle_register)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        page.add(
            ft.Container(
                content=login_view,
                alignment=ft.alignment.center,
                expand=True
            )
        )
    
    def setup_main_view():
        # Create tab for documents
        documents_tab = ft.Container(
            content=ft.Column([
                ft.Text("Upload Document", size=20, weight=ft.FontWeight.BOLD),
                title_input,
                picked_files,
                ft.Row([
                    ft.ElevatedButton(
                        "Select File",
                        icon=ft.icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files()
                    ),
                    ft.ElevatedButton(
                        "Upload",
                        on_click=upload_files
                    )
                ]),
                ft.Divider(),
                ft.Text("Your Documents", size=20, weight=ft.FontWeight.BOLD),
                documents_list
            ]),
            padding=20
        )
        
        # Create tab for querying
        query_tab = ft.Container(
            content=ft.Column([
                ft.Text("Ask a Question", size=20, weight=ft.FontWeight.BOLD),
                query_input,
                ft.ElevatedButton("Ask", on_click=ask_question),
                ft.Container(height=20),
                ft.Text("Answer:", size=16, weight=ft.FontWeight.BOLD),
                query_result,
                ft.Divider(),
                ft.Text("Query History", size=20, weight=ft.FontWeight.BOLD),
                query_history
            ]),
            padding=20
        )
        
        # Create tabs
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Documents", content=documents_tab),
                ft.Tab(text="Ask Questions", content=query_tab),
            ]
        )
        
        # Create page layout
        page.add(
            ft.AppBar(
                title=ft.Text("RAG SaaS Application"),
                actions=[
                    ft.IconButton(icon=ft.icons.LOGOUT, on_click=lambda _: handle_logout())
                ]
            ),
            tabs
        )
        
        # Fetch initial data
        fetch_documents()
        fetch_query_history()
    
    def handle_logout():
        nonlocal TOKEN, is_logged_in
        TOKEN = ""
        is_logged_in = False
        page.clean()
        setup_login_view()
        page.update()
    
    # Initialize the app with login view
    setup_login_view()

# Run the app
if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=7000)