## Scope Setup

-   Operate non-LowMag imaging mode in Zoom-1 for simplicity.

pyscope/hht.cfg.template that we starts hht.cfg with contains a working set of calibrations that should allow basic operation.

We use '%' as parser for different level of keys. A list of values are separated by "," For example,

    [category]
    MAIN_KEY%SUB_KEY1 = value1,value2
    MAIN_KEY%SUB_KEY1 = value3,value4


will produce effectively a python config dictionary key value pair like this:

    category: {'main_key':{'sub_key1':[value1, value2], 'sub_key2':[value3,value4]}}

## Confirm on the microscope that the magnification list in hht.cfg contains valid magnifications in the defined imaging mode.

These are the lines in hht.cfg with the keys in "optics" module.

    MAGS%LOWMAG
    MAGS%ZOOM1-HC
    MAGS%ZOOM1-HR

-   A magnification not included in the list will not show up in Leginon interface and thus not usable.

## Save the focus offset and initial eucentric focus files

The objective lens focus is different at each magnification in combination to the imaging mode that is calibrated by the manufacturer. The following instruction saves these offset values and an initial eucentric focus in files that Leginon will access and overwrite (in the case of the encentric focus).

1. Define the location and file names for these paths at the end of hht.cfg under "defocus" module.
2. Run pyscope/hht_defocus.py and follow the instruction within the program to change imaging mode, magnification, focus.
