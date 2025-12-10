From the user perspective, a refinement job includes 3 parts:

1.  Preparation step
    -   prepares any data that is needed for the method to be run
    -   includes modifying a selected stack to be in any required format
2.  Run step
    -   User selects which cluster they would like to run the job on
    -   The job file is built and submitted to a queue
3.  Upload step
    -   Results are converted to a format that Appion accepts
    -   Converted results are uploaded to the Appion Database

From a programming perspective, the following pieces of code need to be written:

1.  GUI prep step launch form - see [Refinement GUI tutorial](/appion/Developers_guide/Refine_Refactor_documentation)
2.  Python prep step run script
3.  GUI run step launch form - see [Refinement GUI tutorial](/appion/Developers_guide/Refine_Refactor_documentation)
4.  Python run step run script - see [Refinement Run tutorial](/appion/Developers_guide/Adding_refine_runjob)
5.  GUI upload step launch form - see [Refinement GUI tutorial](/appion/Developers_guide/Refine_Refactor_documentation)
6.  Python upload step run script - see [Refinement Upload tutorial](/appion/Developers_guide/How_to_add_a_new_refinement_method)
7.  GUI results viewing page

Many of these pieces use the [object-oriented programming](/appion/Developers_guide/Object_Oriented_Programming) feature of inheritance to create base classes that take care of common functions.
To add a new cluster job to the Appion Pipeline, you will need to have a basic grasp of [object-oriented programming](/appion/Developers_guide/Object_Oriented_Programming).
This design is used to reduce the amount of copied and pasted repeated code which is error prone, fragile, and difficult to maintain. It can also reduce the learning curve for adding new packages to Appion if the base classes are well defined and easy to read examples are provided.
