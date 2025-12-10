## Preset manager fails to send a preset to the microscope

Why: If Tecnai microscope is busy for reasons such as correcting a pole touch error, Leginon can not comunicate with the scope until the latter is free.

Solution: Make sure the scope is not busy any more and send the preset to scope manually to resume data collection.

Note: The immediate imaing condition may be wrong since manual preset sending does not include extra image shift from the target, but it should recover in later process.

## Leginon can not activate GIF slit

Why: Unknown

Try these:

-   Toggle the filtered button in the EFTEM menu a few times.


-   Send tomography preset and then the square preset to scope.


-   Make sure Gatan's GIF tracking program is off.

There is no fix for this bug.

## Image acquired at the wrong stage position

Commonly why: dirty or worn compustage parts

Solution: Call for scope service

-   If this happens during grid atlas data collection, it has no impact on targets selected on it. However, there is no way to patch to the intended location easily.


-   If this happens while a target is reacquired for drift correction, the drift correction will be wrong. There is no fix except to "declare drift" in Drift Manager to force another drift corection as soon as possible.

[< General operation problems](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems) | [Troubles with Imaging >](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Imaging_-_Troubleshooting)
