import flet as ft
from frontend.services.api_client import ApiClient


class RegisterPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = page.client_storage.get("api_url")
        self.api_client = ApiClient(self.api_url)
        
    def build(self) -> ft.View:
        # Form fields
        self.full_name_field = ft.TextField(
            label="Full Name",
            hint_text="Enter your full name",
            autofocus=True,
            width=320,
            border_color=ft.colors.BLUE_400,
        )
        
        self.email_field = ft.TextField(
            label="Email",
            hint_text="Enter your email",
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
        
        self.confirm_password_field = ft.TextField(
            label="Confirm Password",
            hint_text="Confirm your password",
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
        
        # Register button
        self.register_button = ft.ElevatedButton(
            text="Register",
            width=320,
            bgcolor=ft.colors.BLUE_400,
            color=ft.colors.WHITE,
            on_click=self.register,
        )
        
        # Login link
        self.login_link = ft.TextButton(
            text="Already have an account? Login",
            on_click=lambda _: self.page.go("/login"),
        )
        
        # Create main layout
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Omega RAG", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text("Create a new account", size=16, color=ft.colors.GREY_700),
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    self.full_name_field,
                    self.email_field,
                    self.password_field,
                    self.confirm_password_field,
                    self.error_text,
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    self.register_button,
                    self.login_link,
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
            route="/register",
            controls=[
                ft.Container(
                    content=main_content,
                    alignment=ft.alignment.center,
                    expand=True,
                )
            ]
        )
    
    async def register(self, e):
        # Reset error
        self.error_text.visible = False
        self.page.update()
        
        # Validate inputs
        full_name = self.full_name_field.value
        email = self.email_field.value
        password = self.password_field.value
        confirm_password = self.confirm_password_field.value
        
        if not full_name or not email or not password or not confirm_password:
            self.error_text.value = "Please fill in all fields"
            self.error_text.visible = True
            self.page.update()
            return
        
        if password != confirm_password:
            self.error_text.value = "Passwords do not match"
            self.error_text.visible = True
            self.page.update()
            return
        
        # Disable button during registration
        self.register_button.disabled = True
        self.register_button.text = "Registering..."
        self.page.update()
        
        try:
            # Call register API
            result = await self.api_client.register(email, password, full_name)
            
            if "error" in result:
                self.error_text.value = result.get("error", "Registration failed")
                self.error_text.visible = True
            else:
                # Registration successful, login automatically
                login_result = await self.api_client.login(email, password)
                
                if "error" not in login_result:
                    # Save token
                    token = login_result.get("access_token")
                    self.page.client_storage.set("auth_token", token)
                    
                    # Get user profile
                    self.api_client.token = token
                    user_profile = await self.api_client.get_user_profile()
                    
                    if "error" not in user_profile:
                        self.page.session.set("current_user", user_profile)
                    
                    # Navigate to dashboard
                    self.page.go("/dashboard")
                else:
                    # Registration worked but login failed, redirect to login
                    self.page.go("/login")
        except Exception as ex:
            self.error_text.value = f"Registration failed: {str(ex)}"
            self.error_text.visible = True
        
        # Re-enable button
        self.register_button.disabled = False
        self.register_button.text = "Register"
        self.page.update()