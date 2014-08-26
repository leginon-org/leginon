<?php
/**
 * The Leginon software is Copyright 2003 
 * The Scripps Research Institute, La Jolla, CA
 * For terms of the license agreement
 * see	http://ami.scripps.edu/software/leginon-license
 *
 * Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

if ($_POST['process']) {
	// If values submitted, evaluate data
	runRctVolume();
} else {
	// Create the form page
	createRctVolumeForm();
}

/*
**
** RCT VOLUME FORM
**
*/
function createRctVolumeForm($extra=false, $title='rctVolume.py Launcher', $heading='Run RCT Volume') {
	$expId=$_GET['expId'];
	$projectId=getProjectId();

	$alignid = $_GET['alignid'];
	$clusterid = $_GET['clusterid'];
	$classnum = $_GET['classnum'];

	// save other params to url formaction
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$formAction.=($classnum) ? "&classnum=$classnum" : "";
	$formAction.=($alignid) ? "&alignid=$alignid" : "";
	$formAction.=($clusterid) ? "&clusterid=$clusterid" : "";

	// Set any existing parameters in form
	$description = $_POST['description'];
	$tiltstack = ($_POST['tiltstack']) ? $_POST['tiltstack'] : '';
	$maskrad = ($_POST['maskrad']) ? $_POST['maskrad'] : '';
	$lowpassvol = ($_POST['lowpassvol']) ? $_POST['lowpassvol'] : '10';
	$highpasspart = ($_POST['highpasspart']) ? $_POST['highpasspart'] : '800';
	$lowpasspart = ($_POST['lowpasspart']) ? $_POST['lowpasspart'] : '0';
	$median = ($_POST['median']) ? $_POST['median'] : '3';
	$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '3';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '';
	$minscore = ($_POST['minscore']) ? $_POST['minscore'] : '';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '0.9';
	$contour = ($_POST['contour']) ? $_POST['contour'] : '3.0';
	$mass = ($_POST['mass']) ? $_POST['mass'] : '';

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$sessionpath=getBaseAppionPath($sessioninfo).'/rctvolume/';
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;

	$javascript  = "";
	$javascript .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' VALUE='$sessionname'>\n";
	}

	//query the database for parameters
	$particle = new particledata();
	$numRctRuns = $particle->getNumberOfRctRuns($sessionId, True);
	while (glob($sessionpathval.'rct'.($numRctRuns+1)."[a-z]*"))
		$numRctRuns += 1;
	$defrctname = 'rct'.($numRctRuns+1);
	if ($alignid)
		$defrctname .= "align".$alignid;
	elseif ($clusterid)
		$defrctname .= "clust".$clusterid;
	if ($classnum!="") {
		$classstr = preg_replace("%,%","",$classnum);
		$defrctname .= "class".$classstr;
	}	else {
		$defrctname .= "run";
	}
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrctname;

	echo"<TABLE BORDER=3 CLASS=tableborder>";
	echo"<TR><TD VALIGN='TOP'>\n";

	//Rct Run Name
	echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";

	echo openRoundBorder();
	echo docpop('runname','<b>Rct Volume Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Rct Volume run:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
	echo closeRoundBorder();

	echo "</td></tr></table>\n";

	echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";

	if ($_GET['alignid']) {
		//Case 1: Align Id Selected
		echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";
		echo openRoundBorder();
		echo alignstacksummarytable($_GET['alignid'], $mini=true);
		echo closeRoundBorder();
		echo "<INPUT type='hidden' name='stack' value='align".$_GET['alignid']."'>\n";
		echo "</td></tr></table>\n";
	} elseif ($_GET['clusterid']) {
		//Case 2: Cluster Id Selected
		echo openRoundBorder();
		echo clustersummarytable($_GET['clusterid']);
		echo closeRoundBorder();
		echo "<INPUT type='hidden' name='stack' value='clust".$_GET['clusterid']."'>\n";
	} else {
		//Case 3: Drop Down Menus
		$alignids = $particle->getAlignStackIds($expId);
		if ($alignids) {
			echo "<SELECT name='stack'>\n";
			foreach ($alignids as $aligniddata){
				$alignid = $aligniddata['alignstackid'];
				$aligndata = $particle->getAlignStackParams($alignid);
				$runname  = $aligndata['name'];
				$numclass = $particle->getNumAlignStackReferences($alignid);
				$descript = substr($aligndata['description'],0,40);
				echo "<OPTION value='align$alignid'";
				if ($alignid == $_POST['alignid']) echo " SELECTED";
				echo">Align $alignid: $runname ";
				if ($numclass > 0)
					echo "($numclass refs) ";
				echo "$descript...</OPTION>\n";
				$clusterids = $particle->getClusteringStacksForAlignStack($alignid);
				if ($clusterids) {
					foreach ($clusterids as $clusteriddata){
						$clusterid = $clusteriddata['clusterid'];
						$clusterdata = $particle->getClusteringStackParams($clusterid);
						$runname  = $clusterdata['name'];
						$numclass = $clusterdata['num_classes'];
						$descript = substr($clusterdata['description'],0,40);
						echo "<OPTION value='clust$clusterid'";
						if ($clusterid == $_POST['clusterid']) echo " SELECTED";
						echo"> -&gt; Cluster $clusterid: $runname ($numclass classes) $descript...</OPTION>\n";
					}
				}
			}
			echo "</SELECT>\n<br/>\n<br/>\n";
		}
	}

	//Class Numbers
	//echo docpop('classnum','Class Numbers');
	echo 'Class Numbers';
	echo " to generate volume:<br/>";
	if (!$classnum && $classnum != '0') {
		$classnum = '0,1';
		echo "<INPUT type='text' name='classnum' size='5' value='$classnum'>";
		echo "&nbsp;(starts at 0,1,2,...)\n<br/>\n<br/>\n";
	} else {
		echo "<INPUT type='hidden' name='classnum' value='$classnum'>\n";
		echo "<FONT SIZE='+1'>&nbsp;Selected class numbers '<b>$classnum</b>'</FONT> ";
		echo "\n<br/>\n<br/>\n";
	}

	//Tilted stack id
	//echo docpop('stackid','Tilted Stack Id:<br/>');
	echo "Tilted Stack Id:<br/>";
	$stackDatas = $particle->getStackIds($expId);
	echo "<SELECT name='tiltstack'>\n";
	foreach ($stackDatas as $stackdata){
		//print_r($stackdata);
		$stackid = $stackdata['DEF_id'];
		$stackparams = $particle->getStackParams($stackid);
		if (!$stackparams['tiltangle'] ||
		 ($stackparams['tiltangle'] != "notilt" && $stackparams['tiltangle'] != "all")) {
			$descript  = substr($stackparams['description'],0,40);
			#print_r($stackparams);
			$box  = $stackparams['boxsize'];
			$numparts = commafy($particle->getNumStackParticles($stackid));
			//handle multiple runs in stack
			$stackname = $stackparams['shownstackname'];
			//print_r($stackparams[0]);
			echo "<OPTION value='$stackid|$box'";
			if ($stackid == $tiltstack) echo " SELECTED";
			echo">$stackid: $stackname ($box boxsize, $numparts parts) $descript...</OPTION>\n";
		}
	}
	echo "</SELECT>\n";
	echo "</td></tr></table>\n";

	//Second half of the table
	echo "</TD></tr>\n<TR><TD VALIGN='TOP' CLASS='tablebg' WIDTH='100%'>\n";

	echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";

	//Mask radius & boxsize (for error checking)
	echo docpop('rctmask','Mask Radius:<br/>');
	echo "<INPUT TYPE='text' NAME='maskrad' SIZE='5' VALUE='$maskrad'>";
	echo "<FONT SIZE='-2'>(in pixels)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	//Median filter of volume
	echo docpop('medianval','Volume Median Filter:<br/>');
	echo "<INPUT TYPE='text' NAME='median' SIZE='3' VALUE='$median'>\n";
	echo "<FONT SIZE='-2'>(in pixels)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	//Low pass filter of volume
	echo docpop('rctvollp','Volume Low Pass Filter:<br/>');
	echo "<INPUT TYPE='text' NAME='lowpassvol' SIZE='3' VALUE='$lowpassvol'>\n";
	echo "<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	//High pass filter of particles
	echo docpop('rctparthp','Particle High Pass Filter:<br/>');
	echo "<INPUT TYPE='text' NAME='highpasspart' SIZE='5' VALUE='$highpasspart'>\n";
	echo "<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	//Low pass filter of particles
	echo docpop('rctpartlp','Particle Low Pass Filter:<br/>');
	echo "<INPUT TYPE='text' NAME='lowpasspart' SIZE='5' VALUE='$lowpasspart'>\n";
	echo "<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	if ($_GET['alignid'] || $_GET['clusterid']) {
		//Minimum score cutoff
		echo docpop('minscore','Min Score/Spread cutoff:<br/>');
		echo "<INPUT TYPE='text' NAME='minscore' SIZE='5' VALUE='$minscore'>\n";
		echo "<FONT SIZE='-2'>(see graph)</FONT>\n";
		echo "\n<br/>\n<br/>\n";
	}

	//Number of particles
	echo docpop('numpart','Number of Particles:<br/>');
	echo "<INPUT TYPE='text' NAME='numpart' SIZE='2' VALUE='$numpart'>\n";
	echo "\n<br/>\n<br/>\n";

	//Number of iterations
	echo docpop('rctcenter','Number of Particle centering iterations:<br/>');
	echo "<INPUT TYPE='text' NAME='numiter' SIZE='2' VALUE='$numiter'>\n";
	echo "\n<br/>\n<br/>\n";

	//Chimera settings
	echo "<u>Chimera snapshot settings:</u><br/>";
	echo "<i>Contour:</i>\n&nbsp;\n";
	echo "<INPUT TYPE='text' NAME='contour' SIZE='3' VALUE='$contour'>\n&nbsp;\n";
	echo "<i>Zoom:</i>\n&nbsp;\n";
	echo "<INPUT TYPE='text' NAME='zoom' SIZE='3' VALUE='$zoom'>\n&nbsp;\n";
	echo "<i>Mass:</i>\n&nbsp;\n";
	echo "<INPUT TYPE='text' NAME='mass' SIZE='3' VALUE='$mass'> kDa\n";

	echo "</td></tr></table>\n";

	//Finish up
	echo "</TD></tr><TR><TD ALIGN='CENTER'><hr/>\n";
	echo getSubmitForm("Rct Volume");
	echo "</td></tr></table></form>\n";

	echo spiderRef();

	processing_footer();
	exit;
}

/*
**
** RCT VOLUME RUN
**
*/

function runRctVolume() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$maskrad = $_POST['maskrad'];
	$lowpassvol = $_POST['lowpassvol'];
	$highpasspart = $_POST['highpasspart'];
	$lowpasspart = $_POST['lowpasspart'];
	$median = $_POST['median'];
	$numiter = $_POST['numiter'];
	$numpart = $_POST['numpart'];
	$classnum = $_POST['classnum'];
	$description=$_POST['description'];
	$stack=$_POST['stack'];
	$minscore=$_POST['minscore'];
	$contour=$_POST['contour'];
	$mass=$_POST['mass'];
	$zoom=$_POST['zoom'];

	$stackparams = explode("|",$_POST['tiltstack']);
	$tiltstack = $stackparams[0];
	$box = $stackparams[1];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$tiltstack)
		createRctVolumeForm("<B>ERROR:</B> No tilted stack selected");

	if (!$stack)
		createRctVolumeForm("<B>ERROR:</B> No align or cluster stack selected");

	if (!$classnum && $classnum!='0')
		createRctVolumeForm("<B>ERROR:</B> Class numbers were not provided");

	if (!$description)
		createRctVolumeForm("<B>ERROR:</B> Enter a brief description of the rct volume");

	if (!$maskrad)
		createRctVolumeForm("<B>ERROR:</B> Enter a mask radius");

	if ((intval($box)/2-intval($maskrad))<2)
		createRctVolumeForm("<B>ERROR:</B> Mask radius needs to be at least 2 pixels smaller than 1/2*boxsize; SPIDER error will result otherwise");

	if (!$runname)
		createRctVolumeForm("<B>ERROR:</B> Enter a unique run name");

	if (!$stack)
		createRctVolumeForm("<B>ERROR:</B> No alignment selected");

	if (substr($stack,0,5) == "align")
		$alignid = (int) substr($stack,5);
	elseif (substr($stack,0,5) == "clust")
		$clusterid = (int) substr($stack,5);

	$particle = new particledata();
	$stackparam = $particle->getStackParams($tiltstack);
	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	/* *******************
	PART 3: Create program command
	******************** */
	//putting together command
	$command ="rctVolume.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--description=\"$description\" ";
	$command.="--rundir=$rundir ";
	$command.="--runname=$runname ";
	if ($alignid)
		$command.="--align-id=$alignid ";
	elseif ($clusterid)
		$command.="--cluster-id=$clusterid ";
	$command.="--classnums=$classnum ";
	$command.="--tilt-stack=$tiltstack ";
	$command.="--mask-rad=$maskrad ";
	$command.="--num-iters=$numiter ";
	if ($numpart)
		$command.="--num-part=$numpart ";
	$command.="--zoom=$zoom ";
	if ($mass)
		$command.="--mass=$mass ";
	else
		$command.="--contour=$contour ";
	$command.="--lowpassvol=$lowpassvol ";
	if ($highpasspart && $highpasspart > 0)
		$command.="--highpasspart=$highpasspart ";
	if ($lowpasspart && $lowpasspart > 0)
		$command.="--lowpasspart=$lowpasspart ";
	$command.="--median=$median ";
	if ($minscore)
		$command.="--min-score=$minscore ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= spiderRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// Setting the nodes and ppn per issue #2274
	$nproc = 4;
	$nodes = 1;
	$ppn = 4;

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'rctvolume', $nproc, $testimg=False, $nodes, $ppn);

	// if error display them
	if ($errors)
		createRctVolumeForm("<b>ERROR:</b> $errors");
}

?>
