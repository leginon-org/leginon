Any image can be used as a template for the hole finder. If you create your own, you just need to point the node preference to the right mrc file. Our philosophy for the template distributed with the Leginon package (your leginon python source path/holetemplate.mrc) was to make a hole template that had the average features of a 2 micron hole covered in vitreous ice. To accomplish this, we took fifty images of holes acquired by Leginon at 5000X magnification. Holes were then boxed out of these images using the boxer utility in the EMAN package making sure that the holes were in the center of the box.

![](images/JAHCHole.png)

Figure 1-Boxing a hole

The hole images were then assembled into a single Imagic stack. Since the hole images were well centered, they were then averaged to produce an image of an average hole (fig. 2). Finally, the average hole image was rotationally averaged to produce a symmetrical generalized hole image (fig. 3).

![](images/JAHCAvg.png)

Figure 2-Average of 50 holes

![](images/JAHCRotAvg.png)

Figure 3-Rotationally averaged final template.

The following is the EMAN program and parameters associated with each step.

1. For 10-50 hole images, run boxer to box out holes and save them as a pair of IMAGIC file (hole.hed and hold.img).

    boxer <hole_image.mrc>

2. Average hole images and save the output as an MRC image file.

    proc2d hole.hed average.mrc average

3. Rotationally average the average hole image and save as an MRC image file.

    proc2d average.mrc rotav.mrc rotav

4. The result is the new hole template.

[< Summary of this application](/leginon/Leginon_Manual/Leginon_MSI-T_Application/Summary_of_this_application_-_MSI-T) | [Hole Targeting Set-up for MSI-T >](/leginon/Leginon_Manual/Leginon_MSI-T_Application/Hole_Targeting_Set-up_for_MSI-T)
