import reflex as rx


def hero():
    """Hero section component"""
    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.heading(
                    "RAG-Powered AI Chatbot",
                    size="1",
                    color="white",
                    text_align="center",
                    margin_bottom="1em"
                ),
                rx.text(
                    "Upload your documents and chat with an AI that has deep knowledge of your content. "
                    "Powered by Retrieval-Augmented Generation (RAG) for accurate, source-based answers.",
                    font_size="lg",
                    color="gray.300",
                    text_align="center",
                    max_width="700px",
                    line_height="1.6"
                ),
                rx.hstack(
                    rx.button(
                        "Get Started",
                        size="2",
                        background_color="blue.600",
                        _hover={"background_color": "blue.700"},
                        padding="1.5em 3em",
                        on_click=rx.redirect("/upload")
                    ),
                    rx.button(
                        "Learn More",
                        size="2",
                        variant="outline",
                        border_color="blue.600",
                        color="blue.400",
                        _hover={"background_color": "blue.600", "color": "white"},
                        padding="1.5em 3em",
                        on_click=rx.redirect("/chat")
                    ),
                    spacing="4",
                    justify="center",
                    margin_top="2em"
                ),
                spacing="4",
                align_items="center",
                width="100%"
            ),
            rx.spacer(),
            rx.vstack(
                rx.icon("bot", size=120, color="cyan.400"),
                rx.text(
                    "AI-Powered Document Intelligence",
                    color="cyan.300",
                    font_size="sm",
                    text_align="center"
                ),
                spacing="2"
            ),
            width="100%",
            height="70vh",
            justify_content="center",
            align_items="center"
        ),
        width="100%"
    )