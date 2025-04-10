import flet as ft
from frontend.services.api_client import ApiClient


class DocumentList(ft.ListView):
    def __init__(self, page: ft.Page, api_client: ApiClient):
        super().__init__(
            spacing=10,
            padding=10,
            auto_scroll=True,
        )
        self.page = page
        self.api_client = api_client
        
        # Add loading text initially
        self.controls.append(
            ft.Text("Loading documents...")
        )
    
    async def load_documents(self):
        # Clear existing items
        self.controls.clear()
        
        # Loading indicator
        self.controls.append(
            ft.Text("Loading documents...")
        )
        self.page.update()
        
        try:
            # Get documents
            documents = await self.api_client.get_documents()
            
            # Clear loading indicator
            self.controls.clear()
            
            if not documents:
                self.controls.append(
                    ft.Text("No documents yet. Upload your first document!")
                )
            else:
                # Add documents to list
                for document in documents:
                    title = document.get("title", "Untitled Document")
                    description = document.get("description", "")
                    file_type = document.get("file_type", "").upper()
                    is_processed = document.get("is_processed", False)
                    is_indexed = document.get("is_indexed", False)
                    processing_status = document.get("processing_status", "pending")
                    document_id = document.get("id")
                    
                    # Get appropriate icon
                    icon_name = ft.icons.DESCRIPTION
                    if file_type == "PDF":
                        icon_name = ft.icons.PICTURE_AS_PDF
                    elif file_type == "DOCX":
                        icon_name = ft.icons.ARTICLE
                    elif file_type == "TXT":
                        icon_name = ft.icons.TEXT_FIELDS
                    elif file_type == "MD":
                        icon_name = ft.icons.MARKDOWN
                    
                    # Get status color
                    status_color = ft.colors.BLUE_400
                    status_text = "Processing"
                    
                    if is_processed and is_indexed:
                        status_color = ft.colors.GREEN_400
                        status_text = "Ready"
                    elif processing_status == "failed":
                        status_color = ft.colors.RED_400
                        status_text = "Failed"
                    
                    self.controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(icon_name, color=status_color),
                                            ft.Text(title, weight=ft.FontWeight.BOLD),
                                            ft.Spacer(),
                                            ft.Container(
                                                content=ft.Text(
                                                    file_type,
                                                    size=12,
                                                    color=ft.colors.WHITE,
                                                    weight=ft.FontWeight.BOLD,
                                                ),
                                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                                border_radius=4,
                                                bgcolor=ft.colors.BLUE_400,
                                            ),
                                            ft.Container(
                                                content=ft.Text(
                                                    status_text,
                                                    size=12,
                                                    color=ft.colors.WHITE,
                                                    weight=ft.FontWeight.BOLD,
                                                ),
                                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                                border_radius=4,
                                                bgcolor=status_color,
                                            ),
                                        ]
                                    ),
                                    ft.Text(
                                        description if description else "No description",
                                        size=14,
                                        color=ft.colors.GREY_700,
                                    ),
                                ]
                            ),
                            padding=10,
                            border_radius=5,
                            bgcolor=ft.colors.WHITE,
                            ink=True,
                            on_click=lambda e, id=document_id: self.page.go(f"/document/{id}"),
                        )
                    )
        except Exception as ex:
            self.controls.clear()
            self.controls.append(
                ft.Text(f"Error loading documents: {str(ex)}")
            )
        
        # Update the page
        self.page.update()