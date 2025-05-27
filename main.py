from nicegui import ui
from nicegui import app

@ui.page('/')
def main_page():
    ui.label('Welcome to the NiceGUI App!')
    ui.button('Click Me', on_click=lambda: ui.notify('Button clicked!'))

ui.run()