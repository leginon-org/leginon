An alignment run is one or more iterations of alignment of images from one or more tilt series of the same interested area.
A tilt series is defined as a group of images acquired during a single axis tilt sequence.

## Run identification:

-   appiondata.ApTomoAlignmentRunData: Most importantly, an id number for the alignment run.

## Input information:

-   leginondata.TiltSeriesData: Gives tilt series and basic tilting parameters such as angle increment, min/max tilts and an identifying num
-   leginondata.TomographySettingsData: Settings used in MSI-Tomography application. Some of the advanced tilt series parameters can only be found in here.
-   appiondata.ApTiltsInAlignRunData: This is for future combination of dual tilt series so that an alignment run can use more than one tilt series.

## Alignment method parameter references:

appiondata.ApTomoAlignmentRunData has references to one of the three tables that stores parameters for each method of alignment.

-   appiondata.ApImodXcorrParamsData
-   leginondata.TomographySettingsData
-   appiondata.ApProtomoParamsData


-   Because the alignment run references the method,This means that at the moment, we can not do one iteration of alignment with IMOD shift-only alignment and then use that alignment as the starting point of Protomo refinement. The use of apppiondata.ApTomoAlignerParamsData should make it possible in the future but I have not extend it beyond the case for Protomo*


-   appiondata.ApTomoAlignerParamsData: defines general parameters for an iteration, for example, what the previous refinement iteration the new iteration is refined against. For Protomo refinement, it also Links ApProtomoRefinementParamsData (See below) with ApTomoAlignmentRunData with unique id.

## Protomo iterative alignment parameters:

-   appiondata.ApProtomoRefinementParamsData: Parameter of Protomo refinement for a given iteration

## Alignment results:

-   appiondata.ApProtomoModel: The geometric as defined in Protomo refinement programs. IMOD and leginon method have an unrotated/unscaled model entry in this table.
-   appiondata.ApProtomoAlignmentData: Probably should drop the Protomo part in its name. It is where the alignment rotation and shift are recorded using orientation definition used in Protomo although it could also be determined by other methods.
