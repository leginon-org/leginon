This method uses multiple iterations of Spider AP SR (reference-free) and Spider AP SH (reference-based) commands to align your particles. It is a set of batch-files used for analysis of conformational flexibility of fatty acid synthase during catalysis in *Brignole, et al. Nature Structural and Molecular Biology vol16, 190-197 (2009)*.

## General Workflow:

1.  Check to boxes of templates to be used as references during alignment.
2.  Click on "use these templates."
    ![](images/Picture_26.png)
3.  Make sure that appropriate run name is specified. Appion increments names automatically, but users are free to specify proprietary names and directories.
4.  Enter a description of your run into the description box.
5.  Make sure that appropriate directory tree is specified.
6.  Select the stack to align from the drop down menu. Note that stacks can be identified in this menu by stack name, stack ID, and that the number of particles, pixel and box sizes are listed for each.
7.  Make sure that "Commit to Database" box is checked. (For test runs in which you do not wish to store results in the database this box can be unchecked).
8.  Double check that the templates are the ones you want to use.
9.  Click on "Run Ed-Iter Alignment" to submit your job to the cluster. Alternatively, click on "Just Show Command" to obtain a command that can be pasted into a UNIX shell.
    ![](images/Picture_33.png)
10. If your job has been submitted to the cluster, a page will appear with a link "Check status of job", which allows tracking of the job via its log-file. This link is also accessible from the "1 running" option under the "Run Alignment" submenu in the appion sidebar.
11. Once the job is finished, an additional link entitled "1 complete" will appear under the "Run Alignment" tab in the appion sidebar. This opens a summary of all alignments that have been done on this project.
    ![](images/Picture_34.png)
12. Click on the link next to "reference stack" to open a window that shows the class averages and that contains tools for exploring the result. Such tools include the ability to browse through particles in a given class, create templates for reference based alignment, substack creation, 3D reconstruction, etc.
13. To perform a feature analysis, click on the grey link entitled "Run Feature Analysis on Align Stack ID xxx".

## Notes, Comments, and Suggestions:

1.  This method sometimes produces a halo effect around particle averages. This is particularly noticeable for non-globular particles, due to the nature of the algorithm used to determine the radii of class averages output between alignment iterations. If this becomes an issue, we suggest trying an alternate alignment algorithm.
2.  In the parameters box on the right, under "Particle Params" the last and first ring radii refer to the inner and outermost rings along which alignment parameters will be determined. Good default values for a particle with a box size of 300 x 300 pixels are shown in the overview snapshot above.
3.  In the parameters box on the right, under "Alignment Params" the search range refers to the number of pixels that will be considered from the center of any given starting point during parameter determinination. A step size of 1 means that every single ring between first and last radii will be considered during the search. Good default values for a particle with a box size of 300 x 300 pixels are shown in overview snapshot above.
4.  Clicking on "Show Composite Page" in the Alignment Stack List page (accessible from the "completed" link under "Run Alignment" in the Appion sidebar) will expand the page to show the relationships between alignment, feature analysis, and clustering runs.

[<Run Alignment](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Particle_Alignment/Run_Alignment) | [Run Feature Analysis >](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Particle_Alignment/Run_Feature_Analysis)
