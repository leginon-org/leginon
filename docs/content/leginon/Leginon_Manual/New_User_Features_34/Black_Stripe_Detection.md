For users of the K2 camera. At NYSBC we occasionally lose a channel during collection, resulting in a black stripe in the image. More rarely, counted movies start coming out the wrong size, off by 2 pixels in the X and Y axes. This node will detect both types of problems and throw an warning message. Particularly useful feature if slack messaging is in use.

## Adding the node

Binding needs to be made from Exposure to the Black Stripes Detector Mode. Binding is AcquistionImagePublishEvent.

## Use

Control panel has 2 options, whether to detect black stripes and whether to pause on error. Turning it on means every exposure image will be analyzed for lack of signal in all 8 stripes. Will output the mean and sd of each stripe in the text window. A black stripe is defined as having mean=0 and sd=0. Additionally tests the size to make sure it is K2 standard size (3710 x 3838).

## Testing

Works on images in both orientations (portrait and landscape). Works on super-res images (bins to counting before testing). Does not seem to affect collection rates. Calculations are relatively simple and no pausing is needed during calculations.

## Notes

Note: Pause feature is not yet implemented in the code. Can be checked but no pausing is done. May add a feature to only check every N images.
