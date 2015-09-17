<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runSubStack();
}

// Create the form page
else {
	createAlignSubStackForm();
}

function createAlignSubStackForm($extra=false, $title='subStack.py Launcher', $heading='Make a partial Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$clusterId = $_GET['clusterId'];
	$alignId   = $_GET['alignId'];
	if (!$clusterId) $clusterId = $_POST['clusterId'];
	if (!$alignId)   $alignId   = $_POST['alignId'];

	if ($alignId) {
		$defrunname = 'alignsub'.$alignId;
		$formAction .= "&alignId=$alignId";
	} elseif ($clusterId) {
		$defrunname = 'clustersub'.$clusterId;
		$formAction .= "&clusterId=$clusterId";
	} else
		$defrunname = 'alignsubstack1';

	$classfile=$_GET['file'];

	$exclude=$_GET['exclude'];
	$include=$_GET['include'];	

	// save other params to url formaction
	if ($classfile)
		$formAction .= "&file=$classfile";
	if ($stackId)
		$formAction .= "&sId=$stackId";
	if ($exclude)
		$formAction .= "&exclude=$exclude";
	if ($include)
		$formAction .= "&include=$include";

	// Set any existing parameters in form
	if (!$description) $description = $_POST['description'];
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunname;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	$writefilecheck = ($_POST['writefile'] =='on') ? 'checked' : '';
	$savebadcheck = ($_POST['savebad']=='on') ? 'checked' : '';		
	$maxshift = $_POST['maxshift'] ? $_POST['maxshift'] : '';
	$minscore = $_POST['minscore'] ? $_POST['minscore'] : '';

	if (!strlen($exclude)) $exclude = $_POST['exclude'];
	if (!strlen($include)) $include = $_POST['include'];

	// get outdir path
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=getBaseAppionPath($sessioninfo).'/stacks';

	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $outdir;

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	
	//query the database for parameters
	$particle = new particledata();
	
	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";

	$basename = basename($classfile);
	if ($clusterId) {
		$alignId = $particle->getAlignStackIdFromClusterId($clusterId);
		$clusterlink = "viewstack.php?clusterId=$clusterId&expId=$expId&file=$classfile";
		echo"<b>Clustering Run Information:</b> <ul>\n"
			."<li>Stackfile: <a href='$clusterlink'>$basename</a>\n"
			."<li>Cluster Stack ID: $clusterId\n"
			."<li>Align Stack ID: $alignId\n"
			."<input type='hidden' name='clusterId' value='$clusterId'>\n"
			."</ul>\n";
	} else if ($alignId) {
		$alignlink = "viewstack.php?alignId=$alignId&expId=$expId&file=$classfile";
		echo"<b>Alignment Run Information:</b> <ul>\n"
			."<li>Stackfile: <a href='$alignlink'>$basename</a>\n"
			."<li>Align Stack ID: $alignId\n"
			."<input type='hidden' name='alignId' value='$alignId'>\n"
			."</ul>\n";
	} else {
		$alignIds = $particle->getAlignStackIds($expId, false);
		if ($alignIds) {
			echo"
			Select Aligned Stack:<br>
			<select name='alignId''>\n";
			foreach ($alignIds as $alignarray) {
				$alignid = $alignarray['alignstackid'];
				$alignstack = $particle->getAlignStackParams($alignid);

				// get pixel size and box size
				$apix = $alignstack['pixelsize'];
				if ($apix) {
					$mpix = $apix/1E10;
					$apixtxt=format_angstrom_number($mpix)."/pixel";
				}
				$boxsz = $alignstack['boxsize'];
				//handle multiple runs in stack
				$runname=$alignstack['runname'];
				$totprtls=commafy($particle->getNumAlignStackParticles($alignid));
				echo "<OPTION VALUE='$alignid'";
				// select previously set prtl on resubmit
				if ($stackidval==$alignid) echo " SELECTED";
				echo ">$alignid: $runname ($totprtls prtls,";
				if ($mpix) echo " $apixtxt,";
				echo " $boxsz pixels)</OPTION>\n";
			}
			echo "</SELECT>\n";
			echo "<br/>\n";
		} else {
			echo"
			<FONT COLOR='RED'><B>No Aligned Stacks for this Session</B></FONT>\n";
		}
	}

	echo "<hr/><br/>\n";

	if (file_exists($outdir.'/'.$runname)) {
		for ($i=65; $i<=90; $i++) {
			$letter = strtolower(chr($i));
			$newrunname = $runname.$letter;
			if (!file_exists($outdir.'/'.$newrunname))
				break;
		}
		$runname = $newrunname;
	}

	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' value='$runname' size='15'>\n";

	echo "<br/><br/>\n";

	echo docpop('outdir','<b>Output directory:</b>');
	echo "<input type='text' name='outdir' value='$outdir' size='30'>\n";

	echo "<br/><br/>\n";

	echo docpop('maxshift','<b>Maximum alignment shift:</b> ');
	echo "<input type='text' name='maxshift' value='$maxshift'>\n";

	echo "<br/><br/>\n";

	echo docpop('minscore','<b>Minimum alignment score or spread:</b> ');
	echo "<input type='text' name='minscore' value='$minscore'>\n";
	if ($alignId) {
		echo openRoundBorder();
		echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";
		echo alignstacksummarytable($alignId, $mini=true);
		echo "</td></tr></table>\n";
		echo closeRoundBorder();
	}

	echo "<br/><br/>\n";

	// exclude and include
	if (!$_GET['include']) {
		echo docpop('test','<b>Excluded Classes:</b> ');
		echo "<br/>\n<input type='text' name='exclude' value='$exclude' size='38'><br />\n";
	} else
		echo "<input type='hidden' name='exclude' value=''>\n";
	if (!$_GET['exclude']) {
		echo docpop('test','<b>Included Classes:</b> ');
		echo "<br/>\n<input type='text' name='include' value='$include' size='38'><br />\n";
	} else
		echo "<input type='hidden' name='include' value=''>\n";

	echo "<br><input type='checkbox' name='savebad' $savebadcheck>Save discarded particles in a stack\n";
	echo "<br>\n";
	echo "<br>\n";
	echo "<b>Description:</b><br />\n";
	echo "<textarea name='description' rows='2' cols='60'>$description</textarea>\n";
	echo "<br/>\n";
	echo "<br/>\n";
	echo "<input type='checkbox' name='writefile' $writefilecheck>\n";
	echo docpop('writefile','<b>Write file to disk</b>');
	echo "<br/>\n";
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database</b>');
	echo "<br/>\n";
	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo "<br/>\n";
	echo getSubmitForm("Create SubStack");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	echo initModelRef();

	processing_footer();
	exit;
}

function runSubStack() {
	/* *******************
	PART 1: Get variables
	******************** */

	$clusterId=$_POST['clusterId'];
	$alignId=$_POST['alignId'];
	$commit=$_POST['commit'];
	$savebad=$_POST['savebad'];
	$exclude=$_POST['exclude'];
	$include=$_POST['include'];
	$maxshift=$_POST['maxshift'];
	$minscore=$_POST['minscore'];
	$description=$_POST['description'];
	$writefile = $_POST['writefile'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a description is provided
	if (!$description)
		createAlignSubStackForm("<B>ERROR:</B> Enter a brief description");
	if ($include && $exclude)
		createAlignSubStackForm("<B>ERROR:</B> You cannot have both included and excluded classes");
	if (!$include && !$exclude && !is_numeric($include) && !is_numeric($exclude))
		createAlignSubStackForm("<B>ERROR:</B> You must specify one of either included and excluded classes");
	if ($maxshift || $minscore) {
		//query the database for parameters
		$particle = new particledata();
		if ($clusterId)
			$this_alignId = $particle->getAlignStackIdFromClusterId($clusterId);
		if ($alignId) $this_alignId = $alignId;
		$alignparams = $particle->getAlignStackParams ($this_alignId);
		if (strpos($alignparams['package'],'cl2d') !== false) 
			createAlignSubStackForm("<B>ERROR:</B> CL2D method does not output alignment values. You must not specify maximum alignment shift nor minimum score");
	}
	/* *******************
	PART 3: Create program command
	******************** */

	//putting together command
	$command.="alignSubStack.py ";
	$command.="--description=\"$description\" ";
	if ($exclude || is_numeric($exclude))
		$command.="--class-list-drop=$exclude ";
	elseif ($include || is_numeric($include))
		$command.="--class-list-keep=$include ";
	if ($clusterId) {
		$command.="--cluster-id=$clusterId ";
	} elseif ($alignId) {
		$command.="--align-id=$alignId ";
	} else {
		createAlignSubStackForm("<b>ERROR:</b> You need either a cluster Id or align ID");
	}

	if ($minscore)
		$command.="--min-score=$minscore ";
	if ($maxshift)
		$command.="--max-shift=$maxshift ";
	if ($savebad=='on')
		$command .="--save-bad ";
	$command.= ($writefile=='on') ? "--write-file " : "";
	$command.= ($commit=='on') ? "--commit " : "--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= initModelRef(); // main init model ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack', $nproc);

	// if error display them
	if ($errors)
		createAlignSubStackForm($errors);
	exit;
}

?>
