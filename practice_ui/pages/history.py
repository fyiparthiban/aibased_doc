import reflex as rx

from ..components.navbar import navbar
from ..components.footer import footer
from ..states.rag_state import ChatState


def history():
    """History page showing all chat conversations"""
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Chat History", size="2"),
                rx.divider(),

                rx.cond(
                    ChatState.history_count > 0,
                    rx.vstack(
                        rx.text(f"Total conversations: {ChatState.history_count}", color="gray.400"),
                        rx.foreach(
                            ChatState.history,
                            lambda item: rx.box(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon("user", color="blue.400"),
                                        rx.text("Question:", font_weight="bold", color="blue.400"),
                                        spacing="2"
                                    ),
                                    rx.text(item["question"], padding="2", background_color="blue.900", border_radius="md"),
                                    rx.hstack(
                                        rx.icon("bot", color="green.400"),
                                        rx.text("Answer:", font_weight="bold", color="green.400"),
                                        spacing="2",
                                        margin_top="2"
                                    ),
                                    rx.text(item["answer"], padding="2", background_color="gray.800", border_radius="md"),
                                    rx.cond(
                                        item["sources"],
                                        rx.vstack(
                                            rx.text("Sources available", font_weight="bold", color="yellow.400", font_size="sm"),
                                            rx.text("Source details available in chat view", font_size="sm", color="gray.400"),
                                            spacing="1",
                                            margin_top="2"
                                        )
                                    ),
                                    spacing="2",
                                    padding="4",
                                    border="1px solid",
                                    border_color="gray.600",
                                    border_radius="lg",
                                    width="100%"
                                ),
                                margin_bottom="4",
                                width="100%"
                            )
                        ),
                        rx.button(
                            "Clear All History",
                            on_click=ChatState.reset_session,
                            background_color="red.600",
                            _hover={"background_color": "red.700"},
                            margin_top="2"
                        ),
                        spacing="4",
                        width="100%"
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("history", size=64, color="gray.600"),
                            rx.text("No chat history yet", color="gray.400", font_size="lg"),
                            rx.text("Start a conversation to see your history here", color="gray.500"),
                            spacing="4"
                        ),
                        height="400px"
                    )
                ),

                spacing="4",
                padding="2em"
            ),
            max_width="1000px"
        ),
        footer(),
        background_color="#121212",
        color="white",
        min_height="100vh",
        on_mount=ChatState.load_history
    )