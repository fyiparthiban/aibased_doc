import reflex as rx
from typing import Any, Dict

from ..states.rag_state import ChatState

def render_source(source: Any):
    if hasattr(source, "get") and not isinstance(source, str):
        return rx.text(
            "• ",
            source["source"],
            " (Page ",
            source["page"],
            "): ",
            source["snippet"],
            font_size="sm",
            color="gray.400"
        )
    return rx.text(
        "• ",
        source,
        font_size="sm",
        color="gray.400"
    )


def chat_interface():
    """Chat interface component"""
    return rx.vstack(
        rx.heading("Chat with Your Documents", size="2"),
        rx.divider(),

        # Chat history
        rx.box(
            rx.cond(
                ChatState.history_count > 0,
                rx.vstack(
                    rx.foreach(
                        ChatState.history,
                        lambda item: rx.box(
                            rx.vstack(
                                # Question
                                rx.box(
                                    rx.text("You:", font_weight="bold", color="blue.400"),
                                    rx.text(item["question"], padding="2"),
                                    align_self="flex-end",
                                    background_color="blue.900",
                                    border_radius="lg",
                                    padding="3",
                                    margin_bottom="2",
                                    max_width="70%"
                                ),
                                # Answer
                                rx.box(
                                    rx.text("AI:", font_weight="bold", color="green.400"),
                                    rx.text(item["answer"], padding="2"),
                                    align_self="flex-start",
                                    background_color="gray.800",
                                    border_radius="lg",
                                    padding="3",
                                    margin_bottom="2",
                                    max_width="70%"
                                ),
                                # Sources (if available)
                                rx.cond(
                                    item["sources"],
                                    rx.box(
                                        rx.text("Sources:", font_weight="bold", color="yellow.400", font_size="sm"),
                                        rx.foreach(
                                            item["sources"],
                                            lambda source: rx.box(
                                                render_source(source),
                                                padding="1",
                                                border_left="2px solid",
                                                border_color="yellow.600",
                                                margin_left="1em",
                                                margin_bottom="1"
                                            )
                                        ),
                                        margin_top="1",
                                        padding="2",
                                        background_color="gray.900",
                                        border_radius="md"
                                    )
                                ),
                                spacing="1",
                                width="100%"
                            ),
                            margin_bottom="3",
                            width="100%"
                        )
                    ),
                    width="100%",
                    spacing="2",
                    max_height="500px",
                    overflow_y="auto"
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("message-circle", size=48, color="gray.600"),
                        rx.text("No messages yet", color="gray.400"),
                        rx.text(
                            "Upload documents and start asking questions!",
                            color="gray.500",
                            font_size="sm"
                        ),
                        rx.button(
                            "Upload Documents",
                            on_click=rx.redirect("/upload"),
                            background_color="blue.600",
                            _hover={"background_color": "blue.700"},
                            margin_top="1em"
                        ),
                        spacing="3"
                    ),
                    height="300px"
                )
            ),
            border="1px solid",
            border_color="gray.700",
            border_radius="md",
            padding="4",
            width="100%",
            height="500px",
            overflow_y="auto",
            background_color="#2a2a2a"
        ),

        # Input area
        rx.hstack(
            rx.input(
                value=ChatState.question,
                on_change=ChatState.set_question,
                placeholder="Ask a question about your documents...",
                width="100%",
                is_disabled=ChatState.is_loading,
                background_color="#3a3a3a",
                border_color="gray.600",
                _focus={"border_color": "blue.500"}
            ),
            rx.button(
                "Send",
                on_click=ChatState.ask,
                is_loading=ChatState.is_loading,
                is_disabled=ChatState.is_loading | ~ChatState.has_documents,
                background_color="blue.600",
                _hover={"background_color": "blue.700"}
            ),
            rx.button(
                "Clear",
                on_click=ChatState.reset_session,
                background_color="gray.600",
                _hover={"background_color": "gray.700"}
            ),
            width="100%",
            spacing="2"
        ),

        # Status info
        rx.cond(
            ~ChatState.has_documents,
            rx.box(
                rx.text(
                    "⚠️ Please upload documents first to start chatting",
                    color="yellow.400",
                    font_size="sm",
                    text_align="center"
                ),
                padding="2",
                background_color="yellow.900",
                border_radius="md",
                width="100%"
            )
        ),

        width="100%",
        max_width="900px",
        spacing="4",
        padding="2em"
    )