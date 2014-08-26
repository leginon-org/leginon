<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

$particle = new particledata();
$expId = $_GET['expId'];
$projectId = getProjectId();

/*********************************
Show stack function is an recursive function to
show stack info for the input stack and all of its child stacks
*********************************/
function showStack($stackdata) {
	global $particle;
	global $expId;
	// allstackids contains all the stack ids associated with exp 
	global $allstackIdList;

	$stackid = $stackdata['stackid'];
	// remove this stackid from the list of all stackids
	foreach ($allstackIdList as $key => $value) {
		if ($allstackIdList[$key]['stackid']==$stackid) {
			unset($allstackIdList[$key]);
			break;
		}
	}

	// get all substackd including hidden ones
	$allsubstackdatas = $particle->getSubStackIds($expId, $stackid, true);
	// get only unhidden substackd
	$substackdatas = $particle->getSubStackIds($expId, $stackid);

	// show main stack info
	if ($stackdata['hidden'] != 1 || $_POST['unhideItem'.$stackid] == 'unhide') {
		// if stack is not hidden
		if($substackdatas) {
			//if has children, show mini version of stack info
			echo stacksummarytable($stackid, true); 
		} else {
			//if has no children, show full version of stack info
			echo stacksummarytable($stackid); 
		}
	} else {
		// if stack is hidden, show tiny version of stack info
		echo stacksummarytable($stackid, true, true);
	}

	if ($allsubstackdatas) {
		// for each child stack, recursively run this function within table
		echo "</td></tr><tr><td valign='center'>substack<br/>&ndash;&ndash;&gt;</td><td>";
		echo "<table class='tablebubble'><tr><td colspan='2'>\n";
		foreach ($allsubstackdatas as $substackdata) {
			showStack($substackdata);
		}
		echo "</td></tr></table>\n";
	}
};


/*********************************
MAIN PAGE
*********************************/
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

// add java code to hide/unhide stacks
$javascript.= editTextJava();

// write page header
processing_header("Hierarchical Stack Summary","Hierarchical Stack Summary Page", $javascript, False);
echo "<a href='stacksummary.php?expId=$expId'>[Show original stack summary page]</a><br/><br/>\n";

// get all stack ID's, regardless position in hierarchy
$allstackIdList = $particle->getStackIds($expId, $showHidden=True);
// sort array of stacks by stackid
usort($allstackIdList,'cmp');
// get primary stack data
$allstackdatas = $particle->getPrimaryStackIds($expId);

if ($allstackdatas || $allstackIdList) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	foreach ($allstackdatas as $stackdata) {
		echo "<table class='tablebubble'><tr><td colspan='2'>\n";
		showStack($stackdata);
		echo "</td></tr></table>\n";
	}
	// check if there are orphaned stacks
	if (count($allstackIdList)>0){
		foreach ($allstackIdList as $stackdata) {
			if (in_array($stackdata,$allstackIdList)) {
				echo "<table class='tablebubble'><tr><td colspan='2'>\n";
				showStack($stackdata);
				echo "</td></tr></table>\n";
			}
		}
	}
	echo "</form>";
} else {
	echo "<B><font size='+1'>Session does not contain any stacks.<br/>"
		."Create one here: <a href='runMakeStack2.php?expId=$expId'>make stack</a></font></B>\n";
}

echo "<a href='stacksummary.php?expId=$expId'>[Show original stack summary page]</a><br/><br/>\n";
processing_footer();
exit;

// for sorting the stacks by stackid
function cmp($stacka,$stackb) {
	if ($stacka['stackid'] == $stackb['stackid']) return 0;
	return ($stacka['stackid'] < $stackb['stackid']) ? -1:1;
}
?>
