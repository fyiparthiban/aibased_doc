import reflex as rx

from .pages.home import home
from .pages.upload import upload
from .pages.chat import chat
from .pages.history import history


# Configure the app
app = rx.App()
app.add_page(home, route="/")
app.add_page(upload, route="/upload")
app.add_page(chat, route="/chat")
app.add_page(history, route="/history")
