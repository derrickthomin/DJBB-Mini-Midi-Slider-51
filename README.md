# DJBB Mini Midi Slider 51
small midi controller based on the Raspberry Pi Pico

<img src="https://github.com/user-attachments/assets/d4b539b0-6159-4b0f-80dc-8a50eefbf887" alt="mini midi slider 51" width="400">

**FEATURES**
- 16 x Drum Pads w/ RGB LEDs (membrane style keys)
- 3 x MIDI mappable sliders
- Control up to 51 params w/ sliders (3 global, 48 pad-specific)
- Latch buttons to send pad-specific CC msgs with the sliders
- Can latch multiple to send CC messages for each
- Case and keypad is 3D printed in PETG. PETG is flexible and durable, making it suitable for a membrane-style keypad.

You can buy a fully built device here:
[Mini MIDI Slider 51 on Etsy](https://djbajablast.etsy.com/listing/1744340176/mini-midi-slider-51-compact-midi-drum)


## Updating Firmware

Follow these simple steps to update the firmware on your **DJBB Mini Midi Slider 51**:

1. **Download the `src` Folder:**
   - Click the link below to download the `src` folder from this repository:
     - [Download `src` Folder](https://download-directory.github.io/?url=https://github.com/derrickthomin/DJBB-Mini-Midi-Slider-51/tree/main/src)

2. **Connect Your Mini Slider to Your Computer:**
   - **For macOS Users:**
     - Open **Finder**.
   - **For Windows Users:**
     - Open **File Explorer**.
   - Locate your connected **Mini Midi Slider 51** device. It should appear as a removable drive (likely `CIRCUITPY` or `minslider`)

3. **Transfer the Firmware Files:**
   - Open the downloaded `src` folder.
   - **Select All Files:**
     - **macOS:** Press `Command + A`.
     - **Windows:** Press `Ctrl + A`.
   - **Drag and Drop:**
     - Drag the selected files from the `src` folder and drop them into the root directory of your Mini Slider device.
   - **Overwrite Confirmation:**
     - When prompted to overwrite existing files, confirm by clicking **"Replace"** or **"Yes"**.

4. **Complete the Update Process:**
   - **Wait for the Transfer to Finish:**
     - The files will begin transferring to your Mini Slider. This may take a few moments.
   - **Automatic Reboot:**
     - After the transfer is complete, the Mini Slider should automatically reboot to apply the new firmware.
   - **Manual Reboot (If Necessary):**
     - If your Mini Slider does not reboot on its own:
       - **Unplug** the Mini Slider from your computer.
       - **Plug it back in** to manually restart the device.

5. **Verify the Update:**
   - Once the Mini Slider has rebooted, it should be running the latest firmware.

## Changelog

### v1.1.0 - 2024-04-27

- **Enhanced Functionality:**
  - **Global CC Messages:** Holding a pad in Note mode while moving a slider now sends global CC messages. Previously, it was impossible to play a note while sending global CC messages.
  - **Single Click Mode Switching:** Changing modes is now a single click of the FN button instead of a double click, enabling faster mode switching.
  - **New N+C Mode:** Introduced N+C Mode alongside Note and CC modes. In this mode, holding a pad sends a note and engages pad-specific CC messages, similar to how Note mode operated previously.
  
- **Latch Improvements:**
  - **Universal Pad Latching:** Pads can now be latched in any mode. Double-click the FN button to toggle latch mode.
  - **Flexible Latching Mechanism:** Pads can be latched even when in unlatched mode by holding FN and clicking the pad. If already in latching mode, performing the same action will make the pad behave as if it is in unlatched mode.

- **Velocity Control:**
  - **Velocity:** In Note mode, holding FN and moving the top-right slider changes the global velocity. Hold FN + a pad to change the velocity for just that pad.

- **User Interface Updates:**
  - **Bank Indicator:** The UI now displays the current MIDI bank when changing banks, providing clear feedback to the user.
  - **Lock / Unlock Icons:** So you can see which latch state you switched to
  - **Velocity:** Visual representation of velocity as you change it.
