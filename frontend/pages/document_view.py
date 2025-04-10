import flet as ft
from frontend.services.api_client import ApiClient
from frontend.components.navigation import Navigation


class DocumentViewPage:
    def __init__(self, page: ft.Page, document_id: int):
        self.page = page
        self.document_id = document_id
        self.api_url = page.client_storage.get("api_url")
        self.api_token = page.client_storage.get("auth_token")
        self.api_client = ApiClient(self.api_url, self.api_token)
        
        # Document data
        self.document = None
        
    def build(self) -> ft.View:
        # Create navigation bar
        self.navigation = Navigation(self.page, "documents")
        
        # Header section
        self.page_title = ft.Text(
            "Loading Document...",
            size=24,
            weight=ft.FontWeight.BOLD,
        )
        
        # Document metadata
        self.metadata_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Loading document metadata...", color=ft.colors.GREY_700),
                    ],
                    spacing=10,
                ),
                padding=20,
            ),
        )
        
        # Chat with document button
        self.chat_button = ft.ElevatedButton(
            text="Chat with this Document",
            icon=ft.icons.CHAT,
            bgcolor=ft.colors.BLUE_400,
            color=ft.colors.WHITE,
            on_click=self.start_chat,
            disabled=True,
        )
        
        # Create main layout
        main_content = ft.Container(
            content=ft.Column(
                [
                    self.page_title,
                    ft.Divider(),
                    self.metadata_card,
                    ft.Row(
                        [
                            self.chat_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            expand=True,
        )
        
        # Create view
        view = ft.View(
            route=f"/document/{self.document_id}",
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
        
        # Set up async loading
        view.did_mount = self.did_mount
        return view
    
    async def did_mount(self):
        """Load document data when view is mounted."""
        try:
            # Get document data
            document = await self.api_client.get_document(self.document_id)
            
            if "error" in document:
                self.page_title.value = "Error Loading Document"
                self.metadata_card.content.content.controls = [
                    ft.Text(f"Error: {document.get('error', 'Document not found')}", color=ft.colors.RED_500)
                ]
                self.page.update()
                return
                
            # Store document data
            self.document = document
            
            # Update title
            self.page_title.value = document.get("title", "Document")
            
            # Update metadata card
            description = document.get("description", "")
            file_type = document.get("file_type", "").upper()
            is_processed = document.get("is_processed", False)
            is_indexed = document.get("is_indexed", False)
            processing_status = document.get("processing_status", "pending")
            original_filename = document.get("original_filename", "")
            created_at = document.get("created_at", "")
            
            # Format date
            if created_at:
                from datetime import datetime
                date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_at = date_obj.strftime("%Y-%m-%d %H:%M")
            
            # Get status text and color
            status_text = "Processing"
            status_color = ft.colors.BLUE_400
            
            if is_processed and is_indexed:
                status_text = "Ready"
                status_color = ft.colors.GREEN_400
            elif processing_status == "failed":
                status_text = "Failed"
                status_color = ft.colors.RED_400
            
            # Update metadata card content
            self.metadata_card.content.content.controls = [
                ft.Row(
                    [
                        ft.Icon(
                            ft.icons.PICTURE_AS_PDF if file_type == "PDF" else 
                            ft.icons.ARTICLE if file_type == "DOCX" else
                            ft.icons.TEXT_FIELDS if file_type == "TXT" else
                            ft.icons.MARKDOWN if file_type == "MD" else
                            ft.icons.DESCRIPTION,
                            color=status_color,
                            size=40,
                        ),
                        ft.Column(
                            [
                                ft.Text(document.get("title", ""), size=20, weight=ft.FontWeight.BOLD),
                                ft.Text(description if description else "No description", color=ft.colors.GREY_700),
                            ],
                            spacing=5,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text(
                                status_text,
                                size=14,
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border_radius=15,
                            bgcolor=status_color,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("File Type:", weight=ft.FontWeight.BOLD),
                                ft.Text(file_type),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            [
                                ft.Text("Original Filename:", weight=ft.FontWeight.BOLD),
                                ft.Text(original_filename),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            [
                                ft.Text("Created At:", weight=ft.FontWeight.BOLD),
                                ft.Text(created_at),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                ),
            ]
            
            # Enable chat button if document is ready
            if is_processed and is_indexed:
                self.chat_button.disabled = False
            
            # Update the page
            self.page.update()
            
        except Exception as ex:
            self.page_title.value = "Error Loading Document"
            self.metadata_card.content.content.controls = [
                ft.Text(f"Error: {str(ex)}", color=ft.colors.RED_500)
            ]
            self.page.update()
    
    def start_chat(self, e):
        """Start a new chat with this document."""
        # Start new chat with pre-selected document
        self.page.session.set("chat_document_id", self.document_id)
        self.page.go("/chat/new")