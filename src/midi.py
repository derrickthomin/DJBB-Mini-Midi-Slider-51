import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
import usb_midi
from settings import load_midi_channel_from_file

# Create a MIDI object
channel = load_midi_channel_from_file()
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=channel)

# Set up MIDI banks
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
MIDI_BANK_IDX = 3
current_midi_notes = current_midibank_set[MIDI_BANK_IDX]

def send_midi_note_on(index, velocity=100):
    """
    Sends a MIDI note on message.

    Args:
        index (int): The index of the note.
        velocity (int, optional): The velocity of the note. Defaults to 100.
    """
    note = current_midi_notes[index]
    midi.send(NoteOn(note, velocity))
    print(f"Sending note {note} at index {index} with velocity {velocity}")

def send_midi_note_off(index):
    """
    Sends a MIDI note off message for the note at the specified index.

    Args:
        index (int): The index of the note in the `current_midi_notes` list.
    """
    note = current_midi_notes[index]
    midi.send(NoteOff(note, 1))

def clear_all_notes():
    """
    Sends a NoteOff message for all MIDI notes (0-127) to turn off any currently playing notes.
    """
    for i in range(127):
        midi.send(NoteOff(i, 1))

def change_midi_bank(up_or_down=True):
    """
    Change the MIDI bank index and update the current MIDI notes.

    Args:
        up_or_down (bool, optional): Determines whether to move the MIDI bank index up or down. 
            Defaults to True, which moves the index up.
    """
    global MIDI_BANK_IDX
    global current_midi_notes

    if up_or_down and MIDI_BANK_IDX < (len(current_midibank_set) - 1):
        clear_all_notes()
        MIDI_BANK_IDX += 1

    if not up_or_down and MIDI_BANK_IDX > 0:
        clear_all_notes()
        MIDI_BANK_IDX -= 1

    current_midi_notes = current_midibank_set[MIDI_BANK_IDX]

def send_control_change(control_change, value):
    """
    Sends a control change message with the specified control change number (cc) and value.

    Args:
        control_change (int): The control change number.
        value (int): The value to set for the control change.
    """
    print(f"Sending CC {control_change} with value {value}")
    midi.send(ControlChange(control_change, value))
