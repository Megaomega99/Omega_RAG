import flet as ft
import requests
import os
import traceback

# API configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1")

def main(page: ft.Page):
    # Basic page configuration
    page.title = "RAG SaaS"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Define variables in function scope
    TOKEN = ""
    current_view = "login"  # Instead of tabs, track the current view
    
    # Login form components
    email_input = ft.TextField(label="Email", width=300)
    password_input = ft.TextField(label="Password", password=True, width=300)
    login_error_text = ft.Text("", color="red")
    
    # Document upload components
    title_input = ft.TextField(label="Document Title", width=300)
    picked_files = ft.Text("No file selected")
    
    # Query components
    query_input = ft.TextField(
        label="Ask a question about your documents",
        multiline=True,
        min_lines=2,
        max_lines=4,
        width=600
    )
    
    # Results containers
    documents_list = ft.Column(spacing=10)
    query_result = ft.Text("", selectable=True)
    query_history = ft.Column(spacing=10)
    
    # File picker setup
    def handle_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            picked_files.value = f"Selected file: {e.files[0].name}"
        else:
            picked_files.value = "No file selected"
        page.update()
    
    file_picker = ft.FilePicker(on_result=handle_file_picked)
    page.overlay.append(file_picker)
    
    # Main content container (will be updated to show different views)
    main_content = ft.Container(
        content=None,
        expand=True,
        alignment=ft.alignment.center
    )
    
    # Navigation bar (alternative to Tabs which causes the error)
    nav_bar = ft.Row(
        visible=False,  # Hidden until login
        controls=[
            ft.ElevatedButton(
                text="Documents",
                on_click=lambda _: switch_view("documents")
            ),
            ft.ElevatedButton(
                text="Ask Questions",
                on_click=lambda _: switch_view("questions")
            ),
            ft.ElevatedButton(
                text="Logout",
                on_click=lambda _: handle_logout()
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )
    
    # Function to switch between views
    def switch_view(view_name):
        nonlocal current_view
        current_view = view_name
        
        if view_name == "login":
            # Reset login form
            email_input.value = ""
            password_input.value = ""
            login_error_text.value = ""
            nav_bar.visible = False
            
            # Set login view content
            main_content.content = ft.Column(
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
            
        elif view_name == "documents":
            # Load documents data
            fetch_documents()
            
            # Set documents view content
            main_content.content = ft.Column([
                ft.Text("Document Management", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Upload Document", size=18),
                        title_input,
                        picked_files,
                        ft.Row([
                            ft.ElevatedButton(
                                "Select File",
                                on_click=lambda _: file_picker.pick_files()
                            ),
                            ft.ElevatedButton(
                                "Upload",
                                on_click=handle_upload
                            )
                        ]),
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.colors.GREY_400),
                    border_radius=5
                ),
                ft.Container(height=20),
                ft.Text("Your Documents", size=18),
                documents_list
            ])
            
        elif view_name == "questions":
            # Load query history
            fetch_query_history()
            
            # Set questions view content
            main_content.content = ft.Column([
                ft.Text("Ask Questions", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        query_input,
                        ft.ElevatedButton("Ask", on_click=handle_ask_question),
                        ft.Container(height=10),
                        ft.Text("Answer:", size=16, weight=ft.FontWeight.BOLD),
                        query_result
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.colors.GREY_400),
                    border_radius=5
                ),
                ft.Container(height=20),
                ft.Text("Query History", size=18),
                query_history
            ])
        
        # Update the page
        page.update()
    
    # Authentication handlers
    def handle_login(e):
        nonlocal TOKEN
        
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
                nav_bar.visible = True
                switch_view("documents")
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
                login_error_text.value = f"Registration failed: {response.status_code}"
                login_error_text.color = "red"
            
            page.update()
        except Exception as ex:
            login_error_text.value = f"Error: {str(ex)}"
            page.update()
    
    def handle_logout():
        nonlocal TOKEN
        TOKEN = ""
        switch_view("login")
    
    # Document management handlers
    def handle_upload(e):
        if not title_input.value or "No file selected" in picked_files.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please select a file and enter a title"))
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            upload_file = file_picker.result.files[0]
            
            with open(upload_file.path, "rb") as file_data:
                files = {"file": (upload_file.name, file_data, "application/octet-stream")}
                response = requests.post(
                    f"{API_BASE_URL}/documents/",
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
                    page.snack_bar = ft.SnackBar(ft.Text(f"Upload failed: {response.status_code}"))
                    page.snack_bar.open = True
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"))
            page.snack_bar.open = True
            print(f"Upload error details: {traceback.format_exc()}")
        
        page.update()
    
    def fetch_documents():
        try:
            response = requests.get(
                f"{API_BASE_URL}/documents/",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            
            if response.status_code == 200:
                documents = response.json()
                documents_list.controls.clear()
                
                if not documents:
                    documents_list.controls.append(
                        ft.Text("No documents found. Upload some documents to get started.")
                    )
                else:
                    for doc in documents:
                        status = "Processed" if doc.get("processed", False) else "Processing..."
                        doc_item = ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(doc["title"], weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Status: {status}")
                                ]),
                                ft.Row([
                                    ft.OutlinedButton(
                                        "Delete",
                                        on_click=lambda e, doc_id=doc["id"]: delete_document(doc_id)
                                    )
                                ], alignment=ft.MainAxisAlignment.END)
                            ]),
                            padding=10,
                            border=ft.border.all(1, ft.colors.GREY_400),
                            border_radius=5,
                            margin=ft.margin.only(bottom=10)
                        )
                        documents_list.controls.append(doc_item)
                
                page.update()
        except Exception as ex:
            documents_list.controls.clear()
            documents_list.controls.append(
                ft.Text(f"Error loading documents: {str(ex)}", color="red")
            )
            page.update()
            print(f"Document fetch error: {traceback.format_exc()}")
    
    def delete_document(document_id):
        try:
            response = requests.delete(
                f"{API_BASE_URL}/documents/{document_id}",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            
            if response.status_code == 200:
                page.snack_bar = ft.SnackBar(ft.Text("Document deleted successfully"))
                page.snack_bar.open = True
                fetch_documents()
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"Delete failed: {response.status_code}"))
                page.snack_bar.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"))
            page.snack_bar.open = True
            page.update()
    
    # Query handlers
    def handle_ask_question(e):
        if not query_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter a question"))
            page.snack_bar.open = True
            page.update()
            return
        
        query_result.value = "Processing your question..."
        page.update()
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/queries/",
                headers={"Authorization": f"Bearer {TOKEN}"},
                params={"question": query_input.value}
            )
            
            if response.status_code == 200:
                result = response.json()
                query_result.value = result["answer"]
                query_input.value = ""  # Clear the input
                fetch_query_history()  # Refresh history
            else:
                query_result.value = f"Error: {response.status_code} - {response.text}"
            
            page.update()
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
                
                if not queries:
                    query_history.controls.append(
                        ft.Text("No queries found. Ask some questions to get started.")
                    )
                else:
                    for query in queries:
                        query_item = ft.Container(
                            content=ft.Column([
                                ft.Text("Question:", weight=ft.FontWeight.BOLD),
                                ft.Text(query["question"]),
                                ft.Text("Answer:", weight=ft.FontWeight.BOLD),
                                ft.Text(query["answer"], selectable=True),
                                ft.Text(f"Created: {query['created_at']}", 
                                       size=12, italic=True)
                            ]),
                            padding=10,
                            border=ft.border.all(1, ft.colors.GREY_400),
                            border_radius=5,
                            margin=ft.margin.only(bottom=10)
                        )
                        query_history.controls.append(query_item)
                
                page.update()
        except Exception as ex:
            query_history.controls.clear()
            query_history.controls.append(
                ft.Text(f"Error loading history: {str(ex)}", color="red")
            )
            page.update()
    
    # Set up the page structure
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("RAG SaaS Application", size=28, weight=ft.FontWeight.BOLD),
                nav_bar,
                main_content
            ]),
            padding=20
        )
    )
    
    # Initialize with login view
    switch_view("login")

# Run the application
if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=7000)