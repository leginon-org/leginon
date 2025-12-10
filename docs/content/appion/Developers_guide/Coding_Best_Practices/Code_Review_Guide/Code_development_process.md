1.  Developer writes code
2.  Developer checks code into Subversion
3.  Developer updates Redmine issue with:
    1.  the svn revision number
    2.  a description of the changes
    3.  a reference to test cases or a description of how to test the changes
    4.  set the Status to In Code Review
    5.  assign the issue to another person to perform a code review
4.  Code reviewer receives an email that they have code to review
5.  Code reviewer inspects the changes to the code using the review guide.
    1.  Revisions that involve complicated logic or widespread changes are better done in person. In this case the reviewer can ask the developer to do a walk through.
6.  If the reviewer finds a problem, the Redmine issue is updated with:
    1.  a description of the problem
    2.  the Assigned to field is set back to the developer and the process starts over.
7.  If no problems are found, the Redmine issue is updated with:
    1.  The Status is set to In Test
    2.  The Assigned to field is set to someone who can readily test it.
8.  The fly server is updated nightly with the latest code in SVN. The code may be tested at http://fly/myamiweb the day after the code is checked in.
9.  If the tester finds a problem, the Issue is reassigned to the developer and the process starts over.
10. If the tester does not find a problem the Issue Status is set to Closed.
