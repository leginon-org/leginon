Falcon Intermediate Image Tool allows base frames to be saved in 7 frame bins.

For raw frame saving using FEI's software, the midpoint time of the starting and ending base frames to be included in saved frame bin is defined by an xml file on Titan as

    C:\Titan\Data\Falcon\IntermediateConfig.xml

To adjust the way the frames are saved in the bins, this file needs to be re-configured.

Leginon handles this configuration file modification required for each image acquisition. However, if you need to generate your own, such as when setting it up for obtaining gain/dark reference in TUI's Reference Manager, you can make a copy of the python script in myami/pyscope/falconframe.py and run it alone.

    python falconframe.py exposure_time_in_second first_distributed_frame_number

For example:

    python falconframe.py 1.0 2


generates this xml file equivalent to Leginon camera config *Frames to Use" (1,2,17)

    <?xml version="1.0" encoding="utf-8"?>
    <IntermediateConfig>
        <FormatVersion>1.0</FormatVersion>
        <StoragePath>E:\frames/20140808_14395200</StoragePath>
        <InterFrameBoundary>0.084 - 0.084</InterFrameBoundary>
        <InterFrameBoundary>0.139 - 0.195</InterFrameBoundary>
        <InterFrameBoundary>0.251 - 0.363</InterFrameBoundary>
        <InterFrameBoundary>0.418 - 0.530</InterFrameBoundary>
        <InterFrameBoundary>0.586 - 0.697</InterFrameBoundary>
        <InterFrameBoundary>0.753 - 0.864</InterFrameBoundary>
        <InterFrameBoundary>0.920 - 1.032</InterFrameBoundary>
    </IntermediateConfig>
