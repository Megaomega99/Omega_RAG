import os
import tempfile
import flet as ft
from frontend.services.api_client import ApiClient
from frontend.components.navigation import Navigation


class DocumentUploadPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = page.client_storage.get("api_url")
        self.api_token = page.client_storage.get("auth_token")
        self.api_client = ApiClient(self.api_url, self.api_token)
        
        # File paths
        self.temp_dir = tempfile.gettempdir()
        self.selected_file = None
        
    def build(self) -> ft.View:
        # Create navigation bar
        self.navigation = Navigation(self.page, "documents")
        
        # Header section
        self.page_title = ft.Text(
            "Upload Document",
            size=24,
            weight=ft.FontWeight.BOLD,
        )
        
        # Form fields
        self.title_field = ft.TextField(
            label="Document Title",
            hint_text="Enter a title for your document",
            width=400,
            border_color=ft.colors.BLUE_400,
            required=True,
        )
        
        self.description_field = ft.TextField(
            label="Description",
            hint_text="Enter a description (optional)",
            width=400,
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=ft.colors.BLUE_400,
        )
        
        # File picker
        self.file_picker = ft.FilePicker(
            on_result=self.on_file_selected
        )
        self.page.overlay.append(self.file_picker)
        
        self.file_button = ft.ElevatedButton(
            "Select File",
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: self.file_picker.pick_files(
                allowed_extensions=["pdf", "txt", "docx", "md"],
                allow_multiple=False
            )
        )
        
        self.file_text = ft.Text("No file selected")
        
        # Upload button
        self.upload_button = ft.ElevatedButton(
            text="Upload Document",
            icon=ft.icons.CLOUD_UPLOAD,
            bgcolor=ft.colors.BLUE_400,
            color=ft.colors.WHITE,
            disabled=True,
            on_click=self.upload_document,
        )
        
        # Status text
        self.status_text = ft.Text(
            color=ft.colors.RED_500,
            size=14,
            visible=False,
        )
        
        # Create upload form
        upload_form = ft.Container(
            content=ft.Column(
                [
                    self.title_field,
                    self.description_field,
                    ft.Row(
                        [
                            self.file_button,
                            self.file_text,
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.status_text,
                    self.upload_button,
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            width=500,
        )
        
        # Create main layout
        main_content = ft.Container(
            content=ft.Column(
                [
                    self.page_title,
                    ft.Divider(),
                    ft.Row(
                        [upload_form],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            expand=True,
        )
        
        # Create view
        return ft.View(
            route="/upload",
            controls=[
                ft.Column(
                    [
                        self.navigation,
                        main_content,
                    ],
                    expand=True,
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            padding=0,
            bgcolor=ft.colors.BLUE_50,
        )
    
    def on_file_selected(self, e: ft.FilePickerResultEvent):
        """Handle file selection."""
        if not e.files:
            # No file selected
            self.file_text.value = "No file selected"
            self.selected_file = None
            self.upload_button.disabled = True
        else:
            # File selected
            file = e.files[0]
            self.file_text.value = file.name
            self.selected_file = file.path
            
            # Enable upload button if title is also filled
            self.upload_button.disabled = not self.title_field.value
            
        self.page.update()
    
    async def upload_document(self, e):
        """Upload the document to the API."""
        # Validate form
        if not self.title_field.value:
            self.status_text.value = "Please enter a title"
            self.status_text.visible = True
            self.page.update()
            return
            
        if not self.selected_file:
            self.status_text.value = "Please select a file"
            self.status_text.visible = True
            self.page.update()
            return
        
        # Disable button during upload
        self.upload_button.disabled = True
        self.upload_button.text = "Uploading..."
        self.status_text.visible = False
        self.page.update()
        
        try:
            # Call upload API
            result = await self.api_client.upload_document(
                title=self.title_field.value,
                description=self.description_field.value or "",
                file_path=self.selected_file
            )
            
            if "error" in result:
                self.status_text.value = f"Upload failed: {result.get('error', 'Unknown error')}"
                self.status_text.visible = True
            else:
                # Upload successful, navigate to document view
                document_id = result.get("id")
                self.page.go(f"/document/{document_id}")
                return
        except Exception as ex:
            self.status_text.value = f"Upload failed: {str(ex)}"
            self.status_text.visible = True
        
        # Re-enable button
        self.upload_button.disabled = False
        self.upload_button.text = "Upload Document"
        self.page.update()