There are a few situations that has different solutions:

## Removing one of the many targets you selected on a single image which you not yet submit for processing:

Right-click with your mouse in the proximity of the target.

## Removing all targets you or the auto-hole finder selected on a single image which you not yet submit for processing:

In most target finder there is a settings window next to the image viewer where you select how the targets are displayed. On the settings of acquisition targets, there is a button on the left-bottom corner for "Clear Targets".

There is also a short-cut key ctrl-shift-right click that will remove all targets like "Clear Targets".

## Removing one of the many targets on a image submitted to the queue or for processing:

Sorry, you can't do that. You have to treat all unprocessed targets selected on the same image in the same way.

## Removing all remaining targets on the image currently being processed (abort):

Click on "Abort" button on the toolbar of the node that is processing the target list.

## Removing all remaining targets on all images in the queue (Queue abort):

Click on "Queue Abort" button on the toolbar of the acquisition node that receives the target queue.
see [Queuing option#Configuration-and-operation-rules-for-a-chosen-queuing-point](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_option#Configuration-and-operation-rules-for-a-chosen-queuing-point) on 'Configuration and operation rules for a chosen queuing point'

## Removing all targets on or derived from an image in the queue (Queue remover):

(a) On a web browser, go to your webserver 3way viewer (probably <http://your_host/myamiweb/3wviewer.php> ).

(b) Select the image that you want to remove queued targets derived from it and its children images so that it is displayed.

© click on the toolbutton above the image displayed that shows a line across the letter Q. This is the Queue remover button.

(d) The window pops up shows how many targets are derived from this image and how many of them are active ( as in will be processed if you let leginon continue its course.

(e) If you are sure that you'd like to remove these all, click on "Remove Active".

Note that this process only works for tagets on targets that are not on the image that is currently processed. You have to follow case 4 if you want to remove those.

-   Example for using this case: You've queued up 3 targets per hole on 50 holes per squares and have done so with 10 squares. Leginon is running happily and collected targets on 4 holes on square 2 and is acquiring images on hole 5 now. By looking at the final images, you decide that not only this square 2 is not worth collecting data but also square 6 and 9 that have the exact appearance as square 2. However, you don't want to abort everything (Case 5) because the rest of the squares look good. Therefore, you go to the webviewer 3wviwer.php, make square 2,6,9 displayed in turn and remove the active targets derived from each of them (total of 3*50*3 - 3*5 of them). Then use case 4 to abort targets on the current image if it is still going on at hole 5.

[< Pausing and Aborting during data collection](/leginon/Leginon_Manual/Trouble_shooting/Pausing_and_Aborting_during_data_collection) | [Aborting targets that are not yet being processed](/leginon/Leginon_Manual/Trouble_shooting/Aborting_targets_that_are_not_yet_being_processed) | [Restarting procedure to continue data acquisition >](/leginon/Leginon_Manual/Trouble_shooting/Restarting_procedure_to_continue_data_acquisition)
