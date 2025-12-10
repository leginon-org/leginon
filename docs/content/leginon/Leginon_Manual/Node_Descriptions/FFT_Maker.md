The FFT Maker calculates power spectrums of input images.

**Required bindings:**

Acquisition - (AcquisitionImagePublishEvent) -> FFT Maker

There are two FFT Maker nodes in MSI, Exposure FFT and Focus FFT. Both of these FFT Maker nodes need to be bound with events from different acquisition nodes. Exposure FFT (with a hint from its name) is bound to the Exposure (Acquisition) node. Likewise, Focus FFT is bound to the Focus node (that has Acquisition node behavior embedded within it).

## Settings

-   Calculate FFT and save to the database = when enabled, the input image will have its FFT calculated and existence stored in the database


-   Mask radius "1" % of image width = this percentage refers to how much of the center of the FFT (with the high intesity base frequency) will be masked out in order to make the rest of the FFT features more visable on the computer screen.


-   Images in Database: Find images in this session with label "" = *Currently this feature is not used.

[< The EM node](/leginon/Leginon_Manual/Node_Descriptions/The_EM_node) | [Focuser >](/leginon/Leginon_Manual/Node_Descriptions/Focuser)
