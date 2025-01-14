# mode_manager.py

import midi
from display import (
    draw_C, draw_N, draw_NC, draw_lock_icon, draw_unlock_icon,
    set_pixel_color_note, set_pixel_color_cc, set_pad_pixel_color_nc,
    clear_pixel
)
from settings import debug_print

MODE_NOTE = 'Note'
MODE_CC = 'CC'
MODE_NC = 'N+C'
MODES = [MODE_NOTE, MODE_CC, MODE_NC]

class ModeManager:
    """
    Manages the MIDI controller's modes, latch states, and velocities.

    Modes:
        - 'Note': Pads send MIDI note messages.
        - 'CC': Pads send MIDI CC (Control Change) messages.
        - 'N+C': Pads can send both Note and CC messages.

    Latch Modes:
        - Each mode can be in 'locked' (latch active) or 'unlocked' (latch inactive) state.
        - When locked, pads can latch notes or CC messages.
        - When unlocked, pads function momentarily (notes/CC messages sent only while pad is pressed).

    Attributes:
        mode (str): The current mode ('Note', 'CC', or 'N+C').
        note_latch_active (bool): Indicates if latch is active in Note mode.
        cc_latch_active (bool): Indicates if latch is active in CC mode.
        nc_latch_active (bool): Indicates if latch is active in N+C mode.
        note_pad_latched (list): Track latched pads in Note mode.
        cc_pad_latched (list): Track latched pads in CC mode.
        pad_held_states (list): Track the hold state of pads (True if held).
        global_velocity (int): The global MIDI note velocity.
        pad_velocities (list): Per-pad velocities (if None, uses global velocity).
    """

    def __init__(self):
        self.mode = 'Note'
        self.note_latch_active = False
        self.cc_latch_active = True
        self.nc_latch_active = False
        self.note_pad_latched = [False] * 16
        self.cc_pad_latched = [False] * 16
        self.nc_pad_latched = [False] * 16
        self.pad_held_states = [False] * 16
        self.global_velocity = 100
        self.global_velocity_changed = False
        self.pad_velocities = [None] * 16

        # Display
        self.currently_displaying_velocity = False

    def cycle_mode(self):
        """
        Cycle through modes in order: Note -> CC -> N+C -> Note.
        """
        previous_mode = self.mode
        if self.mode == 'Note':
            self.mode = 'CC'
        elif self.mode == 'CC':
            self.mode = 'N+C'
        else:
            self.mode = 'Note'
        self.update_mode(previous_mode)

    def update_mode(self, previous_mode):
        """
        Update LEDs and other settings when mode changes.

        Args:
            previous_mode (str): The mode prior to the change.
        """
        # Turn off latched notes when leaving N+C mode
        if previous_mode == 'N+C' and self.mode != 'N+C':
            for idx in range(16):
                if self.nc_pad_latched[idx]:
                    # transfer latch to note mode
                    self.note_pad_latched[idx] = True
                    # midi.send_midi_note_off(idx)
                    # self.nc_pad_latched[idx] = False
                    
                clear_pixel(idx)

        # Update display and pad LEDs based on the new mode
        
        if self.mode == 'CC':
            draw_C()
            self.update_cc_mode_leds()
        elif self.mode == 'Note':
            draw_N()
            self.update_note_mode_leds()
        elif self.mode == 'N+C':
            draw_NC()
            self.update_nc_mode_leds()

    def toggle_latch_mode(self):
        """
        Toggle the latch mode for the current mode.
        """
        if self.mode == 'CC':
            self.cc_latch_active = not self.cc_latch_active
            if self.cc_latch_active:
                debug_print("CC Latch Mode Activated")
                draw_lock_icon()
            else:
                debug_print("CC Latch Mode Deactivated")
                draw_unlock_icon()
            self.update_cc_mode_leds()
        elif self.mode == 'Note':
            self.note_latch_active = not self.note_latch_active
            if self.note_latch_active:
                debug_print("Note Latch Mode Activated")
                draw_lock_icon()
            else:
                debug_print("Note Latch Mode Deactivated")
                draw_unlock_icon()
            self.update_note_mode_leds()
        elif self.mode == 'N+C':
            self.nc_latch_active = not self.nc_latch_active
            if self.nc_latch_active:
                debug_print("N+C Latch Mode Activated")
                draw_lock_icon()
            else:
                debug_print("N+C Latch Mode Deactivated")
                draw_unlock_icon()
            self.update_nc_mode_leds()


    def update_note_mode_leds(self):
        """
        Update pad LEDs for Note mode based on latch states.
        """
        for idx in range(16):
            if self.note_pad_latched[idx]:
                set_pixel_color_note(idx)
            else:
                clear_pixel(idx)

    def update_cc_mode_leds(self):
        """
        Update pad LEDs for CC mode based on latch states.
        """
        for idx in range(16):
            if self.cc_pad_latched[idx]:
                set_pixel_color_cc(idx)
            else:
                clear_pixel(idx)

    def update_nc_mode_leds(self):
        """
        Update pad LEDs for N+C mode based on latch states.
        """
        for idx in range(16):
            if self.nc_pad_latched[idx]:
                set_pad_pixel_color_nc(idx)
            else:
                clear_pixel(idx)

    def set_currently_displaying_velocity(self, value):
        """
        Set the currently_displaying_velocity attribute.

        Args:
            value (bool): The value to set.
        """
        self.currently_displaying_velocity = value
    
    def refresh_display(self):
        """
        Update the display to show the current mode.
        """
        self.set_currently_displaying_velocity(False)
        if self.mode == 'CC':
            self.update_cc_mode_leds()
        elif self.mode == 'Note':
            self.update_note_mode_leds()
        elif self.mode == 'N+C':
            self.update_nc_mode_leds()