import time
from midi import send_control_change, send_midi_note_off, send_midi_note_on
from display import display_velocity, clear_pixels
from settings import slide_cc_vals, slide_cc_vals_held, debug_print
import sliders

class SliderHandler:
    """
    Handles slider value changes and sends MIDI CC messages.

    Attributes:
        mode_manager (ModeManager): Reference to the ModeManager instance.
        button_handler (ButtonHandler): Reference to the ButtonHandler instance.
    """

    DEBOUNCE_DELAY = 0.05  # 50ms debounce delay

    def __init__(self, mode_manager, button_handler):
        self.mode_manager = mode_manager
        self.button_handler = button_handler
        self.current_any_pad_active = False
        self.last_change_time = time.monotonic()

    def handle_slider_changes(self, any_pad_active):
        """
        Handles changes in slider values and sends appropriate MIDI messages.

        Args:
            any_pad_active (bool): Indicates if any pad is currently active.
        """
        current_time = time.monotonic()
        sliders_changed = sliders.update()

        if any_pad_active != self.current_any_pad_active:
            if current_time - self.last_change_time > self.DEBOUNCE_DELAY:
                self.current_any_pad_active = any_pad_active
                self.last_change_time = current_time
                debug_print("[SliderHandler] Pad active state changed. Skipping slider processing this cycle.")
                return
            else:
                debug_print("[SliderHandler] Debouncing pad active state change.")
                return  # Still within debounce period

        if sliders_changed:
            if self.button_handler.fn_button_pressed:
                self.button_handler.set_fn_button_state_used()
            mode = self.mode_manager.mode
            if mode == 'Note':
                self.handle_note_mode_sliders()
            elif mode == 'CC':
                self.handle_cc_mode_sliders(any_pad_active)
            elif mode == 'N+C':
                self.handle_nc_mode_sliders(any_pad_active)
            sliders.reset_changes()

    def handle_note_mode_sliders(self):
        """
        Handles slider changes in 'Note' mode.
        """
        if sliders.midi_value_changed[0]:  # Slider 1
            current_slider1_value = sliders.current_slide_pots_midi[0]
            if self.button_handler.fn_button_pressed and not any(self.mode_manager.pad_held_states): # Just holding FN
                self.mode_manager.global_velocity = current_slider1_value
                self.mode_manager.global_velocity_changed = True
                debug_print(f"Global velocity changed to {current_slider1_value}")
                display_velocity(self.mode_manager.global_velocity, self.mode_manager.currently_displaying_velocity)
                self.mode_manager.set_currently_displaying_velocity(True)
                self.button_handler.set_fn_button_state_used()

            elif self.button_handler.fn_button_pressed and any(self.mode_manager.pad_held_states): # Holding FN and pads
                self.button_handler.per_pad_velocity_adjustment = True
                self.button_handler.set_fn_button_state_used()
                for idx, is_held in enumerate(self.mode_manager.pad_held_states):
                    if is_held:
                        self.mode_manager.pad_velocities[idx] = current_slider1_value
                        display_velocity(current_slider1_value, self.mode_manager.currently_displaying_velocity)
                        debug_print(f"Pad {idx} velocity changed to {current_slider1_value}")
                        send_midi_note_off(idx)
                        send_midi_note_on(idx, current_slider1_value)
                        self.mode_manager.set_currently_displaying_velocity(True)
            else:
                send_control_change(slide_cc_vals[0], current_slider1_value)

        for idx, slider_changed in enumerate(sliders.midi_value_changed):
            if idx == 0:
                continue  # Slider 1 already handled
            if slider_changed:
                current_value = sliders.current_slide_pots_midi[idx]
                send_control_change(slide_cc_vals[idx], current_value)

    def handle_cc_mode_sliders(self, any_pad_active):
        if not any_pad_active:
            # No pads are active; send global CC messages if sliders changed
            self.send_global_slider_cc_messages()
            return

        # Get list of active pads
        active_pads = [idx for idx, active in enumerate(self.mode_manager.cc_pad_latched) if active]
        active_pads.extend([idx for idx, held in enumerate(self.mode_manager.pad_held_states) if held and idx not in active_pads])

        if not active_pads:
            # No pads are latched or held; send global CC messages
            self.send_global_slider_cc_messages()
            return

        for idx, slider_changed in enumerate(sliders.midi_value_changed):
            if slider_changed:
                current_value = sliders.current_slide_pots_midi[idx]
                for pad_idx in active_pads:
                    cc_num = slide_cc_vals_held[pad_idx][idx]
                    send_control_change(cc_num, current_value)
                    
    def send_global_slider_cc_messages(self):
        for idx, slider_changed in enumerate(sliders.midi_value_changed):
            if slider_changed:
                current_value = sliders.current_slide_pots_midi[idx]
                send_control_change(slide_cc_vals[idx], current_value)

    def handle_nc_mode_sliders(self, any_pad_active):
        """
        Handles slider changes in 'N+C' mode.

        Args:
            any_pad_active (bool): Indicates if any pad is currently active.
        """
        if any_pad_active:
            for idx, slider_changed in enumerate(sliders.midi_value_changed):
                if slider_changed:
                    current_value = sliders.current_slide_pots_midi[idx]
                    for pad_idx in range(16):
                        if self.mode_manager.nc_pad_latched[pad_idx] or self.mode_manager.pad_held_states[pad_idx]:
                            cc_num = slide_cc_vals_held[pad_idx][idx]
                            send_control_change(cc_num, current_value)
        else:
            for idx, slider_changed in enumerate(sliders.midi_value_changed):
                if slider_changed:
                    current_value = sliders.current_slide_pots_midi[idx]
                    send_control_change(slide_cc_vals[idx], current_value)
                    