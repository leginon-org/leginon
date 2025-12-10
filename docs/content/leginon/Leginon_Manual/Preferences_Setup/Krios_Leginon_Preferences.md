Here are notes of my experimental setup for our Krios modified from the standard values. To apply this on Krios but not on other scopes in the same database, you should copy your application to a different name and rename each node affected. I add a K in front of them, for example.

You need post 3.0 version to take advantages of some of these if I indicate.

## Preset cycling vs lens normalization

All Krios Leginon users in the past use preset cycling just that they do on other scope. However, if lens is normalized for every preset from sq to en as the default, it takes quite a while and seems unnecessary. One group reported that they only cycle high magnification presets. Another turned off lens normalization. Here I record what I do to use lens normalization only.

    KPresets Manager/settings/cycle presets = No.

To use this, you will need to add extra normalization from the standard list given at installation. Here are our current normalization settings in TUI.

  -------------------------- ----------- ----------- -----------
  condition description      Condenser   Projector   Objective
  TEM LM <>SA              No          Yes         Yes
  TEM magnification change   Yes         Yes         Yes
  TEM spotsize               Yes         Yes         Yes
  -------------------------- ----------- ----------- -----------

This is all default behavior except Magnification Change normalization.

## Stage xy movement backlash

Krios compustage we have performs its own hysteresis removal. Including backlash correction as is in standard Leginon setup actually makes the targeting less accurate. To check if this is true for yours. Do this test:

1.  From Leginon Navigation node, acquire an image at sq preset.
2.  Insert Flucam so that you can observe the trajectory.
3.  Click on the Leginon Navigation node image panel a position that requires significant movement in both x and y to reach.
4.  Watch how the trajectory of the targeting.

Instead of a straight diagonal move (xy moved together) or zigzag (xy moved separated), if the stage reach the position by a curved line like the trajectory of Boomerang not coming back to you (depending on the vector of the supposed movement), you have a self-corrected compustage.

If you do, you should change to turn backlash off.

r18177 in 3.0 gives a new instrument class called Krios that you can use. In instruments.cfg on the scope computer, put

    tecnai.Krios


in place of

    tecnai.Tecnai

For 3.3 and above, use fei.Krios in instruments.cfg on the scope computer

    fei.Krios

For existing installation with calibrations, using new class will confuse the queries. Therefore, run the attached python script (tem_classname_change.py) in your leginon processing host to change the database record before starting leginon again.
