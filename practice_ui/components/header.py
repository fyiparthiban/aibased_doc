import reflex as rx
import requests
import random

from .navbar import navbar

class MyState(rx.State):
    quote = ""
    author = ""

    def get_quote(self):
        url = "https://type.fit/api/quotes"
        res = requests.get(url)
        data = res.json()

        rand_num = random.randrange(0, len(data))

        self.quote = data[rand_num]['text']
        self.author = data[rand_num]['author']

def header():
    return rx.grid(
        rx.center(
            rx.box(
                rx.heading("I am Parthiban!"),
                rx.heading("This project is about..."),
                
                rx.button(
                    "Click here!",
                    on_click=MyState.get_quote
                ),

                rx.text(MyState.quote),
                rx.text(MyState.author)
            )
        ),
        rx.center(
            rx.image(src="Chat bot-rafiki.png")
        ),
        columns={
            "base": "1",
            "md": "2",
            "lg": "3"
        }
    )
    