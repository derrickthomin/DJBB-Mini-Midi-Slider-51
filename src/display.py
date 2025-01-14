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

previous_velocity_step = 0

# What it looks like visually. 15 is bottom left, 3 is top right.

#                          0  1  2  3
#                          7  6  5  4
#                          8  9  10 11
#                          15 14 13 12    

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

def calculate_brightness(step):
    """
    Calculates the brightness level for a given step (1-16).
    Brightness ranges from low to high.

    Args:
        step (int): The step number (1-16).

    Returns:
        float: Brightness value between 0.1 and 1.0.
    """
    brightness = 0.1 + ((step - 1) / 15) * 0.9  # Scale brightness from 0.1 to 1.0
    return max(0.1, min(brightness, 1.0))

def scale_color(color, brightness):
    """
    Scales the color by the given brightness.

    Args:
        color (tuple): Original RGB color tuple (0-255).
        brightness (float): Brightness factor (0.1 to 1.0).

    Returns:
        tuple: Scaled RGB color tuple.
    """
    r = int(color[0] * brightness)
    g = int(color[1] * brightness)
    b = int(color[2] * brightness)
    return (r, g, b)

def display_velocity(velocity_value, is_currently_displaying_velocity=True, color=WHITE):
    """
    Displays the velocity on the NeoPixel grid by lighting up pixels in steps.
    Updates only when the velocity crosses into a new step.

    Args:
        velocity_value (int): MIDI velocity value (0-127).
        color (tuple, optional): Base RGB color for the pixels. Defaults to WHITE.
        is_currently_displaying_velocity (bool): Flag to indicate if velocity is currently being displayed.

    Returns:
        None
    """
    # Define velocity thresholds for each of the 16 steps
    velocity_thresholds = [int((127 * i) / 16) for i in range(1, 17)]  # 16 thresholds

    # Determine the current step based on velocity
    step = 16  # Default to maximum step
    for i, threshold in enumerate(velocity_thresholds):
        if velocity_value <= threshold:
            step = i + 1
            break

    global previous_velocity_step

    if step == previous_velocity_step and is_currently_displaying_velocity:
        # No change in step and currently displaying velocity; do not update display
        return

    # Define the lighting order from bottom left to top right
    light_order = [15, 14, 13, 12,
                   8, 9, 10, 11,
                   7, 6, 5, 4,
                   0, 1, 2, 3]
    
    if not is_currently_displaying_velocity:
        for idx in range(0, step):
            brightness = calculate_brightness(idx + 1)
            scaled_color = scale_color(color, brightness)
            pixels[light_order[idx]] = scaled_color

    if step > previous_velocity_step:
        # Light up the next pixel(s)
        for idx in range(previous_velocity_step, step):
            brightness = calculate_brightness(step)
            scaled_color = scale_color(color, brightness)
            pixels[light_order[idx]] = scaled_color
    else:
        # Turn off the previous pixel(s)
        for idx in range(step, previous_velocity_step):
            pixels[light_order[idx]] = BLACK

    previous_velocity_step = step  # Update the stored step
    pixels.show()
# Function to draw a letter 'C' on the pixels with a specified color
def draw_C(color=BLUE, sleeptime=0.2):
    """
    Draws the letter 'C' on an LED matrix using the specified color.

    Args:
        color (tuple): The color to use for drawing the 'C'. Default is BLUE.
        sleeptime (float): The time to wait before toggling the color to BLACK. Default is 0.2 seconds.

    The function lights up specific pixels to form the shape of the letter 'C' on an LED matrix.
    It toggles the color between the specified color and BLACK with a delay specified by sleeptime.
    """
    clear_pixels()
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
            time.sleep(sleeptime)
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
def draw_N(color=ORANGE, sleeptime=0.2):
    """
    Draws the letter 'N' on a pixel display with the specified color and sleep time.

    Args:
        color (tuple): The color to draw the letter 'N'. Default is ORANGE.
        sleeptime (float): The time to sleep between color changes. Default is 0.2 seconds.

    The function lights up specific pixels to form the letter 'N' and alternates the color with BLACK after a specified sleep time.
    """
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
            time.sleep(sleeptime)
            color = BLACK

        i += 1

def draw_NC(color=CYAN):
    """
    Draws a pattern representing the N+C mode on the display.

    This function first clears the pixels, then draws the pattern for 'N' 
    with a specified sleep time, clears the pixels again, and finally 
    draws the pattern for 'C' with the same sleep time. Additionally, 
    it lights up all corners of the display with the specified color.

    Args:
        color (tuple): The color to use for lighting up the corners. 
                       Defaults to CYAN.
    """

    clear_pixels()
    draw_N(sleeptime=0.15)
    clear_pixels()

    # Draw Slash
    pixels[15] = color
    pixels[9] = color
    pixels[5] = color
    pixels[3] = color

    pixels.show()
    time.sleep(0.15)
    clear_pixels()
    draw_C(sleeptime=0.15)
    
def draw_lock_icon(color=RED):
    """
    Draws the letter 'L' on the NeoPixel grid using the specified color.

    The 'L' consists of:
    - The entire left-hand column lit up (pixels 15, 8, 7, 0).
    - The bottom row lit up starting from the left (pixels 0, 1, 2).

    Args:
        color (tuple, optional): The RGB color value to use for drawing the letter 'L'.
                                  Defaults to ORANGE.

    Returns:
        None
    """
    clear_pixels()

    for j in (8,9,10,15,14,13): # body of lock
        pixels[j] = color

    sleep_time = 0
    for j in (7,0,1,2,5): # animate locking
        sleep_time = sleep_time + 0.015
        time.sleep(sleep_time)
        pixels[j] = color
    
    time.sleep(0.25)
    clear_pixels()


def draw_unlock_icon(color=GREEN):
    """
    Draws the letter 'K' on the NeoPixel grid using the specified color.

    The 'K' consists of:
    - The entire second column lit up (pixels 14, 9, 6, 1).
    - Pixels to form the upper and lower diagonals:
        - Upper diagonal: pixels 5
        - Lower diagonal: pixels 4

    Args:
        color (tuple, optional): The RGB color value to use for drawing the letter 'K'.
                                  Defaults to GREEN.

    Returns:
        None
    """
    clear_pixels()
    for j in range(16):
        if j in (6, 12, 11, 4, 3):
            continue
        pixels[j] = color
    
    sleep_time = 0
    for j in (5,2,1,0,7): # animate unlocking
        sleep_time = sleep_time + 0.015
        time.sleep(sleep_time)
        pixels[j] = BLACK

        # if color != BLACK:
        #     #time.sleep(4)
        #     color = BLACK  # Turn off the pixels after a short delay
    time.sleep(0.25)
    clear_pixels()


def display_bank_number(number, color=WHITE):
    """
    Lights up the specified number of pixels on the NeoPixel grid,
    starting from the bottom left (pixel 0).

    Args:
        number (int): Number of pixels to light up (0-15).
                      - If 0 is passed, light up the first pixel (pixel 0).
                      - If 1 is passed, light up pixels 0 and 1.
                      - ...
                      - If 15 is passed, light up all 16 pixels.
        color (tuple): RGB color to light the pixels with. Defaults to WHITE.

    Returns:
        None
    """
    clear_pixels()

    # Define the lighting order starting from pixel 0 (bottom left)
    light_order = [3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12]

    # Determine the number of pixels to light up
    # If number is 0, light up 1 pixel (pixel 0)
    num_pixels = number + 1 if number < len(light_order) else len(light_order)

    # Ensure num_pixels does not exceed the grid
    num_pixels = min(num_pixels, len(light_order))

    # Get the list of pixels to light up
    pixels_to_light = light_order[:num_pixels]

    # Light up the specified pixels
    for px in pixels_to_light:
        try:
            mapped_idx = pixels_mapped.index(px)
            pixels[mapped_idx] = color
        except ValueError:
            # If the pixel is not found in pixels_mapped, skip it
            continue

    # Optional: Adjust the sleep duration as needed
    time.sleep(0.1)

    # Clear the pixels after displaying the number
    clear_pixels()

# Function to light up the pixel associated with the MIDI bank up button
def display_midi_bank_up(bank_number):
    """
    Displays the MIDI bank up action on the pixels by showing the bank number.

    This function sets the color of the pixels to display the specified bank number in green.

    Args:
        bank_number (int): The bank number to display.

    Returns:
        None
    """
    display_bank_number(bank_number, GREEN)

def display_midi_bank_down(bank_number):
    """
    Displays the MIDI bank down indicator on the display by showing the bank number.

    This function sets the color of the pixels to display the specified bank number in red.

    Args:
        bank_number (int): The bank number to display.

    Returns:
        None
    """
    display_bank_number(bank_number, RED)

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

def set_pad_pixel_color_nc(idx):
    """
    Sets the color of a specific pad pixel to cyan.

    Args:
        idx (int): The index of the pad pixel to be colored.
    """
    pixels[get_pixel(idx)] = CYAN

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

def update_pad_led(mode, idx, active):
    """
    Updates the LED for a pad based on the mode and active state.

    Args:
        mode (str): Current mode ('Note', 'CC', 'N+C').
        idx (int): Index of the pad.
        active (bool): True to turn on the LED, False to turn it off.
    """
    if mode == 'Note':
        pixel_color = ORANGE
    elif mode == 'CC':
        pixel_color = COLORS[selected_color_idx]
    elif mode == 'N+C':
        pixel_color = CYAN
    else:
        pixel_color = BLACK

    if active:
        pixels[get_pixel(idx)] = pixel_color
    else:
        clear_pixel(idx)

