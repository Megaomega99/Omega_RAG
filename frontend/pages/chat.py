import flet as ft
from frontend.services.api_client import ApiClient
from frontend.components.navigation import Navigation
from frontend.components.chat_interface import ChatInterface


class ChatPage:
    def __init__(self, page: ft.Page, conversation_id: int = None):
        self.page = page
        self.conversation_id = conversation_id
        self.api_url = page.client_storage.get("api_url")
        self.api_token = page.client_storage.get("auth_token")
        self.api_client = ApiClient(self.api_url, self.api_token)
        
    def build(self) -> ft.View:
        # Create navigation bar
        self.navigation = Navigation(self.page, "chat")
        
        # Create chat interface
        self.chat_interface = ChatInterface(
            self.page,
            self.api_client,
            self.conversation_id
        )
        
        # Header section
        self.page_title = ft.Text(
            "Chat with your Documents",
            size=24,
            weight=ft.FontWeight.BOLD,
        )
        
        # Create main layout
        main_content = ft.Container(
            content=ft.Column(
                [
                    self.page_title,
                    ft.Divider(),
                    self.chat_interface,
                ],
                spacing=15,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
        
        # Create view
        view = ft.View(
            route=f"/chat/{self.conversation_id}" if self.conversation_id else "/chat/new",
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
        # Load documents for selector
        await self.chat_interface.load_documents()
        
        # Load conversation history if available
        if self.conversation_id:
            await self.chat_interface.load_conversation()