import shutil
import sys
import time
from distutils.dir_util import copy_tree


# ------ USER SETTINGS ------

NUKE = True             # If true, use nuke.uf2 first

# Update these depending on the device

# Mini Slider
NUKE_FP = "/Users/derrickthomin/Downloads/flash_nuke.uf2"
UF2_FP = "/Users/derrickthomin/Downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-8.1.0.uf2"
SRC_FOLDER_FP = "/Users/derrickthomin/📜Documents Local/📝Project Writeups/Mini Midi Slider/Production/src"

# RGB Loopster
# NUKE_FP = "/Users/derrickthomin/Downloads/flash_nuke.uf2"
# UF2_FP = "/Users/derrickthomin/📜Documents Local/📝Project Writeups/DJBB Midi Loopster SMD RGB/Code - Production/uf2 current/adafruit-circuitpython-raspberry_pi_pico-en_US-8.2.6.uf2"
# SRC_FOLDER_FP = "/Users/derrickthomin/📜Documents Local/📝Project Writeups/DJBB Midi Loopster SMD RGB/Code - Production/src"
# # ---------------------------

RPI_INIT_FP= "/Volumes/RPI-RP2"
RPI_CIRCUITPYTHON_PATH = "/Volumes/CIRCUITPY"
TIMEOUT_THRESHOLD = 20 #seconds
time_prev = time.monotonic()

operation_finished = False

# Nuke if needed
if NUKE:
    try:
        shutil.copy(NUKE_FP, RPI_INIT_FP)

    except Exception as e:
        print(f"no folder named RPI-RP2 found {e}")
        sys.exit()

    print("Nuking...")

# Copy UF2 to device
ready_for_copy = False
print("Waiting for RPI-RP2 to mount...")
while not ready_for_copy:
    try:
        shutil.copy(UF2_FP, RPI_INIT_FP)
        ready_for_copy = True
        print("copied uf2 to RPI-RP2")
        time_prev = time.monotonic()
    except:
        print("Retrying in 2s...")
        time.sleep(2)

    if time.monotonic() - time_prev > TIMEOUT_THRESHOLD:
        print("Timeout")
        sys.exit()

time.sleep(10)

# Copy src files to CIRCUITPY
success = False
print("Waiting for CIRCUITPY to mount...")
time_prev = time.monotonic()
while not success:
    try:
        copy_tree(SRC_FOLDER_FP, RPI_CIRCUITPYTHON_PATH)
        success = True
        print("Success")
        time_prev = time.monotonic()
    except:
        print("Retrying in 2s...")
        time.sleep(2)

    if time.monotonic() - time_prev > TIMEOUT_THRESHOLD:
        print("Timeout")
        sys.exit()