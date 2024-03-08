import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
import usb_midi

# Create a MIDI object
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1)


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

# cc_only_mode = False   # If True, only CC messages will be sent. No notes.
CC_BANK = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,12,13,14,15]  # CC messages for the buttons

def send_midi_note_on(idx,vel=100):
    note = current_midi_notes[idx]
    midi.send(NoteOn(note, vel))

def send_midi_note_off(idx):
    note = current_midi_notes[idx]
    midi.send(NoteOff(note, 1))

def clear_all_notes():
    for i in range(127):
        midi.send(NoteOff(i, 1))

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

def send_control_change(idx, value):
    cc = CC_BANK[idx]
    midi.send(ControlChange(cc, value))
    return