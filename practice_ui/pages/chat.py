import reflex as rx

from ..components.chat import chat_interface
from ..components.navbar import navbar
from ..components.footer import footer
from ..states.rag_state import ChatState


def chat():
    """Chat page"""
    return rx.box(
        navbar(),
        rx.container(
            chat_interface(),
            max_width="900px"
        ),
        footer(),
        background_color="#121212",
        color="white",
        min_height="100vh",
        on_mount=ChatState.load_history
    )