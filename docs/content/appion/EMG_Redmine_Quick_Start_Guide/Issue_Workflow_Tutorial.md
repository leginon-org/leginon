There are several types of Trackers available:

1.  Bug
2.  Feature
3.  Support
4.  Task
5.  Test Case

All fall under the general category of Issue. For each Tracker type, there is the ability to set a status. The status types available vary for each Tracker type.

## Bug and Feature work flow

The normal status work flow for a Bug or Feature request is New -> Assigned -> In Code Review -> In Test -> Closed.

**New** - The issue has been created, and there is not a particular person assigned to address the issue. In this case, the Issue Administrator (currently Amber) will review the new issue and assign it to the appropriate person.

**Assigned** - The issue has been assigned to someone. That person is responsible for addressing the issue. If it is a Bug, this person will fix it. If it is a feature, this person will implement it. This person will also indicate in the issue how their changes should be tested.

**In Code Review** - The person responsible for fixing or implementing the feature has completed the job and has checked the code into subversion. It is now ready for a code review. The person the issue was assigned to selects another person to perform a code review. The Assigned To field of the issue is changed to the person who will perform the code review.

**In Test** - The code has been reviewed and any potential problems have been addressed. Someone other than the person who implemented the code change is assigned to test the change. The person who implemented the change should indicate which Test Cases can be used to test the code changes.

**Closed** -> All testing of the code change is complete and successful.

There are several cases where the normal work flow will not apply:

**Duplicate** - indicates that there is already an issue addressing the same topic. In this case, be sure to make a reference to the existing issue.
**Wont Fix / Wont Do** - indicates that the bug or feature request will be ignored. Please provide a detailed explanation for making this choice.

[Good guide from Drupal, we could incorporate](http://drupal.org/node/73179)
