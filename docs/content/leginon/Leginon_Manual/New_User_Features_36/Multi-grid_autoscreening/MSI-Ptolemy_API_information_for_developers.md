## Square_Targeting node (MosaicScoreTargetFinder class):

The square finding should operate on each gr image tile at its saved mrc dimension.

### Shell script to call and specified in Blobs settings.

The script should accept the same parameters and give json output as [Setup Ptolemy CLI shell script](/leginon/Leginon_Manual/New_User_Features_36/Multi-grid_autoscreening/First-time_autoscreening_setup/Setup_Ptolemy_CLI_shell_script) for square targeting

### Output json file is a list of square blob founds by the algorithm. For each item, it requires the following key, value pairs.

### area: integer

> number of pixels the square opening on the gr tile image.

### center: [float, float]

> The coordinate of the square opening center [col, row] with [0,0] at the start of the data block in the mrc image.

### score: float

> The score of the blob as goodness of the blob as a good square. The higher the number the better.

### brightness: float

> Mean intensity value or equivalent in the square blob. This is saved as a part of statistics but not used for filtering.

### vertices: [[float, float], [float, float], [float, float], .....]

> convex-hull vertices used by leginon to determine if a cursor position is within the square blob. Same coordinate system as centers.

## Example json:

    [{"vertices": [[600.4, 304.7], [502.5, 334.8], [532.7, 432.7], [630.5, 402.6]], "center": [566, 368], "area": 10488.9, "brightness": 194.2, "score": 0.3902},
     {"vertices": [[464.1, 568.5], [370.0, 597.5], [399.2, 692.5], [493.3, 663.5]], "center": [431, 630], "area": 9785.5, "brightness": 193.7, "score": 0.2530}]

## Exposure_Targeting node (ScoreTargetFinder class):

The hole finding should operate on each hl image at its saved mrc dimension.

### Shell script to call and specified in Hole settings.

The script should accept the same parameters and give json output as [Setup Ptolemy CLI for exposure targeting](/leginon/Leginon_Manual/New_User_Features_36/Multi-grid_autoscreening/First-time_autoscreening_setup/Setup_Ptolemy_CLI_for_exposure_targeting)

### Output json file is a list of target blob founds by the algorithm. For each item, it requires the following key, value pairs.

### center: [float, float]

> The coordinate of the hole center [col, row] with [0,0] at the start of the data block in the mrc image.

### score: float

> The score of the blob as goodness of the hole as a good hole. The higher the number the better. The key does not need to be "score". If you need it in a different name, just change leginon settings to match.

## Example json:

    [{"center": [566, 368], "score": 0.3902},
     {"center": [431, 630], "score": 0.2530}]
