## Ptolemy does not find the holes

Ptolemy hole location algorithm relies on estimate lattice from the input image itself. It performs better if there is clear lattice in the image. Therefore, more consistent results will be found if there are many regularly spaced holes in the image. One way to achieve this is to use lower magnification image as inputs.

## Ptolemy blobs not centered on the holes

There is no solution to this. Ptolemy decides the lattice and then place them in what it thinks fit best in the image. If individual holes are off the lattice, it does not adjust for it.

## Where to place focus target in autoscreen

In autoscreen situation, each grid may oriented differently. Two possible way to place the focus target works well.

1.  Use "Center" option in "Focus hole selection" section of the Acquisition Targeting Settings dialog. This uses the Ptolemy lattice to estimate half-way point and use that for focusing.
2.  Use "Any Hole" option in "Focus hole selection" section of the Acquisition Targeting Settings dialog, and add Focus offset that moves it to the edge of that hole.
