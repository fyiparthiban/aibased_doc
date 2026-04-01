import reflex as rx

from ..components.navbar import navbar
from ..components.hero import hero
from ..components.footer import footer


def home():
    """Home page with hero section"""
    return rx.box(
        navbar(),
        hero(),
        footer(),
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        min_height="100vh",
        width="100%"
    )