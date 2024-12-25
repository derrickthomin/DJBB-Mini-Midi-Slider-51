Please test the following scenarios:

Switching Modes:

Cycle through the modes using single presses of the FN button.
Verify that the display updates accordingly for each mode.
N+C Mode Behavior:

In N+C mode, latch a pad and verify that both the note is latched (note plays) and CC messages are sent when sliders are moved.
Hold the FN button and press the +/- pads to change the bank, similar to Note mode.
Slider Behavior in N+C Mode:

With no pads latched or held, move the sliders and verify that global CC messages are sent.
With pads latched or held, move the sliders and verify that pad-specific CC messages are sent for those pads.
Latch Persistence Across Modes:

Latch pads in N+C mode, then switch to Note mode and CC mode.
Verify that the latch states are preserved and the pads remain latched.
Velocity Adjustments:

In N+C mode, attempt to adjust the per-pad velocities (should not change).
Adjust the global velocity (holding FN button and moving Slider 1) and verify that it works.
Function Button Behavior:

Verify that holding the FN button for more than the HOLD_THRESHOLD suppresses mode change upon release.
Edge Cases:

Test interactions with latch modes in N+C mode.
Ensure that the latch toggling works as expected when double-pressing the FN button.