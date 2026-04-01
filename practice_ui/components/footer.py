import reflex as rx


def footer():
    """Footer component"""
    return rx.box(
        rx.vstack(
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.heading("About", size="4", margin="0"),
                    rx.link(rx.text("AI Document Search"), href="/about"),
                    rx.link(rx.text("How it Works"), href="/about"),
                    spacing="2"
                ),
                rx.vstack(
                    rx.heading("Features", size="4", margin="0"),
                    rx.link(rx.text("Document Upload"), href="/documents"),
                    rx.link(rx.text("AI Chat"), href="/chat"),
                    spacing="2"
                ),
                rx.vstack(
                    rx.heading("Contact", size="4", margin="0"),
                    rx.text("support@aidocsearch.com"),
                    rx.text("© 2026 AI Document Search"),
                    spacing="2"
                ),
                width="100%",
                justify="between",
                spacing="6"
            ),
            rx.divider(),
            rx.hstack(
                rx.text("Built with Reflex", font_size="sm"),
                rx.spacer(),
                rx.text(
                    "© 2026 AI Document Search. All rights reserved.",
                    font_size="sm"
                ),
                width="100%"
            ),
            spacing="4",
            padding="2em",
            width="100%"
        ),
        background_color="#1a1a1a",
        border_top="1px solid",
        border_color="gray.700",
        width="100%",
        margin_top="4em"
    )
    