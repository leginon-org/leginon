Leginon image files are typically named 09mar16a_atlas1_00005gr_00003sq_00001hl_v1_00002en.mrc

This name includes

1.  sessionname: 09mar16a
     
2.  grid atlas label: atlas1
     
3.  target number in the target list: 00005; 00003; 00001; 00002
     
4.  presetname with which the image is aquired: gr; sq; hl; en
     
5.  target version: v1

Since Leginon always defines target on an image, and an image is acquired at the location of the target offsets from the parent image of the target, a family tree is estabilished. The filename therefore carries this family tree of the multi-scaled imaging.

-   Grid atlas label is always unique in the session. When robotic grid insertion/extration or Grid Entry node class is used for large-scale screening, the atlas label is replaced by the grid label, unique within the
    project, and the insertion number.


-   The targets selected on grid atlas has a unique number in the session. Therefore, the number of squares targeted in the session overall is the same as the largest target number fo sq preset.


-   Each target in the target list an Acquisition node class or subclass receives has a unique number. Ocassionally a target in the list is out of range of the goniometer or is aborted for various reasons before acquired. The filename will therefore skip the number.


-   When drift is declared, a new version of the target is obtained through the node of TransformManager class, therefore the image acquired using that target carries the version number to distinguish it from the
    original.

[Why is the first Grid Image Not Numbered 00001? >](/leginon/Leginon_Manual/Frequent_Asked_Questions/Why_does_the_first_Grid_Image_Not_Numbered_00001)
