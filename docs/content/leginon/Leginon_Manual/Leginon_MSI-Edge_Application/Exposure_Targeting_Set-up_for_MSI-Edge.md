The same hole finder class from Hole Targeting is used in Exposure Targeting for finding exposure and focus targets at higher magnifications by loosely defining some parameters. This set-up should be much easier and more stable than Hole Targeting. The parameters not mentioned here can be left at their default values. To proceed from one step of the exposure targeting process to another, simply proceed from top to bottom through the display selection buttons in the image control panel. The display settings associated with each display selection are the locations where the Hole Targeting parameters can be adjusted. To see the final acquisition and focus targets, enable only the Original, acquisition, and focus display selections.

### 1. Leginon/Exposure Targeting/Edge>

(This step does not apply if you are using [MSI-T](/leginon/JAHC_finder_nodes_set-up))

A good combination of parameters show edges of the hole(s) well with minimal thresholded "edge" from random features.

* Select the Edge Display Selection before opening the Edge Display Settings window.

* Choose an edge detection Threshold and press "Test". "Test" should be done every time a parameter is changed to check its effect.

* Adding a proper low pass filter can sometimes reduce the fragmented appearance of the edge image.

* Increase the Threshold if too many edges are shown in the edge image.

* Use the ruler tool to measure the inner and outer hole diameter for preparation on template correlation.

### 2. Leginon/Exposure Targeting/Template>

(This step does not apply if you are using [MSI-T](/leginon/JAHC_finder_nodes_set-up))

A good template gives a sharp correlation at the center of the holes.

* Select the Template Display Selection before opening the Template Display Settings window.

* Click Add (Rings) and enter the inner and outer hole diameters that were measured in the previous section. (Only one set of hole diameters should be in the list. If a set already exists, click Edit instead to enter the measure hole diameters.)

* correlation method = "cross" correlation

* "Test" and adjust, normally, the template diameters for better results.

* Find, from the correlation image, the typical correlation peak height for the center of the hole. This will be used in determining the threshold in the next step.

### 3. Leginon/Exposure Targeting/Threshold>

A good correlation threshold leaves only small blobs of the correlation peaks from the hole(s). This parameter also tends to change during an experiment. In addition, the value is in the unit of number of standard deviation above the mean.

* Select the Blobs Display Selection before opening the Threshold Display Settings window.

* Enter the Threshold value determined in the previous section and press Test.

* Use the ruler tool to measure the diameter of blob that represents the center of the targeted hole. Square this number and use it in the next blob finding section.

### 4. Leginon/Exposure Targeting/Blobs>

The Border is used here to prevent the selection of non-targeted holes that show up at the edge of the image.

* "Border" should be set at least the radius of the holes.

* Maximum number of blobs = 1

* "Maximum size of blobs" should be adjusted until only the hole centers are shown. A starting value is the measured blob diameter value measured in the previous section.

* "Test" and adjust the parameter in this and the last three steps to obtain the best results. Ideally, only the targeted hole should be shown and selected.

### 5. Leginon/Exposure Targeting/Lattice>

This step is used here only to remove multiple blobs found close to the center of the targeted hole.

* Spacing= any number.

* Zero thickness is the intensity measurement from an empty hole at the same preset (hole). If not measurable, use a high estimate here.

* "Test." The correct setting leaves only one target.

### 6. Leginon/Exposure Targeting/acquisition>

No discrimination of holes is needed here. This step will set-up the template for exposure and focus targets.

* For example, Minimun ice thickness = 0.01, Maximun ice thickness = 5.0, Maximum Stdev = 2.0

* "Test" to check if the target passes the criteria.

* Use target template = yes

* Set up the template with a list of coordinates relative to the current hole target center. For example, for an acquisition target at the same place as the "good hole" target should have x,y coordinates as 0,0. Add, Edit, and Test the Acquisition and Focus Target Template.

### 7. Leginon/Exposure Targeting/Settings> Activate automatic hole finding for future images received.

Skip automatic hole finding = no

[< Hole Targeting Set-up for MSI-Edge](/leginon/Leginon_Manual/Leginon_MSI-Edge_Application/Hole_Targeting_Set-up_for_MSI-Edge)
