# button_handler.py

import board
import digitalio
from adafruit_debouncer import Button
from midi import send_midi_note_on, send_midi_note_off, change_midi_bank
from display import (
    set_pixel_color_note, set_pixel_color_cc, set_pad_pixel_color_nc,
    clear_pixel, display_midi_bank_down, display_midi_bank_up,
    blink_next_color, blink_prev_color, clear_pixels, update_pad_led
)
from settings import DOUBLE_PRESS_INTERVAL, HOLD_THRESHOLD, debug_print
from display import BANK_DOWN_IDX, BANK_UP_IDX

# FN button state constants
FN_STATE_IDLE = 0        # FN button not pressed
FN_STATE_PRESSED = 1     # FN button pressed but not yet used for any action
FN_STATE_USED = 2        # FN button pressed and used for an action
FN_STATE_HELD = 3        # FN button held beyond hold threshold
NUM_PADS = 16

class ButtonHandler:
    """
    Handles drum pad and FN button inputs.

    Attributes:
        mode_manager (ModeManager): Reference to the ModeManager instance.
        fn_button (Button): Debounced FN button.
        fn_button_pressed (bool): State of the FN button.
        pad_buttons (list): List of debounced pad buttons.
        last_fn_press_time (float): Timestamp of the last FN button press.
        last_fn_release_time (float): Timestamp of the last FN button release.
        single_press_timer (float): Timer for single press detection.
        fn_press_count (int): Count of FN button presses.
        function_button_state (int): Current state of the FN button.
        per_pad_velocity_adjustment (bool): Flag for per-pad velocity adjustment.
    """

    def __init__(self, mode_manager):
        """
        Initializes the ButtonHandler with the given ModeManager.

        Args:
            mode_manager (ModeManager): The ModeManager instance.
        """
        self.mode_manager = mode_manager

        # Initialize the FN button
        fn_input = digitalio.DigitalInOut(board.GP1)
        fn_input.direction = digitalio.Direction.INPUT
        fn_input.pull = digitalio.Pull.UP
        self.fn_button = Button(fn_input)
        self.fn_button_pressed = False

        # Initialize drum pad buttons
        self.pad_buttons = []
        pad_pins = [
            board.GP17, board.GP16, board.GP15, board.GP14,
            board.GP19, board.GP18, board.GP12, board.GP13,
            board.GP21, board.GP9, board.GP6, board.GP7,
            board.GP4, board.GP0, board.GP2, board.GP5
        ]
        for pin in pad_pins:
            pad_input = digitalio.DigitalInOut(pin)
            pad_input.direction = digitalio.Direction.INPUT
            pad_input.pull = digitalio.Pull.UP
            self.pad_buttons.append(Button(pad_input))

        # FN button timing variables
        self.last_fn_press_time = None
        self.last_fn_release_time = 0
        self.single_press_timer = 0
        self.fn_press_count = 0
        self.function_button_state = FN_STATE_IDLE

        # Velocity adjustment flag
        self.per_pad_velocity_adjustment = False
    
    def set_fn_button_state_used(self):
        """
        Sets the FN button state to used.
        """
        self.function_button_state = FN_STATE_USED

    def update_buttons(self, current_time):
        """
        Updates the state of all buttons and handles events.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            tuple: A tuple containing two boolean values:
                - True if any pad is held or latched, False otherwise.
                - True if the display needs to be redrawn, False otherwise.
        """
        self.fn_button.update()
        self.fn_button_pressed = not self.fn_button.value  # Active LOW
        self.handle_fn_button_events(current_time)
        any_pad_active = False
        redraw_display = False

        for idx, pad_button in enumerate(self.pad_buttons):
            pad_button.update()
            if pad_button.fell:
                # Pad pressed
                self.mode_manager.pad_held_states[idx] = True
                redraw_display = self.handle_pad_press(idx)

            if pad_button.rose:
                # Pad released
                self.mode_manager.pad_held_states[idx] = False
                self.handle_pad_release(idx)

            # Check if any pad is held or latched
            if self.is_pad_active(idx):
                any_pad_active = True

        # If per-pad velocity adjustment was in progress and all pads are released
        if not any(self.mode_manager.pad_held_states) and self.per_pad_velocity_adjustment:
            clear_pixels()
            self.per_pad_velocity_adjustment = False

        return any_pad_active, redraw_display

    def handle_fn_button_events(self, current_time):
        """
        Handles events related to the FN button.

        Args:
            current_time (float): The current time in seconds.
        """
        if self.fn_button.fell:
            self._on_fn_button_press(current_time)

        if self.fn_button_pressed:
            self._on_fn_button_hold(current_time)

        if self.fn_button.rose:
            self._on_fn_button_release(current_time)

        self._handle_single_press(current_time)

    def _on_fn_button_press(self, current_time):
        """
        Handles FN button press event.

        Args:
            current_time (float): The current time in seconds.
        """
        self.last_fn_press_time = current_time
        self.function_button_state = FN_STATE_PRESSED
        debug_print("FN Button Pressed")

    def _on_fn_button_hold(self, current_time):
        """
        Handles FN button hold event.

        Args:
            current_time (float): The current time in seconds.
        """
        hold_duration = current_time - self.last_fn_press_time
        if hold_duration >= HOLD_THRESHOLD and self.function_button_state == FN_STATE_PRESSED:
            self.function_button_state = FN_STATE_HELD
            debug_print(f"FN Button held for {hold_duration:.2f}s; suppressing mode change on release")

    def _on_fn_button_release(self, current_time):
        """
        Handles FN button release event.

        Args:
            current_time (float): The current time in seconds.
        """
        self.mode_manager.set_currently_displaying_velocity(False)
        hold_duration = current_time - self.last_fn_press_time
        debug_print(f"FN Button Released after {hold_duration:.2f}s")

        if self.mode_manager.global_velocity_changed:
            self.mode_manager.refresh_display()
            self.mode_manager.global_velocity_changed = False

        if self.function_button_state in {FN_STATE_USED, FN_STATE_HELD}:
            debug_print("FN Button action suppressed; skipping mode change")
            self.fn_press_count = 0
        else:
            self._handle_fn_press_count(current_time)

    def _handle_fn_press_count(self, current_time):
        """
        Handles the count of FN button presses for single or double press detection.

        Args:
            current_time (float): The current time in seconds.
        """
        time_since_last_release = current_time - self.last_fn_release_time
        if time_since_last_release < DOUBLE_PRESS_INTERVAL:
            self.fn_press_count += 1
            if self.fn_press_count == 2:
                debug_print("Double FN Press Detected: Toggling Latch Modes")
                self.mode_manager.toggle_latch_mode()
                self.fn_press_count = 0
                self.function_button_state = FN_STATE_IDLE
        else:
            self.fn_press_count = 1
            self.single_press_timer = current_time
        self.last_fn_release_time = current_time

    def _handle_single_press(self, current_time):
        """
        Handles single press event after the interval.

        Args:
            current_time (float): The current time in seconds.
        """
        if self.fn_press_count == 1 and (current_time - self.single_press_timer) >= DOUBLE_PRESS_INTERVAL:
            if self.function_button_state == FN_STATE_PRESSED:
                debug_print("Single FN Press Detected: Cycling Mode")
                self.mode_manager.cycle_mode()
            else:
                debug_print("FN Button action suppressed; skipping mode change")
            self.fn_press_count = 0
            self.function_button_state = FN_STATE_IDLE

    def handle_pad_press(self, idx):
        """
        Handles pad press based on the current mode.

        Args:
            idx (int): Index of the pad.

        Returns:
            bool: True if the display needs to be redrawn, False otherwise.
        """
        redraw_display = False  # Set to True if display needs to be redrawn, like after changing banks

        if self.mode_manager.mode == 'Note':
            redraw_display = self.handle_note_mode_pad_press(idx)
        elif self.mode_manager.mode == 'CC':
            redraw_display = self.handle_cc_mode_pad_press(idx)
        elif self.mode_manager.mode == 'N+C':
            redraw_display = self.handle_nc_mode_pad_press(idx)
            
        return redraw_display

    def handle_pad_release(self, idx):
        """
        Handles pad release based on the current mode.

        Args:
            idx (int): Index of the pad.
        """
        if self.mode_manager.mode == 'Note':
            self.handle_note_mode_pad_release(idx)
        elif self.mode_manager.mode == 'CC':
            self.handle_cc_mode_pad_release(idx)
        elif self.mode_manager.mode == 'N+C':
            self.handle_nc_mode_pad_release(idx)

    def is_pad_active(self, idx):
        """
        Checks if a pad is active (held or latched).

        Args:
            idx (int): Index of the pad.

        Returns:
            bool: True if the pad is active, False otherwise.
        """
        mode = self.mode_manager.mode
        pad_latched = {
            'Note': self.mode_manager.note_pad_latched,
            'CC': self.mode_manager.cc_pad_latched,
            'N+C': self.mode_manager.nc_pad_latched
        }.get(mode, [False] * 16)

        return pad_latched[idx] or self.mode_manager.pad_held_states[idx]

    def handle_note_mode_pad_press(self, idx):
        """
        Handles pad press in Note mode.

        Args:
            idx (int): Index of the pad.

        Returns:
            bool: True if the display needs to be redrawn, False otherwise.
        """
        mode = 'Note'

        # --- Function Button Held Block ---
        redraw_display = False
        if not self.fn_button.value:
            self.function_button_state = FN_STATE_USED
            if idx == BANK_DOWN_IDX:
                bank_idx = change_midi_bank(False)
                display_midi_bank_down(bank_idx)
                debug_print("Bank Down")
                redraw_display = True

            elif idx == BANK_UP_IDX:
                bank_idx = change_midi_bank(True)
                display_midi_bank_up(bank_idx)
                debug_print("Bank Up")
                redraw_display = True

            else:
                # Toggle latch with FN button
                self.toggle_pad_latch(mode, idx, use_fn_button=True)

            return redraw_display

        # --- Function Button Not Held Block ---
        if self.mode_manager.note_latch_active or self.mode_manager.note_pad_latched[idx]:
            # Latch mode is active
            self.toggle_pad_latch(mode, idx, use_fn_button=False)
        else:
            # Send Note On for momentary action
            self.send_midi_note_message(idx, note_on=True)
            update_pad_led(mode, idx, active=True)
            debug_print(f"Pad {idx} pressed in Note mode")
                
    def handle_note_mode_pad_release(self, idx):
        """
        Handles pad release in Note mode.

        Args:
            idx (int): Index of the pad.
        """
        mode = 'Note'
        
        if self.fn_button.value:
            # FN button not held
            if not self.mode_manager.note_latch_active and not self.mode_manager.note_pad_latched[idx]:
                # Send Note Off for momentary action
                self.send_midi_note_message(idx, note_on=False)
                update_pad_led(mode, idx, active=False)
                debug_print(f"Pad {idx} released in {mode} mode (momentary)")
        else:
            # FN button held
            if self.mode_manager.note_latch_active:
                # Temporary unlatch behavior
                self.send_midi_note_message(idx, note_on=False)
                update_pad_led(mode, idx, active=False)
                debug_print(f"Pad {idx} released in {mode} mode with FN button")
            else:
                # Pad remains latched; no action needed
                pass

    def handle_cc_mode_pad_press(self, idx):
        """
        Handles pad press in CC mode.

        Args:
            idx (int): Index of the pad.

        Returns:
            bool: True if the display needs to be redrawn, False otherwise.
        """
        mode = 'CC'

        # --- Function Button Held Block ---
        redraw_display = False
        if not self.fn_button.value:
            self.function_button_state = FN_STATE_USED
            if idx == BANK_DOWN_IDX:
                blink_next_color()
                debug_print("Color cycled to next")
                redraw_display = True

            elif idx == BANK_UP_IDX:
                blink_prev_color()
                debug_print("Color cycled to previous")
                redraw_display = True

            else:
                self.toggle_pad_latch(mode, idx, use_fn_button=True)

        # --- Function Button Not Held Block ---
        else:
            if self.mode_manager.cc_latch_active or self.mode_manager.cc_pad_latched[idx]:
                self.toggle_pad_latch(mode, idx, use_fn_button=False)
            else:
                update_pad_led(mode, idx, active=True)
                debug_print(f"Pad {idx} pressed in CC mode")
        
        return redraw_display

    def handle_cc_mode_pad_release(self, idx):
        """
        Handles pad release in CC mode.

        Args:
            idx (int): Index of the pad.
        """
        mode = 'CC'

        if self.fn_button.value:
            # FN button not held
            if not self.mode_manager.cc_latch_active and not self.mode_manager.cc_pad_latched[idx]:
                # Turn off the pad LED for momentary action
                update_pad_led(mode, idx, active=False)
                debug_print(f"Pad {idx} released in CC mode")
        else:
            # FN button held
            if self.mode_manager.cc_latch_active:
                # Temporary unlatch behavior
                update_pad_led(mode, idx, active=False)
                debug_print(f"Pad {idx} released in CC mode with FN button")

    def handle_nc_mode_pad_press(self, idx):
        """
        Handles pad press in N+C mode.

        Args:
            idx (int): Index of the pad.

        Returns:
            bool: True if the display needs to be redrawn, False otherwise.
        """
        mode = 'N+C'
        redraw_display = False

        if not self.fn_button.value:
            # FN button held
            self.function_button_state = FN_STATE_USED
            redraw_display = self._handle_fn_button_held(idx, mode)
        else:
            redraw_display = self._handle_fn_button_not_held(idx, mode)

        return redraw_display

    def _handle_fn_button_held(self, idx, mode):
        """
        Handles pad press when FN button is held.

        Args:
            idx (int): Index of the pad.
            mode (str): Current mode.

        Returns:
            bool: True if the display needs to be redrawn, False otherwise.
        """
        if idx == BANK_DOWN_IDX:
            bank_idx = change_midi_bank(False)
            display_midi_bank_down(bank_idx)
            debug_print("Bank Down")
            return True

        if idx == BANK_UP_IDX:
            bank_idx = change_midi_bank(True)
            display_midi_bank_up(bank_idx)
            debug_print("Bank Up")
            return True

        # Toggle latch with FN button
        self.toggle_pad_latch(mode, idx, use_fn_button=True)
        return False

    def _handle_fn_button_not_held(self, idx, mode):
        """
        Handles pad press when FN button is not held.

        Args:
            idx (int): Index of the pad.
            mode (str): Current mode.

        Returns:
            bool: True if the display needs to be redrawn, False otherwise.
        """
        if self.mode_manager.nc_latch_active or self.mode_manager.nc_pad_latched[idx]:
            # Latch mode is active
            self.toggle_pad_latch(mode, idx, use_fn_button=False)
        else:
            # Send Note On for momentary action
            self.send_midi_note_message(idx, note_on=True)
            update_pad_led(mode, idx, active=True)
            debug_print(f"Pad {idx} pressed in N+C mode")
        return False

    def handle_nc_mode_pad_release(self, idx):
        """
        Handles pad release in N+C mode.

        Args:
            idx (int): Index of the pad.
        """
        mode = 'N+C'

        if self.fn_button.value:
            # FN button not held
            if not self.mode_manager.nc_latch_active and not self.mode_manager.nc_pad_latched[idx]:
                # Send Note Off for momentary action
                self.send_midi_note_message(idx, note_on=False)
                update_pad_led(mode, idx, active=False)
                debug_print(f"Pad {idx} released in N+C mode")
        else:
            # FN button held
            if self.mode_manager.nc_latch_active:
                # Temporary unlatch behavior
                self.send_midi_note_message(idx, note_on=False)
                update_pad_led(mode, idx, active=False)
                debug_print(f"Pad {idx} released in N+C mode with FN button")

    def toggle_pad_latch(self, mode, idx, use_fn_button):
        """
        Toggles the latch state of a pad.

        Args:
            mode (str): The current mode ('Note', 'CC', or 'N+C').
            idx (int): Index of the pad.
            use_fn_button (bool): Whether the FN button is used for this action.
        """
        if use_fn_button:
            self.function_button_state = FN_STATE_USED
        
        # Initialize variables based on mode
        if mode == 'Note':
            latch_active = self.mode_manager.note_latch_active
            pad_latched = self.mode_manager.note_pad_latched
            set_pixel_color = set_pixel_color_note
            send_midi_notes = True
        elif mode == 'CC':
            latch_active = self.mode_manager.cc_latch_active
            pad_latched = self.mode_manager.cc_pad_latched
            set_pixel_color = set_pixel_color_cc
            send_midi_notes = False  # Do not send MIDI notes in CC mode
        elif mode == 'N+C':
            latch_active = self.mode_manager.nc_latch_active
            pad_latched = self.mode_manager.nc_pad_latched
            set_pixel_color = set_pad_pixel_color_nc
            send_midi_notes = True
        else:
            return  # Unknown mode

        # Check if pad is already latched
        if pad_latched[idx]:
            # Pad is already latched; unlatch it
            pad_latched[idx] = False
            clear_pixel(idx)
            debug_print(f"Pad {idx} unlatched in {mode} mode")
            if send_midi_notes:
                # Only send MIDI notes in 'Note' or 'N+C' modes
                self.send_midi_note_message(idx, note_on=False)
            return
        else:
            # Determine whether to latch the pad based on latch_active and use_fn_button
            should_latch = (latch_active and not use_fn_button) or (not latch_active and use_fn_button)

            if should_latch:
                # Latch the pad
                pad_latched[idx] = True
                set_pixel_color(idx)
                debug_print(f"Pad {idx} latched in {mode} mode")
                if send_midi_notes:
                    self.send_midi_note_message(idx, note_on=True)
            else:
                # Momentary action
                if send_midi_notes:
                    self.send_midi_note_message(idx, note_on=True)
                set_pixel_color(idx)
                debug_print(f"Pad {idx} pressed in {mode} mode (momentary)")

    def send_midi_note_message(self, idx, note_on, velocity=None):
        """
        Sends a MIDI note on or off message for a given pad.

        Args:
            idx (int): Index of the pad.
            note_on (bool): True to send Note On, False to send Note Off.
            velocity (int, optional): Velocity for Note On messages.
        """
        if note_on:
            if velocity is None:
                # Use per-pad velocity if set, otherwise use global velocity
                pad_velocity = self.mode_manager.pad_velocities[idx]
                if pad_velocity is not None:
                    velocity = pad_velocity
                else:
                    velocity = self.mode_manager.global_velocity
            send_midi_note_on(idx, velocity)
            debug_print(f"Sent MIDI Note On for pad {idx} with velocity {velocity}")
        else:
            send_midi_note_off(idx)
            debug_print(f"Sent MIDI Note Off for pad {idx}")