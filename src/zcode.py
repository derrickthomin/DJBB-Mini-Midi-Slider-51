import board
import digitalio
import time

from adafruit_debouncer import Button

from midi import (
    send_midi_note_on, send_midi_note_off, clear_all_notes,
    change_midi_bank, send_control_change
)
import sliders

from display import (
    display_midi_bank_down, display_midi_bank_up,
    BANK_DOWN_IDX, BANK_UP_IDX, draw_C, draw_N,
    set_pixel_color_cc, set_pixel_color_note, clear_pixel,
    update_cc_pixels, draw_HI, blink_next_color, blink_prev_color,
    draw_lock_icon, draw_unlock_icon
)
from settings import debug_print, load_cc_vals_from_file

# Constants
DOUBLE_PRESS_INTERVAL = 0.3  # seconds

# Button Pins Setup
FN_BTN_PIN = board.GP1

DRUMPAD_BTN_PINS = [
    board.GP17, board.GP16, board.GP15, board.GP14,
    board.GP19, board.GP18, board.GP12, board.GP13,
    board.GP21, board.GP9, board.GP6, board.GP7,
    board.GP4, board.GP0, board.GP2, board.GP5
]

# Load CC values from file
all_cc_vals = load_cc_vals_from_file()
slide_cc_vals = all_cc_vals[0]        # Global CC numbers for sliders
slide_cc_vals_held = all_cc_vals[1]   # CC numbers per button per slider when buttons are held or latched

class ModeManager:
    """
    Manages the MIDI controller's modes and latch states.
    """
    def __init__(self):
        self.is_cc_mode = False  # True if in CC mode, False if in Note mode
        self.cc_latch_active = True
        self.note_latch_active = False

        self.cc_button_latched = [False] * 16
        self.note_button_latched = [False] * 16
        self.button_held_states = [False] * 16

    def toggle_mode_cc_note(self):
        """
        Toggle between CC mode and Note mode.
        """
        self.is_cc_mode = not self.is_cc_mode

        if self.is_cc_mode:
            # Entering CC mode
            draw_C()
            # Update LEDs for CC mode
            for idx in range(16):
                if self.note_button_latched[idx]:
                    # Leave the note on, but turn off the LED (since we're in CC mode)
                    clear_pixel(idx)
                if self.cc_button_latched[idx]:
                    set_pixel_color_cc(idx)
                else:
                    clear_pixel(idx)
        else:
            # Entering Note mode
            draw_N()
            # Update LEDs for Note mode
            for idx in range(16):
                if self.cc_button_latched[idx]:
                    # Turn off the CC LED
                    clear_pixel(idx)
                if self.note_button_latched[idx]:
                    # Light up the LED for the latched note
                    set_pixel_color_note(idx)
                else:
                    clear_pixel(idx)

    def toggle_latch_mode(self):
        """
        Toggle the latch mode for the current active mode.
        """
        if self.is_cc_mode:
            self.cc_latch_active = not self.cc_latch_active
            if self.cc_latch_active:
                print("CC Latch Mode Enabled")
                draw_lock_icon()
            else:
                print("CC Latch Mode Disabled")
                draw_unlock_icon()
        else:
            self.note_latch_active = not self.note_latch_active
            if self.note_latch_active:
                print("Note Latch Mode Enabled")
                draw_lock_icon()
            else:
                print("Note Latch Mode Disabled")
                draw_unlock_icon()


class ButtonHandler:
    """
    Handles the drumpad buttons and the FN button.
    """
    def __init__(self, mode_manager):
        self.mode_manager = mode_manager

        # Initialize FN button
        fn_input = digitalio.DigitalInOut(FN_BTN_PIN)
        fn_input.direction = digitalio.Direction.INPUT
        fn_input.pull = digitalio.Pull.UP
        self.fn_button = Button(fn_input)

        # Initialize drumpad buttons
        self.drumpad_buttons = []
        for pin in DRUMPAD_BTN_PINS:
            button_input = digitalio.DigitalInOut(pin)
            button_input.direction = digitalio.Direction.INPUT
            button_input.pull = digitalio.Pull.UP
            self.drumpad_buttons.append(Button(button_input))

        # Timing variables for FN button
        self.last_fn_release_time = 0
        self.fn_release_count = 0
        self.fn_action_triggered = False
        self.fn_button_used_for_override = False  # Track if FN button was used for latch override

    def update_buttons(self, current_time):
        """
        Update the state of all buttons.
        """
        self.fn_button.update()

        # FN Button logic
        if self.fn_button.rose:
            print("FN Button Released")
            if self.fn_button_used_for_override:
                print("FN Button was used for latch override; skipping mode toggle")
                self.fn_release_count = 0
                self.fn_action_triggered = False
                self.fn_button_used_for_override = False  # Reset the flag
            else:
                # Check if the release is within the double press interval
                if (current_time - self.last_fn_release_time) < DOUBLE_PRESS_INTERVAL:
                    self.fn_release_count += 1
                else:
                    self.fn_release_count = 1
                self.last_fn_release_time = current_time

        # Handle FN button single and double press actions
        if self.fn_release_count > 0 and (current_time - self.last_fn_release_time) > DOUBLE_PRESS_INTERVAL:
            if self.fn_release_count == 1 and not self.fn_action_triggered:
                print("Single FN Press Detected: Toggling CC/Note Mode")
                self.mode_manager.toggle_mode_cc_note()
            elif self.fn_release_count >= 2:
                print("Double FN Press Detected: Toggling Latch Modes")
                self.mode_manager.toggle_latch_mode()
            self.fn_release_count = 0
            self.fn_action_triggered = False

        any_button_held_or_latched = False

        for idx, button in enumerate(self.drumpad_buttons):
            button.update()

            if button.fell:
                # Update button held state
                self.mode_manager.button_held_states[idx] = True

                if self.mode_manager.is_cc_mode:
                    self.handle_cc_mode_button_press(idx)

                    # Light up the button when held in CC mode with latch disabled
                    if not self.mode_manager.cc_latch_active and not self.mode_manager.cc_button_latched[idx]:
                        print(f"Button {idx} held in CC mode with latch disabled")
                        set_pixel_color_cc(idx)
                else:
                    self.handle_note_mode_button_press(idx)

            if button.rose:
                # Update button held state
                self.mode_manager.button_held_states[idx] = False

                if self.mode_manager.is_cc_mode:
                    self.handle_cc_mode_button_release(idx)
                    if not self.mode_manager.cc_latch_active and not self.mode_manager.cc_button_latched[idx]:
                        print(f"Button {idx} released in CC mode with latch disabled")
                        clear_pixel(idx)
                else:
                    self.handle_note_mode_button_release(idx)

            if self.mode_manager.is_cc_mode:
                if self.mode_manager.cc_button_latched[idx] or self.mode_manager.button_held_states[idx]:
                    any_button_held_or_latched = True
            else:
                if self.mode_manager.note_button_latched[idx] or self.mode_manager.button_held_states[idx]:
                    any_button_held_or_latched = True

        return any_button_held_or_latched

    def handle_cc_mode_button_press(self, idx):
        """
        Handle button press events when in CC mode.
        """
        if idx == BANK_DOWN_IDX and not self.fn_button.value:
            blink_next_color()
            self.fn_action_triggered = True
        elif idx == BANK_UP_IDX and not self.fn_button.value:
            blink_prev_color()
            self.fn_action_triggered = True
        else:
            if not self.fn_button.value:
                self.fn_button_used_for_override = True  # Set the flag
                if self.mode_manager.cc_latch_active:
                    # Temporarily disable latch
                    print(f"Button {idx} pressed with FN button in CC latch mode (temporary unlatch)")
                    set_pixel_color_cc(idx)
                else:
                    # Override latch mode for this pad
                    self.mode_manager.cc_button_latched[idx] = not self.mode_manager.cc_button_latched[idx]
                    if self.mode_manager.cc_button_latched[idx]:
                        print(f"Button {idx} latched in CC mode via FN button")
                        set_pixel_color_cc(idx)
                    else:
                        print(f"Button {idx} unlatched in CC mode via FN button")
                        clear_pixel(idx)
            else:
                if self.mode_manager.cc_latch_active:
                    self.mode_manager.cc_button_latched[idx] = not self.mode_manager.cc_button_latched[idx]
                    if self.mode_manager.cc_button_latched[idx]:
                        print(f"Button {idx} latched in CC mode")
                        set_pixel_color_cc(idx)
                    else:
                        print(f"Button {idx} unlatched in CC mode")
                        clear_pixel(idx)
                else:
                    # In non-latch mode, button held state is already updated
                    pass

    def handle_cc_mode_button_release(self, idx):
        """
        Handle button release events when in CC mode.
        """
        if not self.fn_button.value and self.mode_manager.cc_latch_active:
            # In latch mode with FN button held, temporary unlatch; clear LED
            print(f"Button {idx} released with FN button in CC latch mode")
            clear_pixel(idx)

    def handle_note_mode_button_press(self, idx):
        """
        Handle button press events when in Note mode.
        """
        if idx == BANK_DOWN_IDX and not self.fn_button.value:
            bank_idx = change_midi_bank(False)
            display_midi_bank_down(bank_idx)
            print("Bank Down")
            self.fn_action_triggered = True
            return
        elif idx == BANK_UP_IDX and not self.fn_button.value:
            bank_idx = change_midi_bank(True)
            display_midi_bank_up(bank_idx)
            print("Bank Up")
            self.fn_action_triggered = True
            return

        if self.mode_manager.note_button_latched[idx]:
            # The pad is already latched
            if not self.fn_button.value and self.mode_manager.note_latch_active:
                # FN button held in latch mode: temporary unlatch behavior
                self.fn_button_used_for_override = True  # Set the flag
                print(f"Button {idx} pressed with FN button in Note latch mode (temporary unlatch)")
                send_midi_note_on(idx)
                set_pixel_color_note(idx)
            else:
                # Unlatch the pad
                self.mode_manager.note_button_latched[idx] = False
                print(f"Button {idx} unlatched in Note mode")
                send_midi_note_off(idx)
                clear_pixel(idx)
        else:
            if not self.fn_button.value:
                self.fn_button_used_for_override = True  # Set the flag
                if self.mode_manager.note_latch_active:
                    # FN button held in latch mode: temporary unlatch behavior
                    print(f"Button {idx} pressed with FN button in Note latch mode (temporary unlatch)")
                    send_midi_note_on(idx)
                    set_pixel_color_note(idx)
                else:
                    # Override latch mode for this pad
                    self.mode_manager.note_button_latched[idx] = True
                    print(f"Button {idx} latched in Note mode via FN button")
                    send_midi_note_on(idx)
                    set_pixel_color_note(idx)
            else:
                if self.mode_manager.note_latch_active:
                    # In latch mode: latch the pad
                    self.mode_manager.note_button_latched[idx] = True
                    print(f"Button {idx} latched in Note mode")
                    send_midi_note_on(idx)
                    set_pixel_color_note(idx)
                else:
                    # In unlatched mode: send note on
                    send_midi_note_on(idx)
                    set_pixel_color_note(idx)

    def handle_note_mode_button_release(self, idx):
        """
        Handle button release events in Note mode.
        """
        if self.fn_button.value:
            # FN button not held
            if not self.mode_manager.note_latch_active and not self.mode_manager.note_button_latched[idx]:
                # Not latched, send note off on release
                send_midi_note_off(idx)
                clear_pixel(idx)
        else:
            # FN button held
            if self.mode_manager.note_latch_active:
                # Temporary unlatch behavior
                print(f"Button {idx} released with FN button in Note latch mode")
                send_midi_note_off(idx)
                clear_pixel(idx)
            else:
                # No action needed; latch state handled elsewhere
                pass


class SliderHandler:
    """
    Handles the sliders and sends MIDI CC messages.
    """
    def __init__(self, mode_manager):
        self.mode_manager = mode_manager

    def handle_slider_changes(self, any_button_held_or_latched):
        """
        Handle slider value changes and send appropriate MIDI CC messages.
        """
        sliders_changed = sliders.update()
        if sliders_changed:
            for idx, slider_changed in enumerate(sliders.midi_value_changed):
                if not slider_changed:
                    continue

                current_value = sliders.current_slide_pots_midi[idx]

                if not self.mode_manager.is_cc_mode:
                    # Always send global CCs in Note mode
                    send_control_change(slide_cc_vals[idx], current_value)

                else:
                    # CC mode
                    if any_button_held_or_latched:
                        # Buttons are latched or held, send button-specific CC messages
                        for button_idx in range(16):
                            if self.mode_manager.cc_button_latched[button_idx] or self.mode_manager.button_held_states[button_idx]:
                                cc_num = slide_cc_vals_held[button_idx][idx]
                                send_control_change(cc_num, current_value)
                    else:
                        # No buttons latched or held, send global CC messages
                        send_control_change(slide_cc_vals[idx], current_value)


def main():
    # Initialize components
    mode_manager = ModeManager()
    button_handler = ButtonHandler(mode_manager)
    slider_handler = SliderHandler(mode_manager)

    draw_HI()  # Splash screen

    while True:
        current_time = time.monotonic()
        any_button_held_or_latched = button_handler.update_buttons(current_time)
        slider_handler.handle_slider_changes(any_button_held_or_latched)


if __name__ == "__main__":
    main()