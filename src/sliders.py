# sliders.py

"""
Slider Module

This module handles reading the values from the sliders (slide potentiometers),
applying Exponential Moving Average (EMA) smoothing, converting them to MIDI values,
and detecting significant changes to determine when to send updated MIDI CC messages.

Provides:
- midi_value_changed: List indicating which sliders have changed significantly.
- current_slide_pots_midi: Current MIDI values for the sliders.
- update(): Function to update slider readings and detect changes.

Assumptions:
- Sliders are connected to specified analog pins.
- Hardware setup requires inverting the raw analog readings (max voltage corresponds to min reading).
"""

import board
import analogio
from settings import debug_print

# Constants
SLIDER_CHANGE_THRESHOLD = 2    # Minimum change in MIDI value to trigger an update
EMA_ALPHA = 0.4                # EMA smoothing factor (0 < alpha ≤ 1)
NUM_SLIDERS = 3                # Number of sliders

# Set up slide potentiometers (adjust pins as needed)
SLIDE_POT_PINS = [board.GP26, board.GP27, board.GP28]
slide_potentiometers = [analogio.AnalogIn(pin) for pin in SLIDE_POT_PINS]

# Initialize variables
ema_values = [0.0] * NUM_SLIDERS                 # EMA values for each slider
current_slide_pots_midi = [0] * NUM_SLIDERS      # Current MIDI values for sliders
midi_value_changed = [False] * NUM_SLIDERS       # Flags indicating if MIDI value changed

def reset_changes():
    for i in range(NUM_SLIDERS):
        midi_value_changed[i] = False

def slide_pot_to_midi(slide_value):
    """
    Convert slide potentiometer value (0-65535) to MIDI value (0-127).
    
    Args:
        slide_value (float): The raw or smoothed analog value from the slider.
    
    Returns:
        int: The corresponding MIDI value (0-127).
    """
    # Ensure slide_value is within valid range
    slide_value = max(0, min(65535, slide_value))
    return int((slide_value / 65535) * 127)

def initialize_ema_values():
    """
    Initialize the EMA values with the current slider readings.
    """
    for idx, slide in enumerate(slide_potentiometers):
        raw_value = slide.value
        inverted_value = 65535 - raw_value   # Invert based on hardware setup
        ema_values[idx] = inverted_value     # Initialize EMA to current value

def update():
    """
    Update slide potentiometers using EMA and check for significant MIDI value changes.

    Returns:
        bool: True if any slider has a significant change, False otherwise.
    """
    any_slider_changed = False
    for idx, slide in enumerate(slide_potentiometers):
        # Read current raw value from the slider
        raw_value = slide.value
        inverted_value = 65535 - raw_value   # Invert based on hardware setup

        # Update EMA value
        previous_ema = ema_values[idx]
        ema = EMA_ALPHA * inverted_value + (1 - EMA_ALPHA) * previous_ema
        ema_values[idx] = ema

        # Convert the EMA value to a MIDI value
        midi_value = slide_pot_to_midi(ema)

        # Check if the MIDI value has changed beyond the threshold
        previous_midi_value = current_slide_pots_midi[idx]
        if abs(midi_value - previous_midi_value) >= SLIDER_CHANGE_THRESHOLD:
            # Significant change detected
            current_slide_pots_midi[idx] = midi_value
            midi_value_changed[idx] = True
            any_slider_changed = True
            # Debug print statement (optional)
            debug_print(f"Slider {idx + 1} MIDI value changed from {previous_midi_value} to {midi_value}")
        else:
            midi_value_changed[idx] = False
    return any_slider_changed

# Initialize EMA values on startup
initialize_ema_values()