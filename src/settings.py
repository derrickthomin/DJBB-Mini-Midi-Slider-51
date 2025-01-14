"""
Settings Module

This module contains configurable constants, default values, and utility functions
used across the MIDI controller project. It centralizes settings for easy adjustments
and ensures consistency throughout the codebase.

Provides:
- Constants for timing intervals, thresholds, and default MIDI values.
- Functions to load CC values and MIDI channel from a JSON configuration file.
- Debug printing utility.
"""

import json

# Debugging
DEBUG = False

def debug_print(message):
    """
    Prints a debug message if debugging is enabled.

    Args:
        message (str): The message to print.
    """
    if DEBUG:
        print(message)

# Filepath for configuration
CONFIG_FILEPATH = 'cc_vals.json'

# Timing Constants
DOUBLE_PRESS_INTERVAL = 0.3   # Seconds between clicks to detect a double press
HOLD_THRESHOLD = 0.5          # Seconds to detect a hold event

# Default MIDI CC Values for Sliders
DEFAULT_SLIDE_CC_VALS = [3, 9, 85]  # Global CC numbers for sliders

# Default CC Values for Sliders when Pads are Held or Latched
# Each sublist corresponds to one of the 16 pads.
DEFAULT_SLIDE_CC_VALS_HELD = [
    [10, 11, 12], [13, 14, 15], [16, 17, 18], [19, 20, 21],
    [22, 23, 24], [25, 26, 27], [28, 29, 30], [31, 32, 33],
    [34, 35, 36], [37, 38, 39], [40, 41, 42], [43, 44, 45],
    [46, 47, 48], [49, 50, 51], [52, 53, 54], [55, 56, 57]
]

# Default MIDI Channel
DEFAULT_MIDI_CHANNEL = 1  # MIDI channels range from 1 to 16

def load_cc_vals_from_file():
    """
    Load CC values for sliders from the configuration file.

    Returns:
        tuple: A tuple containing two lists:
            - slide_cc_vals (list): Global CC numbers for sliders.
            - slide_cc_vals_held (list): CC numbers per pad per slider when pads are held or latched.
    """
    try:
        with open(CONFIG_FILEPATH, 'r') as f:
            all_cc_vals = json.load(f)
            slide_cc_vals = all_cc_vals.get('SLIDER_CC_VALS_GLOBAL', DEFAULT_SLIDE_CC_VALS)
            slide_cc_vals_held = all_cc_vals.get('SLIDER_CC_VALS_HELD', DEFAULT_SLIDE_CC_VALS_HELD)
            debug_print(f"Loaded CC values from file: {slide_cc_vals}")
            debug_print(f"Loaded CC values held from file: {slide_cc_vals_held}")
        return (slide_cc_vals, slide_cc_vals_held)
    except FileNotFoundError:
        debug_print(f"Configuration file '{CONFIG_FILEPATH}' not found. Using default CC values.")
        return (DEFAULT_SLIDE_CC_VALS, DEFAULT_SLIDE_CC_VALS_HELD)

def load_midi_channel_from_file():
    """
    Load the MIDI channel from the configuration file.

    Returns:
        int: The MIDI channel (0-15, where 0 corresponds to MIDI Channel 1).
    """
    try:
        with open(CONFIG_FILEPATH, 'r') as f:
            all_data = json.load(f)
            midi_channel = all_data.get('MIDI_CHANNEL', DEFAULT_MIDI_CHANNEL)
            # Adjust MIDI channel to be zero-based index
            midi_channel = max(1, min(16, midi_channel)) - 1
            debug_print(f"Loaded MIDI channel from file: {midi_channel + 1}")
        return midi_channel
    except FileNotFoundError:
        debug_print(f"Configuration file '{CONFIG_FILEPATH}' not found. Using default MIDI channel.")
        return DEFAULT_MIDI_CHANNEL - 1  # Zero-based index

# Example usage of loading configurations
# This will be used in midi.py or where the MIDI channel is needed
MIDI_CHANNEL = load_midi_channel_from_file()
all_cc_vals = load_cc_vals_from_file()
slide_cc_vals = all_cc_vals[0]
slide_cc_vals_held = all_cc_vals[1]