import board
import analogio

# Constants
SLIDE_POT_CHANGE_THRESHOLD = 1000
SLIDE_CHECK_COUNTER = 0
ANY_SLIDE_CHANGED = False
slide_values_changed = [False, False, False]
current_slide_pots_midi = [0, 0, 0]
midi_val_chg_status = [False, False, False]  # Check this to only send new vals when changed

# Set up slide potentiometers
slide_potentiometers = [
    analogio.AnalogIn(board.GP26),
    analogio.AnalogIn(board.GP27),
    analogio.AnalogIn(board.GP28)
]

slide_values = [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]  # Track 6 for averaging. last always most recent

# Translate slide potentiometer value to MIDI value
def slide_pot_to_midi(slide_value):
    """
    Convert slide potentiometer value to MIDI value.
    """
    return int((slide_value / 65535) * 127)


def update():
    """
    Update slide potentiometers.
    """
    global ANY_SLIDE_CHANGED
    global slide_values_changed
    global current_slide_pots_midi
    global midi_val_chg_status

    # Update pots
    ANY_SLIDE_CHANGED = False
    slide_values_changed = [False, False, False]
    for idx, slide in enumerate(slide_potentiometers):
        current_val = 65535 - slide.value
        slide_values[idx].append(current_val)

        # Compare the average of the most recent value plus the previous two values to the first 3 values in the list
        average = sum(slide_values[idx][-3:]) / 3
        prev_avg = sum(slide_values[idx][:3]) / 3

        midi_val_chg_status[idx] = False
        if abs(average - prev_avg) > SLIDE_POT_CHANGE_THRESHOLD:
            slide_values_changed[idx] = True
            ANY_SLIDE_CHANGED = True
            cur_midi = slide_pot_to_midi(average)
            if cur_midi == current_slide_pots_midi[idx]:
                midi_val_chg_status[idx] = False
            else:
                print(f"prev: {current_slide_pots_midi[idx]} new: {cur_midi}")
                current_slide_pots_midi[idx] = cur_midi
                midi_val_chg_status[idx] = True

        if len(slide_values[idx]) > 7:
            slide_values[idx].pop(0)

    return ANY_SLIDE_CHANGED





    