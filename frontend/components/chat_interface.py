import flet as ft
from frontend.services.api_client import ApiClient
from typing import List, Optional, Dict, Any


class ChatMessage(ft.Container):
    def __init__(
        self, 
        text: str, 
        is_user: bool = False, 
        sources: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__()
        self.text = text
        self.is_user = is_user
        self.sources = sources or []
        self.build()
    
    def build(self):
        # Create message content
        message_text = ft.SelectableText(
            self.text,
            color=ft.colors.BLACK if self.is_user else ft.colors.WHITE,
            selectable=True,
        )
        
        # Sources section
        sources_section = None
        if self.sources and not self.is_user:
            sources_list = ft.Column(spacing=5)
            
            # Add sources
            for i, source in enumerate(self.sources):
                document_title = source.get("document_title", "Document")
                document_id = source.get("document_id")
                similarity = source.get("similarity", 0)
                
                # Format similarity as percentage
                similarity_text = f"{similarity:.0%}" if similarity else "N/A"
                
                sources_list.controls.append(
                    ft.Row(
                        [
                            ft.Icon(ft.icons.DESCRIPTION, size=16, color=ft.colors.BLUE_300),
                            ft.Text(
                                f"{document_title}",
                                size=12,
                                color=ft.colors.BLUE_300,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Spacer(),
                            ft.Text(
                                f"Match: {similarity_text}",
                                size=12,
                                color=ft.colors.BLUE_300,
                            ),
                        ],
                        tight=True,
                    )
                )
            
            # Create sources section
            sources_section = ft.Container(
                content=ft.Column(
                    [
                        ft.Divider(color=ft.colors.BLUE_200, height=20),
                        ft.Text(
                            "Sources:",
                            size=12,
                            color=ft.colors.BLUE_300,
                            weight=ft.FontWeight.BOLD,
                        ),
                        sources_list,
                    ],
                    spacing=5,
                ),
                animate=ft.animation.Animation(duration=300, curve=ft.AnimationCurve.EASE_OUT),
            )
        
        # Build content
        content = ft.Column(
            [message_text] + ([sources_section] if sources_section else []),
            spacing=10,
        )
        
        # Set container properties
        self.content = content
        self.bgcolor = ft.colors.BLUE_100 if self.is_user else ft.colors.BLUE_ACCENT
        self.border_radius = ft.border_radius.only(
            top_left=15 if not self.is_user else 15,
            top_right=15 if self.is_user else 15,
            bottom_left=15 if self.is_user else 0,
            bottom_right=15 if not self.is_user else 0,
        )
        self.width = 500
        self.padding = 15
        self.margin = ft.margin.only(
            left=50 if self.is_user else 10,
            right=10 if self.is_user else 50,
            top=5,
            bottom=5,
        )
        self.alignment = ft.alignment.center_right if self.is_user else ft.alignment.center_left


class ChatInterface(ft.Column):
    def __init__(self, page: ft.Page, api_client: ApiClient, conversation_id: Optional[int] = None):
        super().__init__(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.page = page
        self.api_client = api_client
        self.conversation_id = conversation_id
        
        # Create chat components
        self.chat_area = ft.ListView(
            spacing=10,
            auto_scroll=True,
            expand=True,
        )
        
        self.document_selector = ft.Dropdown(
            label="Select documents for context",
            width=300,
            helper_text="Optional: Select documents to use as context",
        )
        
        self.query_field = ft.TextField(
            hint_text="Type your question here...",
            border_color=ft.colors.BLUE_400,
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=5,
            on_submit=self.send_message,
        )
        
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND,
            icon_color=ft.colors.BLUE_400,
            icon_size=30,
            tooltip="Send message",
            on_click=self.send_message,
        )
        
        # Add components to the layout
        self.controls.extend([
            ft.Container(
                content=self.chat_area,
                expand=True,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=10,
                padding=10,
            ),
            ft.Row(
                [
                    self.document_selector,
                    ft.Spacer(),
                ],
            ),
            ft.Row(
                [
                    self.query_field,
                    self.send_button,
                ],
                spacing=10,
            ),
        ])
    
    async def load_documents(self):
        """Load documents for the document selector."""
        try:
            documents = await self.api_client.get_documents()
            
            if documents:
                # Only include processed documents
                processed_docs = [
                    doc for doc in documents 
                    if doc.get("is_processed") and doc.get("is_indexed")
                ]
                
                # Add to dropdown
                self.document_selector.options = [
                    ft.dropdown.Option(
                        key=str(doc.get("id")),
                        text=doc.get("title", "Untitled")
                    )
                    for doc in processed_docs
                ]
                
                # Enable multi-select
                self.document_selector.multiple = True
                
                # Update
                self.page.update()
        except Exception as ex:
            print(f"Error loading documents: {str(ex)}")
    
    async def load_conversation(self):
        """Load conversation history."""
        if not self.conversation_id:
            return
            
        try:
            conversation = await self.api_client.get_conversation(self.conversation_id)
            
            if "error" in conversation:
                return
                
            # Get messages
            messages = conversation.get("messages", [])
            
            # Clear existing messages
            self.chat_area.controls.clear()
            
            # Add messages to chat
            for message in messages:
                content = message.get("content", "")
                role = message.get("role", "")
                sources = message.get("context_documents", [])
                
                is_user = role == "user"
                
                self.chat_area.controls.append(
                    ChatMessage(content, is_user, sources)
                )
                
            # Update
            self.page.update()
        except Exception as ex:
            print(f"Error loading conversation: {str(ex)}")
    
    async def send_message(self, e):
        """Send a message to the API."""
        # Get query text
        query = self.query_field.value
        
        if not query:
            return
            
        # Clear query field
        self.query_field.value = ""
        self.page.update()
        
        # Add user message to chat
        self.chat_area.controls.append(
            ChatMessage(query, is_user=True)
        )
        
        # Add temporary assistant message
        temp_message = ChatMessage("Thinking...", is_user=False)
        self.chat_area.controls.append(temp_message)
        self.page.update()
        
        try:
            # Get selected documents
            document_ids = None
            if self.document_selector.value:
                if isinstance(self.document_selector.value, list):
                    document_ids = [int(doc_id) for doc_id in self.document_selector.value]
                else:
                    document_ids = [int(self.document_selector.value)]
            
            # Send query to API
            response = await self.api_client.query_rag(
                query=query,
                conversation_id=self.conversation_id,
                document_ids=document_ids
            )
            
            if "error" in response:
                # Replace temporary message with error
                error_message = f"Error: {response.get('error', 'Unknown error')}"
                self.chat_area.controls.remove(temp_message)
                self.chat_area.controls.append(
                    ChatMessage(error_message, is_user=False)
                )
            else:
                # Get conversation ID if this is a new conversation
                if not self.conversation_id:
                    self.conversation_id = response.get("conversation_id")
                    self.page.session.set("current_conversation", self.conversation_id)
                    
                    # Update URL
                    self.page.route = f"/chat/{self.conversation_id}"
                    self.page.update()
                
                # Get full conversation to get the actual response (may be updated by async task)
                await self.load_conversation()
        except Exception as ex:
            # Replace temporary message with error
            self.chat_area.controls.remove(temp_message)
            self.chat_area.controls.append(
                ChatMessage(f"Error: {str(ex)}", is_user=False)
            )
            
        # Update
        self.page.update()