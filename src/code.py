# main.py

import time
from mode_manager import ModeManager
from button_handler import ButtonHandler
from slider_handler import SliderHandler
from display import draw_HI

def main():
    # Initialize components
    mode_manager = ModeManager()
    button_handler = ButtonHandler(mode_manager)
    slider_handler = SliderHandler(mode_manager, button_handler)
    draw_HI()  # Display splash screen

    while True:
        current_time = time.monotonic()
        any_pad_active, redraw_display = button_handler.update_buttons(current_time)
        slider_handler.handle_slider_changes(any_pad_active)
        if redraw_display:
            mode_manager.refresh_display()

if __name__ == "__main__":
    main()