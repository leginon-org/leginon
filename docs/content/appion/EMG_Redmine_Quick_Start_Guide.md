[TOC]

EMG is using [Redmine](http://www.redmine.org) for

-   tracking project issues
-   viewing the code repository from a web interface
-   managing user forums
-   all documentation

## 1 Register as a user

If you have not registered, click on the **Register** link in the top right corner of the website. After submitting the information requested, an administrator will be notified via email that your registration is pending approval. When you are approved, Sign in using the **Sign in** link at the top right corner of the website.

## 2 Post a question on the Forum

Once you have registered, you can post questions on the [Forums](http://emg.nysbc.org/redmine/projects/leginon/boards).

## 3 Select a project to view

Select **Projects** from the top left corner of the website. You will see projects that you are a member of, as well as those that are public.

Although there is not a clear division in the software code between Appion and Leginon, we use these as project names to be consistent with how the products are presented to the rest of the world.
The single svn repository holding the code for both products is available from both Redmine projects.

Available Projects:

-   Appion
    -   loosely everything related to image processing
-   Leginon
    -   loosely everything that has to do with image capture

## 4 Add a new issue

-   Go to the project that you want to add the issue under. Select the **New issue** tab.
-   Select a Tracker: Bug, Feature, Support, or Task.
-   Write a descriptive subject line.
-   At this point you may select **Create** at the bottom of the page. If you can fill in more information, please do.
-   To link to another issue maintained in Redmine, type # followed by the issue number (#17).
-   To link to a subversion changeset, put a lower case r in front of the revision number (r234).

When you are ready for the next level of issue settings check out the [Issue Workflow Tutorial](/appion/EMG_Redmine_Quick_Start_Guide/Issue_Workflow_Tutorial).

## 5 View issues

-   Select the **Projects** link at the top left corner of the web page.
-   Select "View all issues" on the right side of the page. This will display all open issues from all projects.
-   At the top of the screen is a "Filters" section.
-   Select any combination of filter criteria and click **Apply** to view the results.
-   You may save this query and run it in the future. It will show up under "Custom queries" on the right side navigation bar.

## 6 Edit a wiki page

To edit, click the **Edit** link at the top of the page.

-   Official Redmine syntax help: [here](http://www.redmine.org/wiki/redmine/RedmineTextFormatting) and [here](http://redcloth.org/hobix.com/textile/).
-   Wiki Extensions: Check the [wiki extension plugin syntax](http://www.r-labs.org/wiki/r-labs/Wiki_Extensions_en).
-   Tips and tricks: These were a bit more difficult to figure out, check [Wiki Tips](/appion/EMG_Redmine_Quick_Start_Guide/Wiki_Tips).
-   Adding symbols: You can use the [html symbol name](http://www.ascii.cl/htmlcodes.htm)

## 7 Create a new wiki page

To create a new wiki page, edit an existing one and include double brackets around the name of the page that you wish to create like this:

![[My new wiki page]]

It will appear as a red link when it is saved.
Click on the link and add content to your new page.
Remember to save it before navigating away or you will lose all your hard work!
More information on Wiki creation is [here](http://www.redmine.org/wiki/redmine/RedmineWikis).
