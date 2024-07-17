import board
import time
from adafruit_debouncer import Button
from midi import send_midi_note_on, send_midi_note_off, clear_all_notes, change_midi_bank, send_control_change
import sliders

from display import (
    display_midi_bank_down, display_midi_bank_up,
    BANK_DOWN_IDX, BANK_UP_IDX, draw_c, draw_n,
    set_pixel_color_cc, set_pixel_color_note, clear_pixel,
    update_cc_pixels, draw_hi, blink_next_color, blink_prev_color
)
from settings import debug_print
import digitalio

# Button Pins Setup
FN_BTN_PIN = board.GP1
fn_button = digitalio.DigitalInOut(FN_BTN_PIN)
fn_button.direction = digitalio.Direction.INPUT
fn_button.pull = digitalio.Pull.UP
fn_button = Button(fn_button)

DRUMPAD_BTN_PINS = [
    board.GP17, board.GP16, board.GP15, board.GP14,
    board.GP19, board.GP18, board.GP12, board.GP13,
    board.GP21, board.GP9, board.GP6, board.GP7,
    board.GP4, board.GP0, board.GP2, board.GP5
]

# Used in cc only mode. If a button is latched, the slide pot values will be used to send CC messages
LATCH_COUNT = 0  # how many buttons are latched
btn_latched = [
    False, False, False, False,
    False, False, False, False,
    False, False, False, False,
    False, False, False, False
]

drumpad_buttons = []

for pin in DRUMPAD_BTN_PINS:
    button = digitalio.DigitalInOut(pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    drumpad_buttons.append(Button(button))

slide_cc_vals = [3, 9, 85]

# Array of arrays of slide potentiometer values to be used when each of the 16 buttons are held down.
# Each inner array contains the CC values for the 3 slide potentiometers, starting at value 10.
slide_cc_vals_held = [
    [10, 11, 12], [13, 14, 15], [16, 17, 18], [19, 20, 21],
    [22, 23, 24], [25, 26, 27], [28, 29, 30], [31, 32, 33],
    [34, 35, 36], [37, 38, 39], [40, 41, 42], [43, 44, 45],
    [46, 47, 48], [49, 50, 51], [52, 53, 54], [55, 56, 57]
]

# Track latched state for cc mode
button_held_note_mode = [
    False, False, False, False,
    False, False, False, False,
    False, False, False, False,
    False, False, False, False
]

CC_ONLY_MODE = False   # If True, only CC messages will be sent. No notes.


def toggle_cc_only_mode():
    """
    Toggles the CC Only mode.

    This function toggles the global variable `CC_ONLY_MODE` between True and False.
    When `CC_ONLY_MODE` is True, it performs certain actions such as clearing all notes,
    clearing pixels, and drawing the letter 'C'. When `CC_ONLY_MODE` is False, it resets
    the `button_held_note_mode` list, clears pixels, and draws the letter 'N'.

    Returns:
        None
    """
    global CC_ONLY_MODE

    CC_ONLY_MODE = not CC_ONLY_MODE
    if CC_ONLY_MODE:
        clear_all_notes()             # dont leave any notes hanging
        draw_c()

        for i in range(16):           # Reset latches
            button_held_note_mode[i] = btn_latched[i]

        update_cc_pixels(btn_latched) # Redraw latched pixels
    else:
        for idx in range(16):
            button_held_note_mode[idx] = False
        draw_n()


draw_hi()  # Splash screen

while True:
    fn_button.update()
    if fn_button.fell:
        print("FN Button Pressed")

    if fn_button.rose:
        print("FN Button Released")

    # Display mode change if double click
    if fn_button.short_count > 1:
        print("FN btn Dble Click")
        toggle_cc_only_mode()

    any_slide_changed = sliders.update()
    any_button_held = False

    # ------- Button Loop -------
    for idx, button in enumerate(drumpad_buttons):
        button.update()

        # ------- New Button Press -------
        if button.fell:

            # -- CC mode --

            if CC_ONLY_MODE:

                # Next Color
                if idx == BANK_DOWN_IDX and fn_button.value is False:
                    blink_next_color()
                    continue

                # Prev color
                if idx == BANK_UP_IDX and fn_button.value is False:
                    blink_prev_color()
                    continue

                btn_latched[idx] = not btn_latched[idx]

                if btn_latched[idx]:
                    print(f"Button {idx} latched")
                    LATCH_COUNT += 1
                    button_held_note_mode[idx] = True
                    set_pixel_color_cc(idx)
                else:
                    print(f"Button {idx} unlatched")
                    LATCH_COUNT -= 1
                    button_held_note_mode[idx] = False
                    clear_pixel(idx)

            # -- Note mode --

            else:

                # Change MIDI Bank down
                if idx == BANK_DOWN_IDX and fn_button.value is False:
                    change_midi_bank(False)
                    display_midi_bank_down()
                    print("Bank Down")
                    continue

                # Change MIDI Bank up
                if idx == BANK_UP_IDX and fn_button.value is False:
                    change_midi_bank(True)
                    display_midi_bank_up()
                    print("Bank Up")
                    continue

                send_midi_note_on(idx)
                set_pixel_color_note(idx)

        # New Button Release
        if button.rose:
            if CC_ONLY_MODE:
                # send_pad_control_change(idx, 0)
                pass
            else:
                send_midi_note_off(idx)
                button_held_note_mode[idx] = False
                clear_pixel(idx)

        # Special function if button is held down
        if button.long_press:
            button_held_note_mode[idx] = True
            set_pixel_color_cc(idx, True)

        # If any button is held down, we will override the global slide pot cc vals with the button modified one(s)
        if button_held_note_mode[idx] and not CC_ONLY_MODE:
            any_button_held = True

        if button_held_note_mode[idx] and any_slide_changed:
            for i in range(3):
                if sliders.midi_val_chg_status[i]:
                    send_control_change(slide_cc_vals_held[idx][i], sliders.current_slide_pots_midi[i])

    # No slides to change, nothiing else to do. next loooooooooop.
    if not any_slide_changed:
        continue

    # If we are here, then at least one slide has changed.
    for idx, slide_chg_status in enumerate(sliders.midi_val_chg_status):

        if not slide_chg_status:
            continue

        debug_print(f"Slide {idx} changed: {slide_chg_status}")
        debug_print(f"latch count: {LATCH_COUNT}")
        debug_print(f"CC_ONLY_MODE: {CC_ONLY_MODE}")
        debug_print(f"any_button_held: {any_button_held}")

        if CC_ONLY_MODE and LATCH_COUNT < 1:  # CC mode. Dont care about holding buttons - latches only.
            send_control_change(slide_cc_vals[idx], sliders.current_slide_pots_midi[idx])
            debug_print("IN CC MODE")

        if not CC_ONLY_MODE and not any_button_held:  # Note mode - make sure no buttons are held down
            send_control_change(slide_cc_vals[idx], sliders.current_slide_pots_midi[idx])
            debug_print("IN NOTE MODE")
