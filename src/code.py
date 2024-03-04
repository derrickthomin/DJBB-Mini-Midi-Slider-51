import adafruit_midi
import board
import neopixel
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
import usb_midi
import time
import digitalio
from adafruit_debouncer import Debouncer, Button

# Create a MIDI object
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1)

# Create a NeoPixel object
pixels = neopixel.NeoPixel(board.GP3, 16, brightness=0.1)

# Button Pins Setup
FN_BTN_PIN = board.GP1
fn_button = digitalio.DigitalInOut(FN_BTN_PIN)
fn_button.direction = digitalio.Direction.INPUT
fn_button.pull = digitalio.Pull.UP
fn_button = Button(fn_button)

DRUMPAD_BTN_PINS = [board.GP4, board.GP0, board.GP2, board.GP5,
                    board.GP21, board.GP9, board.GP6, board.GP7, 
                    board.GP19, board.GP18, board.GP12, board.GP13, 
                    board.GP17, board.GP16, board.GP15, board.GP14]

drumpad_buttons = []

for pin in DRUMPAD_BTN_PINS:
    button = digitalio.DigitalInOut(pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    drumpad_buttons.append(Button(button))

# Helpers variables for special functions
BANK_DOWN_IDX = 2
BANK_UP_IDX = 3


# Set up midi banks
MIDI_BANKS_CHROMATIC = [[0 + i for i in range(16)],
            [4 + i for i in range(16)],
            [20 + i for i in range(16)],
            [36 + i for i in range(16)],
            [52 + i for i in range(16)],
            [68 + i for i in range(16)],
            [84 + i for i in range(16)],
            [100 + i for i in range(16)],
            [111 + i for i in range(16)]
            ]
current_midibank_set = MIDI_BANKS_CHROMATIC
midi_bank_idx = 3
current_midi_notes = current_midibank_set[midi_bank_idx]

cc_only_mode = False   # If True, only CC messages will be sent. No notes.
CC_BANK = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,12,13,14,15]  # CC messages for the buttons

# Color Constants
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK = (255, 105, 180)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GREEN = (144, 238, 144)
LIGHT_YELLOW = (255, 255, 224)
LIGHT_PURPLE = (221, 160, 221)
LIGHT_ORANGE = (255, 160, 122)

# Map pixels to buttons
pixels_mapped = [0,1,2,3,
                7,6,5,4,
                8,9,10,11,
                15,14,13,12]

# 1. NEOPIXEL FUNCTIONS

# Turn off all pixels
for pixel in pixels_mapped:
    pixel = BLACK

# Function to get the pixel for a button indes
def get_pixel(index):
    return pixels_mapped[index]


# 2. MIDI FUNCTIONS
def send_midi_note_on(note):
    midi.send(NoteOn(note, 120))

def send_midi_note_off(note):
    midi.send(NoteOff(note, 1))

def clear_all_notes():
    for i in range(127):
        send_midi_note_off(i)

def chg_midi_bank(upOrDown = True):
    global midi_bank_idx
    global current_midi_notes

    if upOrDown is True and midi_bank_idx < (len(current_midibank_set) - 1):
        clear_all_notes()
        midi_bank_idx = midi_bank_idx + 1

    if upOrDown is False and midi_bank_idx > 0:
        clear_all_notes()
        midi_bank_idx = midi_bank_idx - 1

    current_midi_notes = current_midibank_set[midi_bank_idx] 
    return

def draw_C(color=BLUE):
    pixels[0] = color
    pixels[1] = color
    pixels[2] = color
    pixels[3] = color
    pixels[7] = color
    pixels[8] = color
    pixels[15] = color
    pixels[14] = color
    pixels[13] = color
    pixels[12] = color

def draw_N(color=ORANGE):
    pixels[0] = color
    pixels[3] = color
    pixels[4] = color
    pixels[6] = color
    pixels[7] = color
    pixels[8] = color
    pixels[10] = color
    pixels[12] = color
    pixels[11] = color
    pixels[15] = color

def toggle_cc_only_mode():
    global cc_only_mode

    cc_only_mode = not cc_only_mode
    clear_all_notes()

    return

while True:
    fn_button.update()
    if fn_button.fell:
        print("FN Button Pressed")

    if fn_button.rose:
        print("FN Button Released")
    
    if fn_button.short_count > 1:
        print("FN btn Dble Click")
        toggle_cc_only_mode()
        if cc_only_mode:
            draw_C()
            time.sleep(0.5)
            draw_C(BLACK)
        else:
            draw_N()
            time.sleep(0.5)
            draw_N(BLACK)

    for idx, button in enumerate(drumpad_buttons):
        button.update()

        # New Button Press
        if button.fell:
            if idx == BANK_DOWN_IDX and fn_button.value is False:
                chg_midi_bank(False)
                pixels[get_pixel(idx)] = RED
                print("Bank Down")
            elif idx == BANK_UP_IDX and fn_button.value is False:
                chg_midi_bank(True)
                pixels[get_pixel(idx)] = GREEN
                print("Bank Up")
            else:
                if cc_only_mode:
                    print(idx)
                    midi.send(ControlChange(CC_BANK[idx], 127))
                    pixels[get_pixel(idx)] = BLUE
                else:
                    send_midi_note_on(current_midi_notes[idx])
                    pixels[get_pixel(idx)] = ORANGE

        # New Button Release
        if button.rose:
            if cc_only_mode:
                midi.send(ControlChange(CC_BANK[idx], 0))
            else:
                send_midi_note_off(current_midi_notes[idx])
            pixels[get_pixel(idx)] = BLACK
    
    time.sleep(0.01)




    