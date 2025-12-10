## Install myami package on the associated camera computer

-   Instead of installing myami package on HHT scope-controlling PC, the access can be through the computer controlling the digital camera.


-   No special supporting package needed.

## hht.cfg

hht.cfg records some instrument specific parameters that are required to convert the instrument output to SI units that Leginon depends on.

The values in pyscope/jeol.cfg.template is based on NYSBC HT7800 equipped with TVIPS XF416. You may start with these and copy it
to pyscope/hht.cfg or other [valid myami configuration file locations](/leginon/Locate_global_config_directory_on_Windows).

## instruments.cfg

[scope]
class: hitachi.HT7800
cs: 3e-3

-   Cs for HR and HC modes are 3.0 mm and 5.2 mm, respectively. You will most likely use HR mode on the final image.


-   You will also be adding the camera in the same instruments.cfg since this file is located on the camera computer in this instruction.

## Testing with pyscope

In python command

    from pyscope import hitachi
    t =hitachi.HT7800()
    t.getHighTension()

You should get the current gun high tension value in Volts.

_

## Next Step: [Hitachi specific Calibrations](/leginon/Leginon_Manual/PyScope_Changes_35/Hitachi_7800_support/Hitachi_setup)
