<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runCtfFind();
}
// CREATE FORM PAGE
else {
	createCtfFindForm();
}

// --- parse data and process on submit
function runCtfFind() {

	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	// ctffind or ctftilt
	$ctftilt = $_GET['ctftilt'];
	if (!$ctftilt) $ctftilt = ($_POST['runctftilt']=='on') ? True : '';
	
	// parse params
	$ampcarbon=$_POST['ampcarbon'];
	$ampice=$_POST['ampice'];
	$fieldsize=$_POST['fieldsize'];
	$medium=$_POST['medium'];
	$binval=$_POST['binval'];
	$resmin=$_POST['resmin'];
	$resmax=$_POST['resmax'];
	$defstep=$_POST['defstep'];
	$numstep=$_POST['numstep'];
	$dast=$_POST['dast'];
	$nominal= ( $_POST['nominal'] == 'db value') ? false: abs($_POST['nominal']);
	//$reprocess=$_POST['reprocess'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	$leginondata = new leginondata();
	if ($leginondata->getCsValueFromSession($expId) === false) {
		createCtfFindForm("Cs value of the images in this session is not unique or known, can't process");
		exit;
	}
	// Error checking:
	if (!$fieldsize) createCtfFindForm("Enter a fieldsize");
	if (!$defstep) createCtfFindForm("Enter a search step");
	if (!$numstep) createCtfFindForm("Enter a number of steps");
	if ($numstep > 250) createCtfFindForm("Too many steps in search, maximum of 250 ");
	if (!$resmin) createCtfFindForm("Enter a minimum resolution");
	//minimum resolution for 4k image with 1.5 Apix is: 1.5*4096 = 6144, go with 5000
	if ($resmin>5000) createCtfFindForm("Minimum resolution is too high, maximum of 5000&Aring;");
	if ($resmin<20) createCtfFindForm("Minimum resolution is too low, minimum of 20&Aring;");
	if (!$resmax) createCtfFindForm("Enter a maxmimum resolution");
	if ($resmax>15) createCtfFindForm("Maximum resolution is too high, maximum of 15&Aring;");
	if ($resmax<3) createCtfFindForm("Maximum resolution is too low, minimum of 3&Aring;");
	
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command = "ctfestimate.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createCtfFindForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$command.="--ampcarbon=$ampcarbon ";
	$command.="--ampice=$ampice ";
	$command.="--fieldsize=$fieldsize ";
	$command.="--medium=$medium ";
	$command.="--bin=$binval ";
	$command.="--resmin=$resmin ";
	$command.="--resmax=$resmax ";
	$command.="--defstep=$defstep ";
	$command.="--numstep=$numstep ";
	$command.="--dast=$dast ";
	if ($_POST['bestdb'])
		$command.=" --bestdb ";		
	

	$progname = "CtfFind";
	if ($ctftilt) {
		$command.="--ctftilt ";
		$progname = "CtfTilt";
	}
	if ($nominal) $command.=" --nominal=$nominal";
	//if ($reprocess) $command.=" reprocess=$reprocess";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= referenceBox("Accurate determination of local defocus and specimen tilt in electron microscopy.", 2003, "Mindell, JA, Grigorieff N.", "J Struct Biol.", 142, 3, 12781660, false, false, "img/grigorieff_lab.png");
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$nproc = 1;
	$errors = showOrSubmitCommand($command, $headinfo, 'ctfestimate', $nproc);

	// if error display them
	if ($errors)
		createCtfFindForm("<b>ERROR:</b> $errors");
}


/*
**
**
** CtfFind FORM
**
**
*/

// CREATE FORM PAGE
function createCtfFindForm($extra=false) {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=getProjectId();

	// check if running ctffind or ctftilt
	$progname = "CtfFind";
	$runbase = "ctffind";
	$ctftilt = $_GET['ctftilt'];
	if ($ctftilt) {
		$progname = "CtfTilt";
		$runbase = "ctftilt";
		$formAction .= "&ctftilt=True";
	}

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions = "";
	$javafunctions .= writeJavaPopupFunctions('appion');
	$javafunctions .= "<script>
		function carbon_preset(obj) {
		  obj.resmin.value = '40';
		  obj.resmax.value = '8';
		  obj.medium[0].checked = true;
		  obj.medium[1].checked = false;
		  obj.defstep.value = 1000;
		  return;
		}
		function ice_preset(obj) {
		  obj.resmin.value = '100';
		  obj.resmax.value = '10';
		  obj.medium[0].checked = false;
		  obj.medium[1].checked = true;
		  obj.defstep.value = 1000;
		  return;
		}
		function finetune_preset(obj) {
		  obj.resmin.value = '100';
		  obj.resmax.value = '10';
		  obj.defstep.value = 100;
		  return;
		}
		function bestdbChange(obj) {
			if (obj.bestdb.checked) {
				obj.ampice.style.backgroundColor = '#bbbbbb';		
				obj.ampcarbon.style.backgroundColor = '#bbbbbb';
				obj.resmax.style.backgroundColor = '#bbbbbb';
				obj.dast.style.backgroundColor = '#bbbbbb';
			} else {
				obj.ampice.style.backgroundColor = '#ffffff';		
				obj.ampcarbon.style.backgroundColor = '#ffffff';
				obj.resmax.style.backgroundColor = '#ffffff';
				obj.dast.style.backgroundColor = '#ffffff';
			}			
		  return;
		}		
		function updateDFsearch() {
		  var dstep = parseFloat(document.getElementById('defstep').value);
		  var numstep = parseFloat(document.getElementById('numstep').value);
		  var range = dstep*numstep*1e-4;
		  range = (range).toFixed(2);
		  document.getElementById('srange').innerHTML=range;
		}
		</script>";

	processing_header("$progname Launcher", "CTF Estimation by $progname", $javafunctions);


	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	} elseif ($ctftilt) {
		echo "<font color='#bb8800' size='+1'>WARNING: CtfTilt is very slow and "
			."you cannot use the tilt angle or astigmatism results in makestack</font><br/><br/>\n";
	}

	echo"
	<form name='viewerform' method='POST' action='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/ctf/';
	}
	$ctf = new particledata();
	$lastrunnumber = $ctf->getLastRunNumberForType($sessionId,'ApAceRunData','name');
	while (file_exists($sessionpath.$runbase.'run'.($lastrunnumber+1)))
		$lastrunnumber += 1;
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : $runbase.'run'.($lastrunnumber+1);

	// set defaults and check posted values
	$form_fieldsz = ($_POST['fieldsize']) ? $_POST['fieldsize'] : 512;
	$form_bin = ($_POST['binval']) ? $_POST['binval'] : 2;
	$form_ampc = ($_POST['ampcarbon']) ? $_POST['ampcarbon'] : '0.15';
	$form_ampi = ($_POST['ampice']) ? $_POST['ampice'] : '0.07';
	$form_resmin = ($_POST['resmin']) ? $_POST['resmin'] : '100';
	$form_resmax = ($_POST['resmax']) ? $_POST['resmax'] : '10';

	$form_defstep = ($_POST['defstep']) ? $_POST['defstep'] : '1000';
	$form_numstep = ($_POST['numstep']) ? $_POST['numstep'] : '25';
	// check if ctftilt is set
	$ctftiltcheck = ($_POST['runctftilt']=='on') ? 'CHECKED' : '';
	$form_dast = ($_POST['dast']) ? $_POST['dast'] : '500';

	$form_nominal = ($_POST['nominal']) ? $_POST['nominal']: 'db value';
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";

	createAppionLoopTable($sessiondata, $defrunname, "ctf");
	// give user option to run ctftilt (useful for film data)


	echo"</TD>\n<TD CLASS='tablebg'>\n";

	if (!$ctftilt) { 
		echo "<input type='checkbox' name='runctftilt' $ctftiltcheck>\n";
		echo docpop('ctftilt','Run CtfTilt');
		echo ", instead of CtfFind<br/><br/>\n";
	}
	echo docpop('medium','<b>Medium:</b>');
	echo "<br/>
	    <INPUT TYPE='radio' NAME='medium' VALUE='carbon'>&nbsp;carbon&nbsp;&nbsp;
	    <INPUT TYPE='radio' NAME='medium' VALUE='ice' checked>&nbsp;ice<br/>
	    <br/>\n";

	echo docpop('ampcontrast','<b>Amplitude Contrast:</b>');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='ampcarbon' VALUE='$form_ampc' SIZE='4'>\n";
	echo "Carbon<br />\n";
	echo "<INPUT TYPE='text' NAME='ampice' VALUE='$form_ampi' SIZE='4'>\n";
	echo "Ice\n";
	echo "<br/><br/>\n";

	echo "<INPUT TYPE='text' NAME='binval' VALUE='$form_bin' SIZE='4'>\n";
	echo docpop('binval','Pre-Binning');
	echo "<br/><br/>\n";
	
	if ($lastrunnumber > 1) {
		echo "<input type='checkbox' name='bestdb' $bestdbcheck onClick='bestdbChange(this.form)'>\n";
		echo docpop('ctffindBestdb','Use best values from DB');
	} else {
		echo "<i>Use best values from DB is not available"
			."<br/>($lastrunnumber ctf runs)</i>\n";
	}
	echo "<br />\n";
	echo "<B>Override nominal defocus set in experiment:</B><br />\n";
	echo "Set to:<INPUT TYPE='text' NAME='nominal' VALUE='".$form_nominal."' SIZE='8'>\n";
	echo "<FONT SIZE=-2><I>(in &mu;m, i.e. <B>2.0</B>)</I></FONT><br />";

	echo "<br/><br/>\n";

	echo "<b>$progname Values</b><br/>\n";
	echo "<INPUT TYPE='text' NAME='fieldsize' VALUE='$form_fieldsz' size='6'>\n";
	echo docpop('field','Field Size');
	echo "(pixels)<br />\n";
	echo "<input type='text' name='resmin' value='$form_resmin' size='6'>\n";
	echo docpop('resmin','Minimum Resolution');
	echo " (&Aring;ngstroms)<br />\n";
	echo "<input type='text' name='resmax' value='$form_resmax' size='6'>\n";
	echo docpop('resmax','Maximum Resolution');
	echo " (&Aring;ngstroms)<br />\n";
	echo "<br />\n";
	echo "<input type='text' id='defstep' name='defstep' "
		."value='$form_defstep' size='6' onChange='updateDFsearch()'>\n";
	echo docpop('defstep','Defocus search step size');
	echo " (&Aring;ngstroms)<br />\n";
	echo "<input type='text' id='numstep' name='numstep' "
		."value='$form_numstep' size='6' onChange='updateDFsearch()'>\n";
	echo docpop('numstep','Number of steps to search');
	echo "<br />\n";
	echo "Search range: &plusmn; <span id='srange'>";
	echo round($form_defstep*$form_numstep*1e-4,2);
	echo "</span>&micro;m<br><br>\n";
	echo "<input type='text' name='dast' value='$form_dast' size='6'>\n";
	echo docpop('dast','Expected astigmatism');
	echo " (&Aring;ngstroms)<br />\n";

	echo "<br />\n";


	echo "<b>PRESET VALUES:</b>";
	echo "<table border='0'><tr><td>\n";
	echo "<input type='button' onClick='carbon_preset(this.form)' 
		value='Carbon Initial Search'>";
	echo "</td></tr><tr><td>\n";
	echo "<input type='button' onClick='ice_preset(this.form)' 
		value='Ice Initial Search'>";
	echo "</td></tr><tr><td>\n";
	echo "<input type='button' onClick='finetune_preset(this.form)' 
		value='Fine Tune Previous Run'>";
	echo "</td></tr></table>\n";

	//echo "<INPUT TYPE='checkbox' NAME='confcheck' onclick='enableconf(this)'>\n";
	//echo "Reprocess Below Confidence Value<br />\n";
	//echo "Set Value:<INPUT TYPE='text' NAME='reprocess' DISABLED VALUE='0.8' SIZE='4'>\n";
	//echo "<FONT SIZE=-2><I>(between 0.0 - 1.0)</I></FONT><br />\n";

	echo"
	  </TD>
	</tr>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run $progname");
	echo "
	  </td>
	</tr>
	</table>
	</form>\n";

	echo referenceBox("Accurate determination of local defocus and specimen tilt in electron microscopy.", 2003, "Mindell, JA, Grigorieff N.", "J Struct Biol.", 142, 3, 12781660, false, false, "img/grigorieff_lab.png");

	processing_footer();
}

?>
