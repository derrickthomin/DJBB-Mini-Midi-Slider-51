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
    BANK_DOWN_IDX, BANK_UP_IDX, draw_C, draw_N, draw_NC,
    set_pixel_color_cc, set_pixel_color_note, clear_pixel, set_pixel_color_nc,
    update_cc_pixels, draw_HI, blink_next_color, blink_prev_color,
    draw_lock_icon, draw_unlock_icon,
    display_velocity, clear_pixels  # Imported functions
)
from settings import debug_print, load_cc_vals_from_file

# Constants
DOUBLE_PRESS_INTERVAL = 0.3  # seconds
HOLD_THRESHOLD = 0.5  # seconds (FN button hold threshold to suppress mode change)

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
slide_cc_vals = all_cc_vals[0]  # Global CC numbers for sliders
slide_cc_vals_held = all_cc_vals[1]  # CC numbers per button per slider when buttons are held or latched


class ModeManager:
    """
    Manages the MIDI controller's modes, latch states, and velocities.
    Modes: 'Note', 'CC', 'N+C' (Note and CC combined)
    """

    def __init__(self):
        self.mode = 'Note'  # Modes can be 'Note', 'CC', or 'N+C'
        self.cc_latch_active = True
        self.note_latch_active = False
        self.nc_latch_active = False  # Latch state for N+C mode
        self.cc_button_latched = [False] * 16
        self.note_button_latched = [False] * 16
        self.button_held_states = [False] * 16
        self.global_velocity = 100  # Default global MIDI velocity
        self.note_velocities = [None] * 16  # Per-pad velocities (None means use global velocity)

    def cycle_mode(self):
        """
        Cycles through the modes: 'Note' -> 'CC' -> 'N+C' -> 'Note' -> ...
        """
        previous_mode = self.mode
        if self.mode == 'Note':
            self.mode = 'CC'
        elif self.mode == 'CC':
            self.mode = 'N+C'
        else:  # self.mode == 'N+C'
            self.mode = 'Note'
        self.update_mode(previous_mode)

    def update_mode(self, previous_mode):
        """
        Updates the LEDs and other settings based on the current mode.
        Should be called whenever mode changes.
        """
        # When switching away from N+C mode, send note off messages for latched notes
        if previous_mode == 'N+C' and self.mode != 'N+C':
            for idx in range(16):
                if self.note_button_latched[idx]:
                    send_midi_note_off(idx)
                clear_pixel(idx)
            print("Sent note off for latched notes when leaving N+C mode")

        if self.mode == 'CC':
            # Entering CC mode
            draw_C()
            # Update LEDs for CC mode
            for idx in range(16):
                if self.cc_latch_active:
                    if self.cc_button_latched[idx]:
                        set_pixel_color_cc(idx)
                    else:
                        clear_pixel(idx)
                else:
                    # In unlocked CC mode, no LEDs are lit unless pressed
                    clear_pixel(idx)

        elif self.mode == 'Note':
            # Entering Note mode
            draw_N()
            # Update LEDs for Note mode
            for idx in range(16):
                if self.note_button_latched[idx]:
                    set_pixel_color_note(idx)
                else:
                    clear_pixel(idx)

        elif self.mode == 'N+C':
            # Entering N+C mode
            draw_NC()
            # Do not display lock/unlock icon when switching modes
            # Update LEDs for N+C mode
            for idx in range(16):
                if self.nc_latch_active:
                    if self.note_button_latched[idx]:
                        set_pixel_color_nc(idx)
                    else:
                        clear_pixel(idx)
                else:
                    # In unlocked N+C mode, no LEDs are lit unless pressed
                    clear_pixel(idx)

    def toggle_latch_mode(self):
        """
        Toggle the latch mode for the current active mode.
        """
        if self.mode == 'CC':
            self.cc_latch_active = not self.cc_latch_active
            if self.cc_latch_active:
                print("CC Latch Mode Enabled")
                draw_lock_icon()
            else:
                print("CC Latch Mode Disabled")
                draw_unlock_icon()
        elif self.mode == 'Note':
            self.note_latch_active = not self.note_latch_active
            if self.note_latch_active:
                print("Note Latch Mode Enabled")
                draw_lock_icon()
            else:
                print("Note Latch Mode Disabled")
                draw_unlock_icon()
        elif self.mode == 'N+C':
            # Toggle N+C latch mode
            self.nc_latch_active = not self.nc_latch_active
            if self.nc_latch_active:
                print("N+C Latch Mode Enabled")
                draw_lock_icon()
            else:
                print("N+C Latch Mode Disabled")
                draw_unlock_icon()
            # Update LEDs to reflect latch state
            for idx in range(16):
                if self.nc_latch_active:
                    if self.note_button_latched[idx]:
                        set_pixel_color_nc(idx)
                    else:
                        clear_pixel(idx)
                else:
                    clear_pixel(idx)


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
        self.fn_button_pressed = False  # Track if FN button is currently pressed
        # Initialize drumpad buttons
        self.drumpad_buttons = []
        for pin in DRUMPAD_BTN_PINS:
            button_input = digitalio.DigitalInOut(pin)
            button_input.direction = digitalio.Direction.INPUT
            button_input.pull = digitalio.Pull.UP
            self.drumpad_buttons.append(Button(button_input))
        # Timing variables for FN button
        self.last_fn_press_time = None
        self.last_fn_release_time = 0
        self.fn_release_count = 0
        self.fn_action_triggered = False
        self.fn_button_used_for_override = False  # Track if FN button was used for latch override
        self.fn_button_used_for_velocity = False  # Track if FN button was used for velocity adjustment
        self.fn_hold_suppressed = False  # Suppress mode change if FN button held beyond threshold
        # Flag to track per-pad velocity adjustment
        self.per_pad_velocity_adjustment = False  # Track if per-pad velocity adjustment is in progress

    def update_buttons(self, current_time):
        """
        Update the state of all buttons.
        """
        self.fn_button.update()
        self.fn_button_pressed = not self.fn_button.value  # Update FN button pressed state

        # FN Button logic
        if self.fn_button.fell:
            # FN button was pressed
            self.last_fn_press_time = current_time
            self.fn_hold_suppressed = False  # Reset suppress flag
            print("FN Button Pressed")

        if self.fn_button.rose:
            # FN button was released
            hold_duration = current_time - self.last_fn_press_time if self.last_fn_press_time else 0
            print(f"FN Button Released after {hold_duration:.2f}s")
            if self.fn_button_used_for_override or self.fn_hold_suppressed:
                # FN button was used for latch override or held beyond threshold; skip mode change
                print("FN Button action suppressed; skipping mode toggle")
                self.fn_release_count = 0
                self.fn_action_triggered = False
                self.fn_button_used_for_override = False  # Reset the flag
                self.fn_hold_suppressed = False  # Reset hold suppress flag
            else:
                # Check if the release is within the double press interval
                if (current_time - self.last_fn_release_time) < DOUBLE_PRESS_INTERVAL:
                    self.fn_release_count += 1
                else:
                    self.fn_release_count = 1
                self.last_fn_release_time = current_time

            # Clear velocity display and re-display latched notes if velocity was adjusted
            if self.fn_button_used_for_velocity:
                # Clear the velocity display
                clear_pixels()
                # Re-display any latched note LEDs if in Note or N+C mode
                if self.mode_manager.mode == 'Note':
                    self.mode_manager.update_mode('Note')  # Update LEDs
                elif self.mode_manager.mode == 'N+C':
                    self.mode_manager.update_mode('N+C')  # Update LEDs
                self.fn_button_used_for_velocity = False  # Reset the flag

        # Suppress mode change if FN button held beyond HOLD_THRESHOLD
        if self.fn_button_pressed and not self.fn_hold_suppressed:
            hold_duration = current_time - self.last_fn_press_time if self.last_fn_press_time else 0
            if hold_duration >= HOLD_THRESHOLD:
                self.fn_hold_suppressed = True
                print(f"FN Button held for {hold_duration:.2f}s; suppressing mode change on release")

        # Handle FN button single and double press actions
        if self.fn_release_count > 0 and (current_time - self.last_fn_release_time) > DOUBLE_PRESS_INTERVAL:
            if self.fn_release_count == 1 and not self.fn_action_triggered:
                print("Single FN Press Detected: Cycling Mode")
                self.mode_manager.cycle_mode()
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
                if self.mode_manager.mode == 'CC':
                    self.handle_cc_mode_button_press(idx)
                elif self.mode_manager.mode == 'Note':
                    self.handle_note_mode_button_press(idx)
                elif self.mode_manager.mode == 'N+C':
                    self.handle_nc_mode_button_press(idx)
            if button.rose:
                # Update button held state
                self.mode_manager.button_held_states[idx] = False
                if self.mode_manager.mode == 'CC':
                    self.handle_cc_mode_button_release(idx)
                elif self.mode_manager.mode == 'Note':
                    self.handle_note_mode_button_release(idx)
                elif self.mode_manager.mode == 'N+C':
                    self.handle_nc_mode_button_release(idx)

        # Check if per-pad velocity adjustment was in progress
        if not any(self.mode_manager.button_held_states):
            # All pads are released
            if self.per_pad_velocity_adjustment:
                # Clear the velocity display
                clear_pixels()
                # Re-display any latched note LEDs if in Note or N+C mode
                if self.mode_manager.mode == 'Note':
                    self.mode_manager.update_mode('Note')  # Update LEDs
                elif self.mode_manager.mode == 'N+C':
                    self.mode_manager.update_mode('N+C')  # Update LEDs
                self.per_pad_velocity_adjustment = False  # Reset the flag

        # Check if any button is held or latched
        for idx in range(16):
            if self.mode_manager.mode == 'CC':
                if self.mode_manager.cc_button_latched[idx] or self.mode_manager.button_held_states[idx]:
                    any_button_held_or_latched = True
            elif self.mode_manager.mode == 'Note':
                if self.mode_manager.note_button_latched[idx] or self.mode_manager.button_held_states[idx]:
                    any_button_held_or_latched = True
            elif self.mode_manager.mode == 'N+C':
                if self.mode_manager.nc_latch_active:
                    if self.mode_manager.note_button_latched[idx]:
                        any_button_held_or_latched = True
                else:
                    if self.mode_manager.button_held_states[idx]:
                        any_button_held_or_latched = True

        return any_button_held_or_latched

    def handle_nc_mode_button_press(self, idx):
        """
        Handle button press events when in N+C mode (combined Note and CC).
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

        velocity = self.mode_manager.global_velocity

        if self.mode_manager.nc_latch_active:
            # N+C latch is active
            if not self.fn_button.value:
                # FN button is held
                self.fn_button_used_for_override = True
                # Temporarily unlock pad
                send_midi_note_on(idx, velocity)
                set_pixel_color_nc(idx)
                print(f"Button {idx} temporarily unlocked in N+C mode with FN")
            else:
                if self.mode_manager.note_button_latched[idx]:
                    # Pad is already latched, unlatch it
                    self.mode_manager.note_button_latched[idx] = False
                    print(f"Button {idx} unlatched in N+C mode")
                    send_midi_note_off(idx)
                    clear_pixel(idx)
                else:
                    # Latch the pad
                    self.mode_manager.note_button_latched[idx] = True
                    print(f"Button {idx} latched in N+C mode")
                    send_midi_note_on(idx, velocity)
                    set_pixel_color_nc(idx)
        else:
            # N+C latch is inactive (unlocked)
            if not self.fn_button.value:
                # FN button is held
                self.fn_button_used_for_override = True
                # Latch the pad
                self.mode_manager.note_button_latched[idx] = True
                print(f"Button {idx} latched in N+C mode via FN button")
                send_midi_note_on(idx, velocity)
                set_pixel_color_nc(idx)
            else:
                # Send note on when button is pressed
                send_midi_note_on(idx, velocity)
                set_pixel_color_nc(idx)

    def handle_nc_mode_button_release(self, idx):
        """
        Handle button release events when in N+C mode.
        """
        if self.mode_manager.nc_latch_active:
            # N+C latch is active
            if not self.fn_button.value:
                # FN button was held, temporarily unlocked pad
                send_midi_note_off(idx)
                clear_pixel(idx)
                print(f"Button {idx} released in N+C mode with FN button")
            else:
                # Latch mode, no action needed
                pass
        else:
            # N+C latch is inactive (unlocked)
            if self.mode_manager.note_button_latched[idx]:
                # Pad was latched via FN button, stay latched
                pass
            else:
                send_midi_note_off(idx)
                clear_pixel(idx)
                print(f"Button {idx} released in N+C mode")

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

        # Determine velocity
        if self.mode_manager.note_velocities[idx] is not None:
            velocity = self.mode_manager.note_velocities[idx]
        else:
            velocity = self.mode_manager.global_velocity

        if self.mode_manager.note_button_latched[idx]:
            # The pad is already latched
            if not self.fn_button.value and self.mode_manager.note_latch_active:
                # FN button held in latch mode: temporary unlatch behavior
                self.fn_button_used_for_override = True  # Set the flag
                print(f"Button {idx} pressed with FN button in Note latch mode (temporary unlatch)")
                send_midi_note_on(idx, velocity)
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
                    send_midi_note_on(idx, velocity)
                    set_pixel_color_note(idx)
                else:
                    # Override latch mode for this pad
                    self.mode_manager.note_button_latched[idx] = True
                    print(f"Button {idx} latched in Note mode via FN button")
                    send_midi_note_on(idx, velocity)
                    set_pixel_color_note(idx)
            else:
                if self.mode_manager.note_latch_active:
                    # In latch mode: latch the pad
                    self.mode_manager.note_button_latched[idx] = True
                    print(f"Button {idx} latched in Note mode")
                    send_midi_note_on(idx, velocity)
                    set_pixel_color_note(idx)
                else:
                    # In unlatched mode: send note on
                    send_midi_note_on(idx, velocity)
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
                print(f"Button {idx} released in Note mode")
            else:
                # No action needed; latch state handled elsewhere
                pass
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

    def handle_cc_mode_button_press(self, idx):
        """
        Handle button press events when in CC mode.
        """
        if idx == BANK_DOWN_IDX and not self.fn_button.value:
            blink_next_color()
            self.fn_action_triggered = True
            return
        elif idx == BANK_UP_IDX and not self.fn_button.value:
            blink_prev_color()
            self.fn_action_triggered = True
            return

        if self.mode_manager.cc_latch_active:
            if not self.fn_button.value:
                # FN button is held
                self.fn_button_used_for_override = True
                # Temporarily activate pad
                set_pixel_color_cc(idx)
                print(f"Button {idx} temporarily activated in CC mode with FN")
            else:
                # Toggle latch state
                self.mode_manager.cc_button_latched[idx] = not self.mode_manager.cc_button_latched[idx]
                if self.mode_manager.cc_button_latched[idx]:
                    set_pixel_color_cc(idx)
                    print(f"Button {idx} latched in CC mode")
                else:
                    clear_pixel(idx)
                    print(f"Button {idx} unlatched in CC mode")
        else:
            # CC latch is inactive (unlocked)
            # Light up the pad while held
            set_pixel_color_cc(idx)
            print(f"Button {idx} pressed in CC mode")

    def handle_cc_mode_button_release(self, idx):
        """
        Handle button release events when in CC mode.
        """
        if self.mode_manager.cc_latch_active:
            if not self.fn_button.value:
                # FN button was held
                clear_pixel(idx)
                print(f"Button {idx} released in CC mode with FN button")
            else:
                # Latch mode, no action needed
                pass
        else:
            # CC latch is inactive (unlocked)
            # Turn off the pad LED
            clear_pixel(idx)
            print(f"Button {idx} released in CC mode")


class SliderHandler:
    """
    Handles the sliders and sends MIDI CC messages or adjusts velocities.
    """

    def __init__(self, mode_manager, button_handler):
        self.mode_manager = mode_manager
        self.button_handler = button_handler  # Access to FN button state

    def handle_slider_changes(self, any_button_held_or_latched):
        """
        Handle slider value changes and send appropriate MIDI CC messages or adjust velocities.
        """
        sliders_changed = sliders.update()
        if sliders_changed:
            if self.mode_manager.mode == 'Note':
                # In Note mode
                # Check if slider 1 has changed
                if sliders.midi_value_changed[0]:  # Slider 1
                    current_slider1_value = sliders.current_slide_pots_midi[0]
                    # Check if FN button is pressed for adjusting global velocity
                    if self.button_handler.fn_button_pressed:
                        # Update global MIDI velocity
                        self.mode_manager.global_velocity = current_slider1_value
                        print(f"Global MIDI velocity changed to {current_slider1_value}")
                        # Display the velocity on the grid
                        display_velocity(self.mode_manager.global_velocity)
                        # Set flag to indicate velocity adjustment
                        self.button_handler.fn_button_used_for_velocity = True
                        # Do not re-trigger any notes
                    # Check if any pads are physically held (excluding latched pads)
                    elif any(self.mode_manager.button_held_states):
                        # For each physically held pad, update its velocity
                        self.button_handler.per_pad_velocity_adjustment = True  # Set the flag
                        for idx, is_held in enumerate(self.mode_manager.button_held_states):
                            if is_held:
                                self.mode_manager.note_velocities[idx] = current_slider1_value
                                print(f"Pad {idx} velocity changed to {current_slider1_value}")
                                # Re-trigger note with new velocity
                                send_midi_note_off(idx)
                                send_midi_note_on(idx, current_slider1_value)
                        # Skip sending global CC messages for Slider 1
                    else:
                        # Optional: Handle slider 1 in Note mode without FN or pads held
                        # Send global CC message for Slider 1
                        send_control_change(slide_cc_vals[0], current_slider1_value)

                # Handle other sliders (e.g., slider 2 and 3)
                for idx, slider_changed in enumerate(sliders.midi_value_changed):
                    if idx == 0:
                        # Slider 1 already handled
                        continue
                    if slider_changed:
                        current_value = sliders.current_slide_pots_midi[idx]
                        # Send global CC messages
                        send_control_change(slide_cc_vals[idx], current_value)

            elif self.mode_manager.mode == 'CC':
                # CC mode handling
                if any_button_held_or_latched:
                    # Buttons are latched or held, send button-specific CC messages
                    for idx, slider_changed in enumerate(sliders.midi_value_changed):
                        if not slider_changed:
                            continue
                        current_value = sliders.current_slide_pots_midi[idx]
                        for button_idx in range(16):
                            if self.mode_manager.cc_button_latched[button_idx] or \
                               self.mode_manager.button_held_states[button_idx]:
                                cc_num = slide_cc_vals_held[button_idx][idx]
                                send_control_change(cc_num, current_value)
                else:
                    # No buttons latched or held, send global CC messages
                    for idx, slider_changed in enumerate(sliders.midi_value_changed):
                        if slider_changed:
                            current_value = sliders.current_slide_pots_midi[idx]
                            send_control_change(slide_cc_vals[idx], current_value)

            elif self.mode_manager.mode == 'N+C':
                # N+C mode handling
                if self.mode_manager.nc_latch_active:
                    # N+C latch is active
                    if any(self.mode_manager.note_button_latched):
                        # Pads are latched, send pad-specific CC messages
                        for idx, slider_changed in enumerate(sliders.midi_value_changed):
                            if slider_changed:
                                current_value = sliders.current_slide_pots_midi[idx]
                                for button_idx in range(16):
                                    if self.mode_manager.note_button_latched[button_idx]:
                                        cc_num = slide_cc_vals_held[button_idx][idx]
                                        send_control_change(cc_num, current_value)
                    else:
                        # Optionally, send global CC messages if no pads are latched
                        for idx, slider_changed in enumerate(sliders.midi_value_changed):
                            if slider_changed:
                                current_value = sliders.current_slide_pots_midi[idx]
                                send_control_change(slide_cc_vals[idx], current_value)
                else:
                    # N+C latch is inactive
                    if any(self.mode_manager.button_held_states):
                        # Pads are being held, send pad-specific CC messages
                        for idx, slider_changed in enumerate(sliders.midi_value_changed):
                            if slider_changed:
                                current_value = sliders.current_slide_pots_midi[idx]
                                for button_idx in range(16):
                                    if self.mode_manager.button_held_states[button_idx]:
                                        cc_num = slide_cc_vals_held[button_idx][idx]
                                        send_control_change(cc_num, current_value)
                    else:
                        # Optionally, send global CC messages if no pads are held
                        for idx, slider_changed in enumerate(sliders.midi_value_changed):
                            if slider_changed:
                                current_value = sliders.current_slide_pots_midi[idx]
                                send_control_change(slide_cc_vals[idx], current_value)


def main():
    # Initialize components
    mode_manager = ModeManager()
    button_handler = ButtonHandler(mode_manager)
    slider_handler = SliderHandler(mode_manager, button_handler)
    draw_HI()  # Splash screen
    while True:
        current_time = time.monotonic()
        any_button_held_or_latched = button_handler.update_buttons(current_time)
        slider_handler.handle_slider_changes(any_button_held_or_latched)


if __name__ == "__main__":
    main()