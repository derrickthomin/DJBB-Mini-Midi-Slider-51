import neopixel
import board
import time

# Helper variables for special functions
BANK_DOWN_IDX = 14
BANK_UP_IDX = 15

# Create a NeoPixel object
pixels = neopixel.NeoPixel(board.GP3, 16, brightness=0.1)

# Constants for colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK = (255, 105, 180)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
LIGHT_PURPLE = (221, 160, 221)
CYAN = (0, 255, 255)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GREEN = (144, 238, 144)
LIGHT_YELLOW = (255, 255, 224)
LIGHT_ORANGE = (255, 204, 153)

COLORS = [RED, GREEN, BLUE, WHITE,
          PINK, YELLOW, CYAN,
          PURPLE, ORANGE, LIGHT_BLUE,
          LIGHT_GREEN, LIGHT_YELLOW,
          LIGHT_PURPLE, LIGHT_ORANGE]

selected_color_idx = 2

# Track colors if user wants to change them per pixel
cc_colors = [BLUE, BLUE, BLUE, BLUE,
             BLUE, BLUE, BLUE, BLUE,
             BLUE, BLUE, BLUE, BLUE,
             BLUE, BLUE, BLUE, BLUE]

pixels_mapped = [15, 14, 13, 12,
                 8, 9, 10, 11,
                 7, 6, 5, 4,
                 0, 1, 2, 3]

# Function to turn off all pixels
def clear_pixels():
    """
    Clears all the pixels on the display by setting them to the color BLACK.
    """
    for pixel in pixels_mapped:
        pixels[pixel] = BLACK

# Function to get the pixel for a button index
def get_pixel(index):
    """
    Retrieves the pixel value at the specified index.

    Args:
        index (int): The index of the pixel to retrieve.

    Returns:
        The pixel value at the specified index.
    """
    return pixels_mapped[index]

# Function to draw a letter 'C' on the pixels with a specified color
def draw_C(color=BLUE):
    i = 0
    while i < 2:
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

        if color != BLACK:
            time.sleep(0.2)
            color = BLACK
        i += 1

def draw_HI(color=BLUE):
    """
    Draws the letters 'HI' on the display using the specified color.

    Args:
        color (tuple, optional): The RGB color value to use for drawing the letters 'HI'. Defaults to BLUE.

    Returns:
        None
    """
    clear_pixels()

    pixels[0] = color
    pixels[7] = color
    pixels[8] = color
    pixels[15] = color
    pixels[2] = color
    pixels[5] = color
    pixels[10] = color
    pixels[13] = color
    pixels[6] = color

    time.sleep(0.5)

    for i in range(16):
        pixels[i] = BLACK

    pixels[1] = LIGHT_PURPLE
    pixels[2] = LIGHT_PURPLE
    pixels[3] = LIGHT_PURPLE
    pixels[5] = LIGHT_PURPLE
    pixels[10] = LIGHT_PURPLE
    pixels[14] = LIGHT_PURPLE
    pixels[13] = LIGHT_PURPLE
    pixels[12] = LIGHT_PURPLE

    time.sleep(0.5)
    clear_pixels()


# Function to draw a letter 'N' on the pixels with a specified color
def draw_N(color=ORANGE):
    clear_pixels()
    i = 0
    while i < 2:
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

        if color != BLACK:
            time.sleep(0.2)
            color = BLACK

        i += 1

# Function to light up the pixel associated with the MIDI bank up button
def display_midi_bank_up():
    """
    Displays the MIDI bank up action on the pixels.

    This function sets the color of the pixel corresponding to the bank up action to green.

    Parameters:
    None

    Returns:
    None
    """
    pixels[get_pixel(BANK_UP_IDX)] = GREEN

def display_midi_bank_down():
    """
    Displays the MIDI bank down indicator on the display.
    """
    pixels[get_pixel(BANK_DOWN_IDX)] = RED

def blink_next_color():
    """
    Displays the next color in the COLORS array on the display.

    This function sets the color of the pixel corresponding to the next color in the COLORS array.

    Parameters:
    None

    Returns:
    None
    """
    global selected_color_idx
    selected_color_idx += 1
    if selected_color_idx >= len(COLORS):
        selected_color_idx = 0
    pixels[get_pixel(BANK_UP_IDX)] = COLORS[selected_color_idx]
    pixels[get_pixel(BANK_DOWN_IDX)] = COLORS[selected_color_idx]
    
    time.sleep(0.2)

    pixels[get_pixel(BANK_UP_IDX)] = BLACK
    pixels[get_pixel(BANK_DOWN_IDX)] = BLACK

def blink_prev_color():
    """
    Displays the previous color in the COLORS array on the display.

    This function sets the color of the pixel corresponding to the previous color in the COLORS array.

    Parameters:
    None

    Returns:
    None
    """
    global selected_color_idx

    selected_color_idx -= 1
    if selected_color_idx < 0:
        selected_color_idx = len(COLORS) - 1

    pixels[get_pixel(BANK_UP_IDX)] = COLORS[selected_color_idx]
    pixels[get_pixel(BANK_DOWN_IDX)] = COLORS[selected_color_idx]

    time.sleep(0.2)

    pixels[get_pixel(BANK_UP_IDX)] = BLACK
    pixels[get_pixel(BANK_DOWN_IDX)] = BLACK

def set_pixel_color_cc(idx, refresh=False):
    """
    Sets the color of a pixel at the given index to blue.

    Parameters:
    - idx (int): The index of the pixel to set the color for.

    Returns:
    None
    """
    global cc_colors

    # Refresh = show us what we had before
    if refresh:
        pixels[get_pixel(idx)] = cc_colors[idx]
    
    # Otherwise set to the currently selected color
    else:
        color = COLORS[selected_color_idx]
        cc_colors[idx] = color
        pixels[get_pixel(idx)] = color

def set_pixel_color_note(idx):
    """
    Sets the color of a pixel based on the given index.

    Parameters:
    idx (int): The index of the pixel.

    Returns:
    None
    """
    pixels[get_pixel(idx)] = ORANGE

def clear_pixel(idx):
    """
    Clears the pixel at the specified index.

    Parameters:
    idx (int): The index of the pixel to be cleared.

    Returns:
    None
    """
    pixels[get_pixel(idx)] = BLACK

# Call when switching back to cc mode to light up the right pixels
def update_cc_pixels(latch_ary):
    """
    Updates the pixels on the display based on the given latch array.

    Parameters:
    - latch_ary (list): A list of latch values indicating whether each pixel should be set or cleared.

    Returns:
    - None
    """
    for idx, latch in enumerate(latch_ary):
        if latch:
            set_pixel_color_cc(idx, refresh=True)
        else:
            clear_pixel(idx)

