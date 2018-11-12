<?php
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Simple viewer to view a image using mrcmodule
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runTopolAlign();
} else {
	createTopolAlignForm();
}

function createTopolAlignForm($extra=false, $title='topologyAlignment.py Launcher', $heading='Topology Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF'];
	}

	// connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set mask radius
	$javascript .= "	var mask = Math.floor((stackArray[2]/2)-2);\n";
	$javascript .= "	document.viewerform.mask.value = mask;\n";
	// set starting & ending # of classes
	$javascript .= "	var strcls = Math.ceil(Math.sqrt(stackArray[3])/4);\n";
	$javascript .= "	var endcls = Math.ceil(Math.sqrt(stackArray[3]));\n";
	$javascript .= "	document.viewerform.startnumcls.value = strcls;\n";
	$javascript .= "	document.viewerform.endnumcls.value = endcls;\n";
	$javascript .= "	estimatetime();\n";
	$javascript .= "}\n";
	$javascript .= "
		function estimatetime() {
			var secperiter = 0.001;
			var stackval = document.viewerform.stackval.value;
			var stackArray = stackval.split('|--|');
			var numpart = document.viewerform.numpart.value;
			var boxsize = stackArray[2];
			var numpix = Math.pow(boxsize/document.viewerform.bin.value, 2);
		}\n";
#			var calctime = (numpart/1000.0) * document.viewerform.startnumcls.value * numpix * secperiter / (document.viewerform.nproc.value - 1);
#			if (calctime < 70) {
#				var time = Math.round(calctime*100.0)/100.0
#				document.viewerform.timeestimate.value = time.toString()+' seconds';
#			} else if (calctime < 3700) {
#				var time = Math.round(calctime*0.6)/100.0
#				document.viewerform.timeestimate.value = time.toString()+' minutes';
#			} else if (calctime < 3700*24) {
#				var time = Math.round(calctime/36.0)/100.0
#				document.viewerform.timeestimate.value = time.toString()+' hours';
#			} else {
#				var time = Math.round(calctime/36.0/24.0)/100.0
#				document.viewerform.timeestimate.value = time.toString()+' days';
#			}
#		}\n";

	// toggle MSA params
	$javascript .="function chooseMSA(package) {\n";
	$javascript .="  if (package == 'CAN') {\n";
	$javascript .="    document.viewerform.msamethod.value='can';\n";
	$javascript .="    document.getElementById('canbutton').style.border='1px solid #0F0';\n";
	$javascript .="    document.getElementById('canbutton').style.backgroundColor='#CCFFCC';\n";
	$javascript .="    document.getElementById('canparams').style.display = 'block';\n";
	$javascript .="    document.getElementById('imagicbutton').style.border='1px solid #F00';\n";
	$javascript .="    document.getElementById('imagicbutton').style.backgroundColor='#C0C0C0';\n";
	$javascript .="    document.getElementById('imagicparams').style.display = 'none';\n";
	$javascript .="  }\n";
	$javascript .="  if (package == 'IMAGIC') {\n";
	$javascript .="    document.viewerform.msamethod.value='imagic';\n";
	$javascript .="    document.getElementById('canbutton').style.border='1px solid #F00';\n";
	$javascript .="    document.getElementById('canbutton').style.backgroundColor='#C0C0C0';\n";
	$javascript .="    document.getElementById('canparams').style.display = 'none';\n";
	$javascript .="    document.getElementById('imagicbutton').style.border='1px solid #0F0';\n";
	$javascript .="    document.getElementById('imagicbutton').style.backgroundColor='#CCFFCC';\n";
	$javascript .="    document.getElementById('imagicparams').style.display = 'block';\n";
	$javascript .="  }\n";
	$javascript .="}\n";

	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<form name='viewerform' method='POST' action='$formAction' onsubmit='return checkform()'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$sessionpath=getBaseAppionPath($sessioninfo).'/align/';

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'topol'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'topol'.($alignruns+1);
	$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = preg_split('%\|--\|%',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$startnumcls = ($_POST['startnumcls']) ? $_POST['startnumcls'] : $numpart/30;
	$endnumcls = ($_POST['endnumcls']) ? $_POST['endnumcls'] : $numpart/50;
	$mask = ($_POST['mask']) ? $_POST['mask'] : 100;
	$premaskcheck = ($_POST['premask']=='on') ? 'checked' : '';
	$nocentercheck = ($_POST['nocenter']=='on') ? 'checked' : '';
	$nomaskcheck = ($_POST['nomask']=='on') ? 'checked' : '';
	$classitercheck = ($_POST['classiter']=='on') ? 'checked' : '';
	$iter = (isset($_POST['iter'])) ? $_POST['iter'] : '5';
	// topology alignment parameters
	$itermult = ($_POST['itermult']) ? $_POST['itermult'] : '10';
	$learn = ($_POST['learn']) ? $_POST['learn'] : '0.01';
	$ilearn = ($_POST['ilearn']) ? $_POST['ilearn'] : '0.0005';
	$age = ($_POST['age']) ? $_POST['age'] : '25';
	// IMAGIC MSA parameters
	$eigen = ($_POST['eigen']) ? $_POST['eigen'] : '69';
	$msaiter = ($_POST['msaiter']) ? $_POST['msaiter'] : '50';
	$overcor = ($_POST['overcor']) ? $_POST['overcor'] : '0.8';
	$activeeigen = ($_POST['activeeigen']) ? $_POST['activeeigen'] : '10';
	$msamethod = ($_POST['msamethod']) ? $_POST['msamethod'] : 'can';

	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>Topology Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Topology Alignment:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";

	if (!$stackIds) {
		echo "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
	} else {
		echo docpop('stack','<b>Select a stack of particles to use</b>');
		echo "<br/>";
		$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
	}
	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></tr>\n";
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br>";

	echo "</TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE cellpading='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	//echo "<B>Particle Params:</B></A><br>\n";

	echo "<b>Filters</b>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass' onChange='estimatetime()'>\n";
	echo docpop('lpstackval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass' onChange='estimatetime()'>\n";
	echo docpop('hpstackval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('partbin','Particle binning');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='mask' VALUE='$mask' SIZE='4'>\n";
	echo docpop('mask','Mask (in pixels, unbinned)');
	echo "<br/>\n";
	echo "<INPUT TYPE='checkbox' name='premask' $premaskcheck>\n";
	echo docpop('premask','Mask raw particles');	
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<b>Job Parameters</b>\n";
	echo "<br/>\n";
	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='startnumcls' VALUE='$startnumcls' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('startnumcls','Starting # of classes');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='endnumcls' VALUE='$endnumcls' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('endnumcls','Ending # of classes');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='iter' VALUE='$iter' SIZE='4'>\n";
	echo docpop('topoliter','Number of iterations');
	echo "<br/>\n";

	echo "<br/>\n";

	echo "<b>MSA Package:</b><br>\n";
	$onstyle = "font-size: 12px; border: 1px solid #0F0; background-color: #CCFFCC";
	$offstyle = "font-size: 12px; border: 1px solid #F00";

	$canstyle = ($msamethod=='can') ? $onstyle : $offstyle;
	$imgstyle = ($msamethod=='imagic') ? $onstyle : $offstyle;
	echo "<input id='canbutton' style='$canstyle' type='button' value='CAN' onclick='chooseMSA(\"CAN\")'>\n";
	echo "<input id='imagicbutton' style='$imgstyle' type='button' value='IMAGIC' onclick='chooseMSA(\"IMAGIC\")'>\n";
	echo "<br>\n";
	echo "<br>\n";

	// hidden input for package
	echo "<input type='hidden' name='msamethod' value='$msamethod'>\n";

	// MSA parameters for CAN classification 
	echo "<div id='canparams'";
	if ($msamethod=='imagic') echo " style='display:none'";
	echo ">\n";
	echo "<b>CAN Parameters</b><br/>\n";
	echo "<input type='text' name='itermult' value='$itermult' size='4'>\n";
	echo docpop('itermult','Iteration multiplier');
	echo "<br/>\n";

	echo "<input type='text' name='learn' value='$learn' size='4'>\n";
	echo docpop('learn','Direct learning rate');
	echo "<br/>\n";

	echo "<input type='text' name='ilearn' value='$ilearn' size='4'>\n";
	echo docpop('ilearn','Indirect learning rate');
	echo "<br/>\n";

	echo "<input type='text' name='age' value='$age' size='4'>\n";
	echo docpop('age','Edge age');
	echo "</div>\n";

	// MSA parameters for IMAGIC MSA
	echo "<div id='imagicparams'";
	if ($msamethod=='can') echo " style='display:none'";
	echo ">\n";
	echo "<b>IMAGIC Parameters</b><br>\n";
	echo "<input type='text' name='eigen' value='$eigen' size='4'>\n";
	echo docpop('numfactor','Number of Eigenimages');
	echo "<br/>\n";

	echo "<input type='text' name='activeeigen' value='$activeeigen' size='4'>\n";
	echo docpop('activeeigen', 'Num of Active Eigenimages');
	echo "<br/>\n";

	echo "<input type='text' name='msaiter' value='$msaiter' size='4'>\n";
	echo docpop('msaiter','MSA iterations');
	echo "<br/>\n";

	echo "<input type='text' name='overcor' value='$overcor' size='4'>\n";
	echo docpop('overcor', 'Overcorrection');
	echo "</div>\n";
	
	echo "<br/>\n";
	echo "<INPUT TYPE='checkbox' name='nocenter' $nocentercheck>\n";
	echo docpop('nocenter','Do not center the class averages');	
	echo "<br/>\n";
	echo "<INPUT TYPE='checkbox' name='nomask' $nomaskcheck>\n";
	echo docpop('nomask','Do not mask the class averages');	
	echo "<br/>\n";
	echo "<INPUT TYPE='checkbox' name='classiter' $classitercheck>\n";
	echo docpop('classiter','Perform iterative class averaging');	
	echo "<br/>\n";

	echo "<br/>\n";
	echo docpop('mramethod','<b>MRA package:</b>');
	echo "<br/>\n";

	if (!HIDE_IMAGIC)
		$mramethods=array('IMAGIC', 'EMAN');
	else
		$mramethods=array('EMAN',);

	echo "<select name='mramethod'>\n";
	foreach ($mramethods as $mra){
		echo "<option";
		if ($_POST['mramethod']==$mra) echo " selected";
		echo ">$mra</option>\n";
	}
	echo "</select>\n";
	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
#	echo "Time estimate for first iteration: ";
#	echo "<INPUT TYPE='text' NAME='timeestimate' SIZE='16' onFocus='this.form.elements[0].focus()'>\n";
#	echo "<br/>\n";
	echo getSubmitForm("Run Topology Alignment");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	echo referenceBox("Topology representing network enables highly accurate classification of protein images taken by cryo electron-microscope without masking.", 2003, "Ogura T, Iwasaki K, Sato C.", "J Struct Biol.", 143, 3, 14572474, false, false, "img/canimg.png");

	processing_footer();
	exit;
}

function runTopolAlign() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackval=$_POST['stackval'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$startnumcls = $_POST['startnumcls'];
	$endnumcls = $_POST['endnumcls'];
	$iter=$_POST['iter'];
	$bin=$_POST['bin'];
	$mask=$_POST['mask'];
	// CAN params
	$itermult=$_POST['itermult'];
	$learn=$_POST['learn'];
	$ilearn=$_POST['ilearn'];
	$age=$_POST['age'];
	// IMAGIC params
	$eigen = $_POST['eigen'];
	$msaiter = $_POST['msaiter'];
	$overcor = $_POST['overcor'];
	$activeeigen = $_POST['activeeigen'];

	$description=$_POST['description'];
	$commit = ($_POST['commit']=="on") ? true : false;
	$premask = ($_POST['premask']=="on") ? true : false;
	$nocenter = ($_POST['nocenter']=="on") ? true : false;
	$nomask = ($_POST['nomask']=="on") ? true : false;
	$classiter = ($_POST['classiter']=="on") ? true : false;
	$mramethod = strtolower($_POST['mramethod']);
	$msamethod = ($_POST['msamethod']);

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = preg_split('%\|--\|%',$stackval);
	//make sure a session was selected

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	// if mask is bigger than box size, complain
	$maxmsk = ($boxsz/2)-2;
	if ($mask>$maxmsk)
		createTopolAlignForm("<b>Error:</b> Maximum mask size is $maxmsk");
	if (!$description)
		createTopolAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	if (!$stackid)
		createTopolAlignForm("<B>ERROR:</B> No stack selected");

	// classification
	if ($numpart < 10)
		createTopolAlignForm("<B>ERROR:</B> Must have more than 10 particles");

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createTopolAlignForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than the number of particles in the stack ($totprtls)");

	// determine calc time
	$stackdata = $particle->getStackParams($stackid);
	$boxsize = $stackdata['boxsize'];
	$secperiter = 0.0025;
#	$calctime = ($numpart/1000.0)*$startnumcls*($boxsize/$bin)*($boxsize/$bin)*$secperiter/$nproc;

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	/* *******************
	PART 3: Create program command
	******************** */
	// setup command
	$command ="topologyAlignment.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--start=$startnumcls ";
	$command.="--end=$endnumcls ";
	$command.="--bin=$bin ";
	$command.="--mask=$mask ";
	$command.="--iter=$iter ";

	// IMAGIC MSA parameters
	if ($msamethod == 'imagic') {
		$command.="--numeigen=$eigen ";
		$command.="--msaiter=$msaiter ";
		$command.="--overcorrection=$overcor ";
		$command.="--activeeigen=$activeeigen ";
	}
	// CAN parameters
	else {
		$command.="--itermul=$itermult ";
		$command.="--learn=$learn ";
		$command.="--ilearn=$ilearn ";
		$command.="--age=$age ";
	}
	$command.="--mramethod=$mramethod ";
	$command.="--msamethod=$msamethod ";

	if ($premask) $command.="--premask ";
	if ($nocenter) $command.="--no-center ";
	if ($nomask) $command.="--no-mask ";
	if ($classiter) $command.="--classiter ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= referenceBox("Topology representing network enables highly accurate classification of protein images taken by cryo electron-microscope without masking.", 2003, "Ogura T, Iwasaki K, Sato C.", "J Struct Biol.", 143, 3, 14572474, false, false, "img/canimg.png");
#	if ($calctime < 60)
#		$headinfo .= "<span style='font-size: larger; color:#999933;'>\n<b>Estimated calc time:</b> "
#			.round($calctime,2)." seconds\n";
#	elseif ($calctime < 3600)
#		$headinfo .= "<span style='font-size: larger; color:#33bb33;'>\n<b>Estimated calc time:</b> "
#			.round($calctime/60.0,2)." minutes\n";
#	else
#		$headinfo .= "<span style='font-size: larger; color:#bb3333;'>\n<b>Estimated calc time:</b> "
#			.round($calctime/3600.0,2)." hours\n";
	$headinfo .= "</span><br/>";
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign');

	// if error display them
	if ($errors)
		createTopolAlignForm("<b>ERROR:</b> $errors");
	
}
?>
