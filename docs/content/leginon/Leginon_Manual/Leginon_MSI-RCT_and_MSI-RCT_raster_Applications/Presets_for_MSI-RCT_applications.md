The main difference between MSI-RCT applications and other MSI's is that a low
magnification image is needed for the target transformation algorithm to reliably find
features to match between tilts. Two strategies has be used with success.

## 1st strategy:

The sq preset is set at a magnification in the HM mode so that hysteresis is minimized.
and the hl preset is eliminated The "sq" preset is used both at "Square" and "Centered
Square" nodes.

**Presets and Magnification for a typical MSI-RCT**

  Preset     magnification   defocus (m)
  ---------- --------------- -----------------
  gr         120             0
  sq         1700            --2.5e-4
  fc,fa,en   50000           (what you need)

## 2nd strategy:

The sq preset is set at the usual LM magnification. The hl preset is set at the low end
of HM mode. The "sq" preset is at "Square" node and "hl" preset is used at "Centered Square"
nodes.

**Presets and Magnification for a typical MSI-RCT**

  Preset     magnification   defocus (m)
  ---------- --------------- -----------------
  gr         120             0
  sq         550             --2e-3
  hl         1700            --2.5e-4
  fc,fa,en   50000           (what you need)

*see also [RCT run protocol from a user](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_run_protocol_from_a_user)*

[< RCT node set-up](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_node_set-up) | [RCT calibration need >](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_calibration)
