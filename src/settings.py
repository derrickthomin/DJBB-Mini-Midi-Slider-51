import json

debug = True
FILEPATH = 'cc_vals.json'

default_slide_cc_vals = [3, 9, 85]

# Array of arrays of slide potentiometer values to be used when each of the 16 buttons are held down.
# Each inner array contains the CC values for the 3 slide potentiometers, starting at value 10.
default_slide_cc_vals_held = [
    [10, 11, 12], [13, 14, 15], [16, 17, 18], [19, 20, 21],
    [22, 23, 24], [25, 26, 27], [28, 29, 30], [31, 32, 33],
    [34, 35, 36], [37, 38, 39], [40, 41, 42], [43, 44, 45],
    [46, 47, 48], [49, 50, 51], [52, 53, 54], [55, 56, 57]
]

def debug_print(message):
    if debug:
        print(message)

def load_cc_vals_from_file():
    # Returns a tuple of the slide_cc_vals and slide_cc_vals_held dictionaries

    try:
        with open(FILEPATH, 'r') as f:
            all_cc_vals = json.load(f)
            slide_cc_vals = all_cc_vals['SLIDER_CC_VALS_GLOBAL']
            cc_vals_held = all_cc_vals['SLIDER_CC_VALS_HELD']

            debug_print(f"Loaded CC values from file: {slide_cc_vals}")
            debug_print(f"Loaded CC values held from file: {cc_vals_held}")

            return (slide_cc_vals, cc_vals_held)

    except FileNotFoundError:
        return (default_slide_cc_vals, default_slide_cc_vals_held)