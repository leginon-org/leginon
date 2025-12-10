Most steps in this original hole finder are identical to that of JAHC holefinder used in MSI-T application. Only the edge and template steps are different since edge finding is performed before using an artificial ring template to create the correlation image used in the later steps.

## Edge>

A good combination of parameters show the edges of holes well with minimal thresholded "edge" from random features.

* Select the Edge Display Selection before opening the Edge Display Settings window.

* Choose an edge detection Threshold and press "Test". "Test" should be done every time a parameter is changed to check its effect.

* Adding a proper low pass filter can sometimes reduce the fragmented appearance of the edge image.

* Increase the Threshold if too many edges are shown in the edge image.

* Use the ruler tool to measure the average inner and outer hole diameters for preparation on template correlation.

## Template>

A good template gives a sharp correlation at the center of the holes.

* Select the Template Display Selection before opening the Template Display Settings window.

* Click Add (Rings) and enter the inner and outer hole diameters that were measured in the previous section. (Only one set of hole diameters should be in the list. If a set already exists, click Edit instead of entering the measure hole diameters.)

* Choose a correlation method. "cross" correlation is the typical for high contrast images. "phase" correlation works better with weak hole edges (i.e., thick ice) but should be used with a low pass filter. For example, increasing the filter pixel size can eliminating scattered peaks.

* "Test" these parameters and adjust, normally, the template diameters for sharpest correlation peaks at the center of the holes and exit the setting window.

[< Summary of this applicaiont](/leginon/Leginon_Manual/Leginon_MSI-Edge_Application/Summary_of_this_application)
