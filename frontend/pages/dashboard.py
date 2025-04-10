import flet as ft
from frontend.services.api_client import ApiClient
from frontend.components.navigation import Navigation
from frontend.components.document_list import DocumentList


class DashboardPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = page.client_storage.get("api_url")
        self.api_token = page.client_storage.get("auth_token")
        self.api_client = ApiClient(self.api_url, self.api_token)
        
        # Get current user
        self.current_user = page.session.get("current_user")
        
    def build(self) -> ft.View:
        # Create navigation bar
        self.navigation = Navigation(self.page, "dashboard")
        
        # Document section
        self.documents_title = ft.Text(
            "Your Documents",
            size=24,
            weight=ft.FontWeight.BOLD,
        )
        
        self.upload_button = ft.ElevatedButton(
            text="Upload New Document",
            icon=ft.icons.UPLOAD_FILE,
            bgcolor=ft.colors.BLUE_400,
            color=ft.colors.WHITE,
            on_click=lambda _: self.page.go("/upload"),
        )
        
        # Document list
        self.document_list = DocumentList(self.page, self.api_client)
        
        # Conversations section
        self.conversations_title = ft.Text(
            "Recent Conversations",
            size=24,
            weight=ft.FontWeight.BOLD,
        )
        
        self.new_chat_button = ft.ElevatedButton(
            text="New Conversation",
            icon=ft.icons.CHAT,
            bgcolor=ft.colors.GREEN_400,
            color=ft.colors.WHITE,
            on_click=lambda _: self.page.go("/chat/new"),
        )
        
        # Conversation list
        self.conversations_list = ft.ListView(
            spacing=10,
            padding=10,
            height=300,
        )
        
        # Create main layout
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self.documents_title,
                            ft.Spacer(),
                            self.upload_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.document_list,
                        padding=10,
                        border_radius=10,
                        bgcolor=ft.colors.BLUE_50,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            self.conversations_title,
                            ft.Spacer(),
                            self.new_chat_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.conversations_list,
                        padding=10,
                        border_radius=10,
                        bgcolor=ft.colors.GREEN_50,
                        expand=True,
                    ),
                ],
                spacing=15,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
        
        # Create view
        return ft.View(
            route="/dashboard",
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
        )
    
    async def did_mount(self):
        # Load documents
        await self.document_list.load_documents()
        
        # Load conversations
        await self.load_conversations()
    
    async def load_conversations(self):
        # Clear existing items
        self.conversations_list.controls.clear()
        
        # Loading indicator
        self.conversations_list.controls.append(
            ft.Text("Loading conversations...")
        )
        self.page.update()
        
        try:
            # Get conversations
            conversations = await self.api_client.get_conversations()
            
            # Clear loading indicator
            self.conversations_list.controls.clear()
            
            if not conversations:
                self.conversations_list.controls.append(
                    ft.Text("No conversations yet. Start a new one!")
                )
            else:
                # Add conversations to list
                for conversation in conversations:
                    title = conversation.get("title", "Untitled Conversation")
                    created_at = conversation.get("created_at", "")
                    conversation_id = conversation.get("id")
                    
                    # Format date
                    if created_at:
                        from datetime import datetime
                        date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_at = date_obj.strftime("%Y-%m-%d %H:%M")
                    
                    self.conversations_list.controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(ft.icons.CHAT, color=ft.colors.GREEN_400),
                                            ft.Text(title, weight=ft.FontWeight.BOLD),
                                            ft.Spacer(),
                                            ft.Text(created_at, size=12, color=ft.colors.GREY_500),
                                        ]
                                    ),
                                ]
                            ),
                            padding=10,
                            border_radius=5,
                            bgcolor=ft.colors.WHITE,
                            ink=True,
                            on_click=lambda e, id=conversation_id: self.page.go(f"/chat/{id}"),
                        )
                    )
        except Exception as ex:
            self.conversations_list.controls.clear()
            self.conversations_list.controls.append(
                ft.Text(f"Error loading conversations: {str(ex)}")
            )
        
        # Update the page
        self.page.update()