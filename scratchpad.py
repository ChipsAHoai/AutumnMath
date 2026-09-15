from nicegui.element import Element


class Scratchpad(Element, component='scratchpad.js'):
    """A browser-local drawing surface for working through quiz questions."""

    def __init__(self):
        super().__init__()
