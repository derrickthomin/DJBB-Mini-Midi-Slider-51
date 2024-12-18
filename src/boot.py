import storage
import board
import digitalio

# Set up the button
FN_BTN_PIN = board.GP1
fn_button_io = digitalio.DigitalInOut(FN_BTN_PIN)
fn_button_io.direction = digitalio.Direction.INPUT
fn_button_io.pull = digitalio.Pull.UP

# Check if the button is held down at startup
if not fn_button_io.value:
    # Button is held, enable USB drive mode
    print("Booting into USB drive mode")
    storage.remount("/", readonly=False)
    storage.enable_usb_drive()
else:
    # Button is not held, disable USB drive mode
    storage.remount("/", readonly=True)
    storage.disable_usb_drive()

# Set the label for the storage
M = storage.getmount("/")
M.label = "midislider"