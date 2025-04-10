import flet as ft


class Navigation(ft.Container):
    def __init__(self, page: ft.Page, active_tab: str = "dashboard"):
        super().__init__()
        self.page = page
        self.active_tab = active_tab
        self.build()
    
    def build(self):
        # Logo section
        logo = ft.Row(
            [
                ft.Icon(ft.icons.AUTO_AWESOME, color=ft.colors.BLUE_500, size=30),
                ft.Text("Omega RAG", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_500),
            ],
            spacing=10,
        )
        
        # Navigation items
        self.dashboard_tab = self.create_nav_item(
            "Dashboard", 
            ft.icons.DASHBOARD,
            "/dashboard",
            is_active=self.active_tab == "dashboard"
        )
        
        self.documents_tab = self.create_nav_item(
            "Documents", 
            ft.icons.FOLDER,
            "/documents",
            is_active=self.active_tab == "documents"
        )
        
        self.chat_tab = self.create_nav_item(
            "Chat", 
            ft.icons.CHAT,
            "/chat/new",
            is_active=self.active_tab == "chat"
        )
        
        # Create navigation row
        navigation = ft.Row(
            [
                logo,
                ft.Spacer(),
                ft.Row(
                    [
                        self.dashboard_tab,
                        self.documents_tab,
                        self.chat_tab,
                    ],
                    spacing=5,
                ),
                ft.Spacer(),
                self.create_user_menu(),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # Set container properties
        self.content = navigation
        self.padding = ft.padding.only(left=20, right=20, top=10, bottom=10)
        self.bgcolor = ft.colors.WHITE
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color=ft.colors.BLACK12,
            offset=ft.Offset(0, 2),
        )
    
    def create_nav_item(self, text: str, icon_name: str, route: str, is_active: bool = False):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        icon_name,
                        color=ft.colors.WHITE if is_active else ft.colors.BLACK,
                        size=20,
                    ),
                    ft.Text(
                        text,
                        color=ft.colors.WHITE if is_active else ft.colors.BLACK,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    ),
                ],
                spacing=5,
            ),
            padding=ft.padding.all(10),
            bgcolor=ft.colors.BLUE_500 if is_active else ft.colors.TRANSPARENT,
            border_radius=30,
            ink=True,
            on_click=lambda e, r=route: self.page.go(r),
        )
    
    def create_user_menu(self):
        # Get user info from session
        current_user = self.page.session.get("current_user", {})
        user_name = current_user.get("full_name", "User") if current_user else "User"
        
        # Create user menu
        return ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(
                    text="Profile",
                    icon=ft.icons.PERSON,
                ),
                ft.PopupMenuItem(
                    text="Settings",
                    icon=ft.icons.SETTINGS,
                ),
                ft.PopupMenuItem(
                    text="Logout",
                    icon=ft.icons.LOGOUT,
                    on_click=self.logout,
                ),
            ],
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.CircleAvatar(
                            content=ft.Text(
                                user_name[0].upper(),
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=ft.colors.BLUE_500,
                            radius=15,
                        ),
                        ft.Text(user_name),
                        ft.Icon(ft.icons.ARROW_DROP_DOWN),
                    ],
                    spacing=5,
                ),
                padding=ft.padding.all(8),
                border_radius=30,
                bgcolor=ft.colors.BLUE_50,
            ),
        )
    
    def logout(self, e):
        # Clear auth token
        self.page.client_storage.set("auth_token", None)
        
        # Clear session
        self.page.session.set("current_user", None)
        
        # Navigate to login
        self.page.go("/login")