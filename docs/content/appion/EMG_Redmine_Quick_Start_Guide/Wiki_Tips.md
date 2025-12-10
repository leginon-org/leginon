[TOC]

## 1 Add "breadcrumbs" to your wiki page

Breadcrumbs are links that appear at the top of a wiki page that show the previous pages that you visited.
To add breadcrumbs you must set up parent/child relationships for wiki pages.
To set the parent of the page that you are currently viewing, select "Rename" at the top right.
Copy and paste the name of the parent page from the desired parent page's "Rename" section.

## 2 Add a Table of Contents to your wiki page

If your wiki page is long with multiple headings, you may want a table of contents.

## 3 Wiki links

![[AMI Redmine Quick Start Guide]] displays a link to the page named 'AMI Redmine Quick Start Guide': [AMI Redmine Quick Start Guide](/appion/AMI_Redmine_Quick_Start_Guide)

![[AMI_Redmine_Quick_Start_Guide|AMI Redmine QSG]] displays a link to the same page but with a different text: [AMI Redmine QSG](/appion/AMI_Redmine_Quick_Start_Guide)

![[AMI_Redmine_Quick_Start_Guide#1-Register-as-a-user|How to register]] displays a link to the header on the same page with a different text: [How to register](/appion/AMI_Redmine_Quick_Start_Guide#1-Register-as-a-user)

Note that when linking to a header on another wiki page, the header must be labeled h1., h2., or h3. (h4. will not work.) Also, there may not be special characters such as period(.) or dash(-) in the header that you are linking to.

## 4 Add super cool images to a wiki page

At the bottom of the wiki page is an "upload file" link. Use this to upload your image file to Redmine.
Then right click on the link to the file and select "Copy Link Location".
Next, edit the wiki page and paste the link location. Put an exclamation point(!) at the start and end of the URL.
You can also just put the name of the file you uploaded between the exclamation points...as long as you are referring to an images that is attached to the specific page you are editing. You can use the url on any wiki page.

Example:

![](images/images.jpeg)

Move it to the right hand side of the page with a greater than symbol(>) after the first (!).

Example:

![](images/images.jpeg)

You can also turn the image into a link to a url by adding a colon (:) after the last (!) and then the url to link to.

Example:

[![](http://lh5.google.com/vossman77/RzJbEE3GhuI/AAAAAAAAASY/SSaOA7FZKwI/nramm.jpg?imgdl=1)](http://nramm.scripps.edu)

## 5 Upload an Apple Keynote file

Since a Keynote file is actually a folder, it will not upload properly in Redmine. You will need to put the Keynote into an archive like Zip and then upload the zip file.
Reference: http://www.redmine.org/boards/2/topics/992?r=1032#message-1032

## 6 Add a reference to a bug number from a subversion commit comment

If you add refs and the bug number to your subversion message it automatically links them, e.g., 'refs #139'.
