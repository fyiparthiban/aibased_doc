import reflex as rx


def navbar():
    """Navigation bar component"""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon("brain", size=25),
                rx.text("RAG Chatbot", font_size="lg", font_weight="bold"),
                spacing="2"
            ),
            rx.spacer(),
            rx.hstack(
                rx.link("Home", href="/", _hover={"text_decoration": "underline"}),
                rx.link("Upload", href="/upload", _hover={"text_decoration": "underline"}),
                rx.link("Chat", href="/chat", _hover={"text_decoration": "underline"}),
                rx.link("History", href="/history", _hover={"text_decoration": "underline"}),
                spacing="5"
            ),
            width="100%",
            padding="1.5em",
            align_items="center"
        ),
        border_bottom="1px solid",
        border_color="gray.700",
        background_color="#1a1a1a",
        position="sticky",
        top="0",
        z_index="100",
        width="100%"
    )
    