import reflex as rx

from ..components.navbar import navbar
from ..components.footer import footer
from ..states.rag_state import ChatState


def upload():
    """Upload page for document management"""
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Upload Documents", size="2"),
                rx.divider(),

                rx.text(
                    "Upload PDF or text documents to build your knowledge base. "
                    "The AI will use these documents to provide accurate answers to your questions.",
                    color="gray.300",
                    text_align="center",
                    max_width="600px"
                ),

                rx.upload(
                    rx.vstack(
                        rx.icon("upload", size=48, color="blue.500"),
                        rx.text("Drag and drop files here or click to select"),
                        rx.text("Supported formats: PDF, TXT, DOCX, MD", color="gray.500", font_size="sm"),
                        rx.text("Maximum 10 files, 10MB each", color="gray.500", font_size="sm"),
                        align_items="center",
                        spacing="2"
                    ),
                    multiple=True,
                    accept={
                        "application/pdf": [".pdf"],
                        "text/plain": [".txt"],
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                        "text/markdown": [".md"]
                    },
                    max_files=10,
                    border="2px dashed",
                    border_color="blue.600",
                    padding="3em",
                    border_radius="lg",
                    background_color="#2a2a2a",
                    _hover={"background_color": "#3a3a3a"},
                    on_drop=ChatState.handle_upload
                ),

                rx.button(
                    "Upload Selected Files",
                    on_click=ChatState.upload_pending_files,
                    background_color="blue.600",
                    _hover={"background_color": "blue.700"},
                    color="white",
                    width="220px",
                    align_self="center",
                    margin_top="1em"
                ),

                rx.cond(
                    ChatState.upload_progress != "",
                    rx.box(
                        rx.text(
                            ChatState.upload_progress,
                            color=rx.cond(ChatState.upload_successful, "green.400", "yellow.400"),
                            font_weight="bold",
                            text_align="center"
                        ),
                        padding="1em",
                        background_color=rx.cond(ChatState.upload_successful, "green.900", "yellow.900"),
                        border_radius="md",
                        margin_top="1em",
                        width="100%"
                    )
                ),

                rx.cond(
                    ChatState.has_documents,
                    rx.box(
                        rx.vstack(
                            rx.text("Documents uploaded successfully!", color="green.400", font_weight="bold"),
                            rx.button(
                                "Start Chatting",
                                on_click=rx.redirect("/chat"),
                                background_color="blue.600",
                                _hover={"background_color": "blue.700"},
                                margin_top="1em"
                            ),
                            spacing="2",
                            align_items="center"
                        ),
                        padding="1em",
                        background_color="green.900",
                        border_radius="md",
                        margin_top="1em",
                        width="100%"
                    )
                )
            ),
            spacing="4",
            padding="2em",
            max_width="900px"
        ),
        footer(),
        background_color="#121212",
        color="white",
        min_height="100vh"
    )