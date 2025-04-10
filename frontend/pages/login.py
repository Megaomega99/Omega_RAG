import flet as ft
from frontend.services.api_client import ApiClient


class LoginPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = page.client_storage.get("api_url")
        self.api_client = ApiClient(self.api_url)
        
    def build(self) -> ft.View:
        # Form fields
        self.email_field = ft.TextField(
            label="Email",
            hint_text="Enter your email",
            autofocus=True,
            width=320,
            border_color=ft.colors.BLUE_400,
        )
        
        self.password_field = ft.TextField(
            label="Password",
            hint_text="Enter your password",
            password=True,
            can_reveal_password=True,
            width=320,
            border_color=ft.colors.BLUE_400,
        )
        
        self.error_text = ft.Text(
            color=ft.colors.RED_500,
            size=14,
            visible=False,
        )
        
        # Login button
        self.login_button = ft.ElevatedButton(
            text="Login",
            width=320,
            bgcolor=ft.colors.BLUE_400,
            color=ft.colors.WHITE,
            on_click=self.login,
        )
        
        # Register link
        self.register_link = ft.TextButton(
            text="Don't have an account? Register",
            on_click=lambda _: self.page.go("/register"),
        )
        
        # Create main layout
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Omega RAG", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text("Login to your account", size=16, color=ft.colors.GREY_700),
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    self.email_field,
                    self.password_field,
                    self.error_text,
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    self.login_button,
                    self.register_link,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            padding=ft.padding.symmetric(vertical=50, horizontal=20),
            alignment=ft.alignment.center,
            width=400,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.colors.BLACK12,
                offset=ft.Offset(0, 0),
            )
        )
        
        return ft.View(
            route="/login",
            controls=[
                ft.Container(
                    content=main_content,
                    alignment=ft.alignment.center,
                    expand=True,
                )
            ]
        )
    
    async def login(self, e):
        # Reset error
        self.error_text.visible = False
        self.page.update()
        
        # Validate inputs
        email = self.email_field.value
        password = self.password_field.value
        
        if not email or not password:
            self.error_text.value = "Please enter both email and password"
            self.error_text.visible = True
            self.page.update()
            return
        
        # Disable button during login
        self.login_button.disabled = True
        self.login_button.text = "Logging in..."
        self.page.update()
        
        try:
            # Call login API
            result = await self.api_client.login(email, password)
            
            if "error" in result:
                self.error_text.value = "Invalid email or password"
                self.error_text.visible = True
            else:
                # Save token
                token = result.get("access_token")
                self.page.client_storage.set("auth_token", token)
                
                # Get user profile
                self.api_client.token = token
                user_profile = await self.api_client.get_user_profile()
                
                if "error" not in user_profile:
                    self.page.session.set("current_user", user_profile)
                
                # Navigate to dashboard
                self.page.go("/dashboard")
        except Exception as ex:
            self.error_text.value = f"Login failed: {str(ex)}"
            self.error_text.visible = True
        
        # Re-enable button
        self.login_button.disabled = False
        self.login_button.text = "Login"
        self.page.update()