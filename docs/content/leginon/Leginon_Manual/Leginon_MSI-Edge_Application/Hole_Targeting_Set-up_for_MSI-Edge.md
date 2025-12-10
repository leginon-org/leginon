We can use any image that is already loaded into Hole Targeting to adjust these parameters. The values in this node vary so much from grid to grid that the best way to find these parameters is by going through a step-by-step trial and error process. The parameters not mentioned here can be left at their default values. To proceed from one step of the hole targeting process to another, simply proceed from top to bottom through the display selection buttons in the image control panel. The display settings associated with each display selection are the locations where the Hole Targeting parameters can be adjusted. To see the final acquisition and focus targets, enable only the Original, acquisition, and focus display selections.

### 1. Leginon/Hole Targeting/Original>

Use this setting to load a test image if needed.

* Select the Image Display Selection before opening the Image Display Settings window.

* Browse the rawdata directory of the current session for an example image for testing.

* Load the selected file and exit Image Display Settings window.

### 2. Leginon/Hole Targeting/Edge>

A good combination of parameters show the edges of holes well with minimal thresholded "edge" from random features.

* Select the Edge Display Selection before opening the Edge Display Settings window.

* Choose an edge detection Threshold and press "Test". "Test" should be done every time a parameter is changed to check its effect.

* Adding a proper low pass filter can sometimes reduce the fragmented appearance of the edge image.

* Increase the Threshold if too many edges are shown in the edge image.

* Use the ruler tool to measure the average inner and outer hole diameters for preparation on template correlation.

### 3. Leginon/Hole Targeting/Template>

A good template gives a sharp correlation at the center of the holes.

* Select the Template Display Selection before opening the Template Display Settings window.

* Click Add (Rings) and enter the inner and outer hole diameters that were measured in the previous section. (Only one set of hole diameters should be in the list. If a set already exists, click Edit instead of entering the measure hole diameters.)

* Choose a correlation method. "cross" correlation is the typical for high contrast images. "phase" correlation works better with weak hole edges (i.e., thick ice) but should be used with a low pass filter. For example, increasing the filter pixel size can eliminating scattered peaks.

* "Test" these parameters and adjust, normally, the template diameters for sharpest correlation peaks at the center of the holes and exit the setting window.

### 4. Leginon/Hole Targeting/Threshold>

A good correlation threshold leaves only small blobs of the correlation peaks from the holes. Since the peaks from holes with ice are usually weaker but more important to catch, it is o.k. to leave some but not too many noise peaks. This parameter also tends to change during an experiment. The value is in the unit of number of standard deviation above the mean.

* Select the Threshold Display Selection before opening the Threshold Display Settings window.

* Enter the Threshold value determined in the previous section and press Test.

### 5. Leginon/Hole Targeting/Blobs>

If the threshold level from the last step is too low, there will be a lot of big blobs, making the process slow. The parameters set in this node reasonably limit the total number of blobs.

* Select the Blob Display Section before opening the Blob Display Settings window.

* "Border" should be set to at least the radius of the holes in order to reduce the border effects.

* "Maximum number of blobs" is typically 300 (although it is sometimes larger if you expect more holes).

* "Maximum size of blobs" should be adjusted until mostly hole centers, not junk spots, are shown.

* "Test" and adjust the parameters in the last three steps (2-4) to acheive the best results.

* To help define the lattice, measure the distance between hole centers with the ruler tool.

### 6. Leginon/Hole Targeting/Lattice>

The lattice of the holes is not perfect; therefore, a decent tolerance is necessary for a good fit to this imperfect lattice. If only a few blobs were centered in the last step, then this step is not likely to work.

* Select the Lattice Display Section before opening the Lattice Display Settings window.

* Enter the Spacing from the measurement in the last step.

* Typical Tolerance = 0.1 (i.e., 10% error in the spacing is accepted)

* Hole Stats Radius = ~ 3/4 of the hole radius.

* Zero thickness = the intensity measurement from an empty hole at the same preset (the sq preset).

* "Test" and examine the "mean thickness" and "standard deviation of thickness" in each hole on the lattice.

### 7. Leginon/Hole Targeting/acquisition>

The settings here depend on the required ice thickness and on the "Zero thickness" setting in the last step. At a minimum, these settings can be used to rule out holes that are empty and that have massive ice contaminant.

* Select the Original and acquisition Display Sections before opening the acquisition Display Settings window.

* Min. mean = ~ 0.05 measured by ln(I0/I)

* Max. mean = ~ 0.3

* Max. stdev = ~ 0.2

* Focus hole selection = Good hole ( or "Any Hole" if hole targets are not plentyful. With "Any Hole" option,and a bad hole may be targeted that is hard to focus such as very thick ice. Alternatively, "Off" to skip the Z height correction step at each square )

* Use target template = no

### 8. Leginon/Hole Targeting/focus>

The only relevant focus setting ("Focus hole selection") in Hole Targeting is in relation to Z Height correction. The Leginon/Hole Targeting/focus Display Settings window = Leginon/Hole Targeting/acquisition Display Settings window. This means that the focus settings were set in the previous section and do not need to be revisited here. To see the focus targets, enable the Original and focus (and optionally the acquisition) display selections in the image control panel.

### 9. Leginon/Hole Targeting/Settings> Activate automatic hole finding for future images received.

Skip automatic hole finding = no

[< Summary of this application](/leginon/Leginon_Manual/Leginon_MSI-Edge_Application/Summary_of_this_application) | [Exposure Targeting Set-up for MSI-Edge >](/leginon/Leginon_Manual/Leginon_MSI-Edge_Application/Exposure_Targeting_Set-up_for_MSI-Edge)
