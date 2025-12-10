## TIA raw (*.bin)

The raw format in TIA is a binary file with a header. Similar to mrc format image files, this can be parsed and converted to numpy array and then converted to any other image format. A python script that has a few basic functions such as read and readHeaderFromFile can be found in pyami/tiaraw.py

For microED purpose, we choose to save int32 data type since the image we received are gain/dark corrected.

## TIA raw to mrc

Within leginon/diffrtransfer.py script this image is converted to mrc format, also at int32. If you want to do this yourself, you can use pyami/tiaraw2mrc.py to make the conversion. See the script in the repository for instruction.

## mrc to SMV

SMV is a simple crystallography format that is typically in unint16.

To retain the statistical characterization, Leginon/diffrtransfer.py converts each of the diffraction series with a constant offset that is recorded in SMV header as LEGINON_OFFSET
LEGINON_OFFSET is (--1) * minimal of all image min values in the diffraction series. This is not expected to be very large if the gain/dark reference are correct. Larger values are usually caused by cosmic ray spike and should be ignored. Therefore, we set a cut off at 2000.

DIALS does not read LEGINON_OFFSET but wants PEDESTRAL value. We make an estimate of reasonable PEDESTRAL value as the maximum of all image min values in the diffraction series after LEGINON_OFFSET is applied. This is defined as such since proper gain/dark corrected image should find its background value averaged at 0 in raw or mrc images.

For example, for a diffraction series that has three images. Their raw/mrc image minumal values are (--10000,--145,--200). LEGINON_OFFSET will be 2000. Any values in the first mrc image that is less than ~~2000 are truncated in the corresponding SMV file. PEDESTRAL value =~~(--2000) + (--145)

For more details, please examine leginon/diffrtransfer.py
