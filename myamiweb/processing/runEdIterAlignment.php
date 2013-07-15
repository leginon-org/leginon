<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Form for starting iterative classification &  alignment of a stack
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
  runAlignment();
}

 // Create the form page
elseif ($_POST['templates']) {
  createAlignmentForm();
}

// Make the template selection form
else {
  createTemplateForm();
}


//***************************************
//***************************************
//***************************************
//***************************************
function createTemplateForm() {
	// check if coming directly from a session
	$expId = $_GET[expId];
	$formAction=$_SERVER['PHP_SELF'];	
	$projectId=getProjectId();

	// retrieve template info from database for this project
	if ($expId){
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}

	$projects=getProjectList();

	if (is_numeric($projectId)) {
		$particle=new particleData;
		$templateData=$particle->getTemplatesFromProject($projectId);
	}

	// extract template info
	if ($templateData) {
		$i=1;
		$templatetable="<br/>\n<TABLE CLASS='tableborder' BORDER='1' CELLPADDING='3'>\n";
		$numtemplates=count($templateData);
		foreach($templateData as $templateinfo) {
			if ($i%2 == 1)
				$templatetable.="<TR><td>\n";
			else
				$templatetable.="<td>\n";
			if (is_array($templateinfo)) {
				$filename = $templateinfo['path'] ."/".$templateinfo['templatename'];
				$checkboxname='template'.$i;
				// create the image template table
				$templatetable.="<img src='loadimg.php?filename=$filename&s=90' WIDTH='90'>\n";
				$templatetable.="</TD><td>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='templateId".$i."' VALUE='$templateinfo[DEF_id]'>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='diam' VALUE='$templateinfo[diam]'>\n";
				$templatetable.="<INPUT TYPE='checkbox' NAME='$checkboxname'>\n";
				$templatetable.="<B>Align to Template ID:</B>  $templateinfo[DEF_id]<br/>\n";
				$templatetable.="<INPUT TYPE='radio' NAME='orientref' value='".$templateinfo['DEF_id']."'";
				if ($i == 1)
					$templatetable.=" CHECKED";
				$templatetable.=">\n";
				$templatetable.="<B>Use as orientation reference</b><br/>\n";
				$templatetable.="Diameter:  $templateinfo[diam]<br>\n";
				$templatetable.="Pixel Size: $templateinfo[apix]<br>\n";
				$templatetable.="File:&nbsp;<I>\n";
				$templatetable.=$templateinfo['templatename']."</I><br/>\n";
				$templatetable.="Description:&nbsp;<I>\n";
				$templatetable.=$templateinfo['description']."</I>\n";
				$i++;
			}
			if ($i%2 == 1)
				$templatetable.="</TD></tr>\n";
			else
				$templatetable.="</TD>\n";
		}
		$templatetable.="</table>\n<br/>\n";
	}

	processing_header("Ed-Iter Template Selection","Ed-Iter Template Selection","");
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>";

	if ($templatetable) {
		echo"
    <CENTER>
    <INPUT TYPE='submit' NAME='templates' value='Use These Templates'>
    </CENTER>\n
    $templatetable
    <CENTER>
    <INPUT TYPE='hidden' NAME='numtemplates' value='$numtemplates'>
    <INPUT TYPE='submit' NAME='templates' value='Use These Templates'>
    </CENTER>\n";
	}
	else echo "<B>Project does not contain any templates.</B>\n";
	echo"</FORM>\n";
}

//***************************************
//***************************************
//***************************************
//***************************************
function createAlignmentForm($extra=false, $title='edIterAlign.py Launcher', $heading='Perform Ed Iter Alignment') {
  // check if coming directly from a session

	$expId=$_GET['expId'];
	$projectId=getProjectId();

	if ($expId){
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$formAction=$_SERVER['PHP_SELF'];
	}

	// connect to particle info
	$particle = new particledata();
	$templateid = $_POST['templateid'];
	$templateinfo = $particle->getTemplatesFromId($templateid);
	$stackIds = $particle->getStackIds($expId);
	$alignrunsarray = $particle->getAlignStackIds($expId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;
	$firststack = $particle->getStackParams($stackIds[0]['stackid']);
	$firstmpix = $particle->getStackPixelSizeFromStackId($stackIds[0]['stackid']);
	$initparts = $particle->getNumStackParticles($stackIds[0]['stackid']);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set max last ring radius
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/100);\n";
	$javascript .= "	var radius = Math.floor(stackArray[2]/3*bestbin);\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	$javascript .= "	document.viewerform.radius.value = radius;\n";
	// set particle & mask radius and lp
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/align/';
	}
  
  // Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'editer'.($alignruns+1)))
		$alignruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'editer'.($alignruns+1);
	$rundescrval = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = preg_split('%\|--\|%',$stackidstr);
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// alignment params
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : $initparts;
	$iters = ($_POST['iters']) ? $_POST['iters'] : 10;
	// $freealigns = ($_POST['freealigns']) ? $_POST['freealigns'] : 1;
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : 10;
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : 2000;
	$orientref = $_POST['orientref'];

	$boxsz = $firststack['boxsize'];
	$bestbin = floor($boxsz/100)+1;
	$radius = ($_POST['radius']) ? $_POST['radius'] : floor($boxsz/3.0/$bestbin*$firstmpix*1e10);
	$bin = ($_POST['bin']) ? $_POST['bin'] : $bestbin;
	$templateList=($_POST['templateList']) ? $_POST['templateList']: '';

	if (!$templateList) {
		$templateTable.="<table><TR>\n";
		for ($i=1; $i<=$_POST['numtemplates']; $i++) {
			$templateimg = "template".$i;
			if ($_POST[$templateimg]){
				$templateTable.="<TD VALIGN='TOP'><TABLE CLASS='tableborder'>\n";
				$templateIdName="templateId".$i;
				$templateId=$_POST[$templateIdName];
				$templateList.=$i.":".$templateId.",";
				$templateinfo=$particle->getTemplatesFromId($templateId);
				$filename=$templateinfo[path]."/".$templateinfo['templatename'];
				$templateTable.="<TR><TD VALIGN='TOP'><img src='loadimg.php?w=125&filename=$filename' WIDTH='125'></TD></tr>\n";
				$templateTable.="<TR><TD VALIGN='TOP'>".$templateinfo['templatename']."</TD></tr>\n";
				$templateForm.="<INPUT TYPE='hidden' NAME='$templateIdName' VALUE='$templateId'>\n";
				$templateForm.="<INPUT TYPE='hidden' NAME='$templateimg' VALUE='$templateId'>\n";

				$templateTable.="</table></TD>\n";
			}
		}
		$templateTable.="</tr></table>\n";
		if ($templateList) { $templateList=substr($templateList,0,-1);}
		else {
			echo "<br><B>no templates chosen, go back and choose templates</B>\n";
			exit;
		}
	} else {
		//get template info if coming from resubmitting input
		$templateIds = templateIds();
		$templatearray=preg_split("%,%",$templateIds);
		$templateTable.="<table><TR>\n";
		foreach ($templatearray as $templateId) {
			$templateTable.="<TD VALIGN='TOP'><TABLE CLASS='tableborder'>\n";
			$templateinfo=$particle->getTemplatesFromId($templateId);
			$filename=$templateinfo[path]."/".$templateinfo['templatename'];
			$templateTable.="<TR><TD VALIGN='TOP'><img src='loadimg.php?w=125&filename=$filename' WIDTH='125'></TD></tr>\n";
			$templateTable.="<TR><TD VALIGN='TOP'>".$templateinfo['templatename']."</TD></tr>\n";
			$templateTable.="</table></TD>\n";
		}
		$templateTable.="</tr></table>\n";
	}
	echo "<INPUT TYPE='hidden' NAME='templateList' VALUE='$templateList'>\n";
	echo "<INPUT TYPE='hidden' NAME='templates' VALUE='continue'>\n";
	echo "<INPUT TYPE='hidden' NAME='orientref' VALUE='$orientref'>\n";
	echo "<INPUT TYPE='hidden' NAME='numtemplates' VALUE='$numtemplates'>\n";

  echo"
	<TABLE BORDER=0 CLASS=tableborder>
	<TR>
		<TD VALIGN='TOP'>
		<TABLE CELLPADDING='10' BORDER='0'>
		<TR>
			<TD VALIGN='TOP'>
			<B>Alignment Run Name:</B>
			<INPUT TYPE='text' NAME='runname' VALUE='$runnameval'>
			</TD>
		</tr>\n";
		echo"<TR>
			<TD VALIGN='TOP'>
			<B>Alignment Description:</B><br>
			<TEXTAREA NAME='description' ROWS='3' COLS='36'>$rundescrval</TEXTAREA>
			</TD>
		</tr>\n";
		echo"<TR>
			<TD VALIGN='TOP'>	 
			<B>Output Directory:</B><br>
			<INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='38'>
			</TD>
		</tr>
		<TR>
			<td>\n";

	if (!$stackIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo "
		Particles:<br>";
		$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
	}
	echo"
		</TD>
	</tr>";
	echo"
	<TR>
		<TD VALIGN='TOP'>
		<INPUT TYPE='checkbox' NAME='commit' $commitcheck>
		<B>Commit to Database</B><br>
		</TD>
	</tr>";
	echo"
	</table>
	</TD>
	<TD CLASS='tablebg'>
	<TABLE CELLPADDING='5' BORDER='0'>
	<TR>";
	echo"
		<TD VALIGN='TOP'>
		<B>Particle Params:</B></A><br>";
	echo"
		<INPUT TYPE='text' NAME='radius' SIZE='5' VALUE='$radius'>
		Last Ring Radius <FONT SIZE='-1'>(in in &Aring;ngstroms)</FONT><br>";
	echo"
		<INPUT TYPE='text' NAME='lowpass' SIZE='5' VALUE='$lowpass'>
		Low Pass Filter <FONT SIZE='-1'>(in &Aring;ngstroms)</FONT><br>";
	echo"
		<INPUT TYPE='text' NAME='highpass' SIZE='5' VALUE='$highpass'>
		High Pass Filter <FONT SIZE='-1'>(in &Aring;ngstroms)</FONT><br>";
	echo"
		<INPUT TYPE='text' NAME='bin' SIZE='5' VALUE='$bin'>
		Particle Binning<br>";
	echo"
		</TD>
	</tr>
	<TR>
		<TD VALIGN='TOP'>
		<B>Alignment Params:</B></A><br>";
	echo"
		<INPUT TYPE='text' NAME='iters' VALUE='$iters' SIZE='4'>
		Classification/Alignment Iterations<br>";
	// echo"
		// <INPUT TYPE='text' NAME='freealigns' VALUE='$freealigns' SIZE='4'>
		// Free-alignments within each iteration<br>";
	echo"
		<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>
		Number of Particles to Use<br>";
	echo"
		<INPUT TYPE='checkbox' NAME='inverttempl' $inverttempl>
		Invert density of all templates before alignment<br>";
	echo"
		</TD>
	</tr>
	</tr>
	</table>
	</TD>
	</tr>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>";
	echo"<INPUT TYPE='hidden' NAME='refid' VALUE='$templateid'>";
	echo getSubmitForm("Run Ed-Iter Alignment");
	echo "
	  </TD>
	</tr>
	</table>
	</FORM>
	</CENTER>\n";

	echo "$templateForm\n";
	echo "$templateTable\n";

	echo referenceBox("Conformational flexibility of metazoan fatty acid synthase enables catalysis.", 2009, "Brignole EJ, Smith S, Asturias FJ.", "Nat Struct Mol Biol.", 16, 2, 19151726, 2653270, false, "img/editer.jpg");

	processing_footer();
	exit;
}

//***************************************
//***************************************
//***************************************
//***************************************
function runAlignment() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$stackval=$_POST['stackval'];
	list($stackid,$apix,$boxsz) = preg_split('%\|--\|%',$stackval);
	$radius=$_POST['radius'];
	$bin=$_POST['bin'];
	$lowpass=$_POST['lowpass'];
	$highpass=$_POST['highpass'];
	$templates=$_POST['refid'];
	$orientref=$_POST['orientref'];
	$iters=$_POST['iters'];
	// $freealigns=$_POST['freealigns'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$inverttempl = ($_POST['inverttempl']=="on") ? 'inverttempl' : '';
	$description=$_POST['description'];
	$numpart=$_POST['numpart'];
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a session was selected
	if (!$description) createAlignmentForm("<B>ERROR:</B> Enter a brief description of the alignment run");

	//make sure a stack was selected
	if (!$stackid) createAlignmentForm("<B>ERROR:</B> No stack selected");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// alignment
	if ($numpart < 1) 
		createAlignmentForm("<B>ERROR:</B> Number of particles must be at least 1");
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) 
		createAlignmentForm("<B>ERROR:</B> Number of particles to align ($numpart) exceeds number of particles in the stack ($totprtls)");

	$fileformat = ($_POST['fileformat']=='spider') ? 'spider' : '';

	/* *******************
	PART 3: Create program command
	******************** */
	$command ="edIterAlign.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--rundir=".$rundir." ";
	$command.="--runname=$runname ";
	$command.="--description=\"$description\" ";
	$command.="--templates=".templateIds()." ";
	$command.="--orientref=$orientref ";
	$command.="--stack=$stackid ";
	$command.="--nparticles=$numpart ";
	$command.="--bin=$bin ";
	$command.="--radius=$radius ";
	$command.="--lowpass=$lowpass ";
	$command.="--highpass=$highpass ";
	$command.="--iterations=$iters ";
	// $command.="--freealigns=$freealigns ";

	if ($inverttempl) $command.="--invert-templates ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= referenceBox("Conformational flexibility of metazoan fatty acid synthase enables catalysis.", 2009, "Brignole EJ, Smith S, Asturias FJ.", "Nat Struct Mol Biol.", 16, 2, 19151726, 2653270, false, "img/editer.jpg");
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);

	// if error display them
	if ($errors)
		createAlignmentForm("<b>ERROR:</b> $errors");
	
}

/*
**
**
** GENERATE COMMANDLINE INFO FOR TEMPLATES
**
**
*/

function templateIds () {
	$command = "";
	// get the list of templates
	$templateList=$_POST['templateList'];
	$templates=preg_split("%,%", $templateList);
	foreach ($templates as $tmplt) {
		list($tmpltNum,$tmpltId)=preg_split("%:%",$tmplt);
		$templateIds.="$tmpltId,";
	}
	$templateIds=substr($templateIds,0,-1);
	return $templateIds;
}

?>
