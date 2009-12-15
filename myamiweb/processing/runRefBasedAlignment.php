<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Form for starting a reference-based alignment of a stack
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

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

	// retrieve template info from database for this project
	if ($expId){
	$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}

	// if user wants to use templates from another project
	if($_POST['projectId']) $projectId =$_POST['projectId'];

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
				$filename = $templateinfo[path] ."/".$templateinfo[templatename];
				$checkboxname='template'.$i;
				// create the image template table
				$templatetable.="<img src='loadimg.php?filename=$filename&s=90' WIDTH='90'>\n";
				$templatetable.="</TD><td>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='templateId".$i."' VALUE='$templateinfo[DEF_id]'>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='diam' VALUE='$templateinfo[diam]'>\n";
				$templatetable.="<INPUT TYPE='checkbox' NAME='$checkboxname'>\n";
				$templatetable.="<B>Use Template ID:</B>  $templateinfo[DEF_id]<br>\n";
				$templatetable.="Diameter:  $templateinfo[diam]<br>\n";
				$templatetable.="Pixel Size: $templateinfo[apix]<br>\n";
				$templatetable.="File:&nbsp;<I>\n";
				$templatetable.=$templateinfo[templatename]."</I><br/>\n";
				$templatetable.="Description:&nbsp;<I>\n";
				$templatetable.=$templateinfo[description]."</I>\n";
				$i++;
			}
			if ($i%2 == 1)
				$templatetable.="</TD></tr>\n";
			else
				$templatetable.="</TD>\n";
		}
		$templatetable.="</table>\n<br/>\n";
	}

	processing_header("Template Correlator Launcher","Automated Particle Selection with Template Correlator","");
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
function createAlignmentForm($extra=false, $title='refBasedAlignment.py Launcher', $heading='Perform a reference-based Alignment') {
  // check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	// connect to particle info
	$particle = new particledata();
	$templateid = $_POST['templateid'];
	$templateForm.="<INPUT TYPE='hidden' NAME='templateid' VALUE='$templateid'>\n";
	$templateinfo = $particle->getTemplatesFromId($templateid);
	$stackIds = $particle->getStackIds($sessionId);
	$refbasedIds = $particle->getRefAliIds($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;
	$firststack = $particle->getStackParams($stackIds[0]['stackid']);
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
	$javascript .= "	var lastring = Math.floor(stackArray[2]/3/bestbin);\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	$javascript .= "	document.viewerform.lastring.value = lastring;\n";
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
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
  
  // Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'refbased'.($alignruns+1)))
		$alignruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'refbased'.($alignruns+1);
	$rundescrval = $_POST['description'];
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// alignment params
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : $initparts;
	$iters = ($_POST['iters']) ? $_POST['iters'] : 3;
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : 10;
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : 2000;
	$xysearch = ($_POST['xysearch']) ? $_POST['xysearch'] : '5';
	$xystep = ($_POST['xystep']) ? $_POST['xystep'] : '1';
	$boxsz = ($firststack['bin']) ? $firststack['boxSize']/$firststack['bin'] : $firststack['boxSize'];
	$bestbin = floor($boxsz/100)+1;
	$lastring = ($_POST['lastring']) ? $_POST['lastring'] : floor($boxsz/3.0/$bestbin);
	$firstring = ($_POST['firstring']) ? $_POST['firstring'] : '4';
	$csym = ($_POST['csym']) ? $_POST['csym'] : '';
	$bin = ($_POST['bin']) ? $_POST['bin'] : $bestbin;

	$templateList=($_POST['templateList']) ? $_POST['templateList']: '';
	$numtemplates = ($_POST['numtemplates']) ? $_POST['numtemplates']: 0;
	if (!$templateList) {
		$templateTable.="<table><TR>\n";
		for ($i=1; $i<=$numtemplates; $i++) {
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
		$templatearray=split(",",$templateIds);
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
		Particles:<br/>";
		$particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
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
		<INPUT TYPE='text' NAME='lastring' SIZE='5' VALUE='$lastring'>
		Last Ring Radius <FONT SIZE='-1'>(in pixels)</FONT><br>";
	echo"
		<INPUT TYPE='text' NAME='firstring' SIZE='5' VALUE='$firstring'>
		First Ring Radius <FONT SIZE='-1'>(in pixels)</FONT><br>";
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
		<INPUT TYPE='text' NAME='csym' SIZE='5' VALUE='$csym'>
		C Symmetry<br>";

	echo"
		</TD>
	</tr>
	<TR>
		<TD VALIGN='TOP'>
		<B>Alignment Params:</B></A><br>";
	echo"
		<INPUT TYPE='text' NAME='iters' VALUE='$iters' SIZE='4'>
		Iterations<br>";
	echo"
		<INPUT TYPE='text' NAME='xysearch' VALUE='$xysearch' SIZE='4'>
		Search range from center <FONT SIZE='-1'>(in pixels)</FONT><br>";
	echo"
		<INPUT TYPE='text' NAME='xystep' VALUE='$xystep' SIZE='4'>
		Step size for parsing search range <FONT SIZE='-1'>(in pixels)</FONT><br>";
	echo"
		<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>
		Number of Particles to Use<br>";

	echo "<INPUT TYPE='checkbox' NAME='inverttempl' $invert>\n";
	echo docpop('invert','Invert density of all templates');
	echo "<br/>\n";

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
	echo getSubmitForm("Run Ref-Based Alignment");
	echo "
	  </TD>
	</tr>
	</table>
	</FORM>
	</CENTER>\n";

	echo "$templateForm\n";
	echo "$templateTable\n";

	processing_footer();
	exit;
}

//***************************************
//***************************************
//***************************************
//***************************************
function runAlignment() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$stackval=$_POST['stackval'];
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);
	$lastring=$_POST['lastring'];
	$firstring=$_POST['firstring'];
	$bin=$_POST['bin'];
	$csym=$_POST['csym'];
	$lowpass=$_POST['lowpass'];
	$highpass=$_POST['highpass'];
	$xysearch=$_POST['xysearch'];
	$xystep=$_POST['xystep'];
	$refid=$_POST['refid'];
	$iters=$_POST['iters'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$inverttempl = ($_POST['inverttempl']=="on") ? 'inverttempl' : '';

	//make sure a stack was selected
	if (!$stackid) createAlignmentForm("<B>ERROR:</B> No stack selected");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// alignment
	$numpart=$_POST['numpart'];
	if ($numpart < 1) 
		createAlignmentForm("<B>ERROR:</B> Number of particles must be at least 1");
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) 
		createAlignmentForm("<B>ERROR:</B> Number of particles to aligned ($numpart) must be "
			."less than the number of particles in the stack ($totprtls)");

	$boxsize = (int) floor($boxsz/$bin);
	$maxbox = (int) floor($boxsize/2-2);
	if (($lastring+$xysearch) > $maxbox) {
		createAlignmentForm("<B>ERROR:</B> last ring radius ($lastring pixels) plus xy-search ($xysearch pixels) "
			."is too big for final boxsize ($boxsize pixels); must be less than $maxbox pixels");
	}

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createAlignmentForm("<B>ERROR:</B> Enter a brief description of the alignment run");

	$command="refBasedAlignment2.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--template-list=".templateIds()." ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";

	if ($lastring) $command.="--last-ring=$lastring ";
	if ($firstring) $command.="--first-ring=$firstring ";
	$command.="--rundir=".$rundir." ";
	$command.="--description=\"$description\" ";
	$command.="--lowpass=$lowpass ";
	if ($highpass) $command.="--highpass=$highpass ";
	$command.="--xy-search=$xysearch ";
	$command.="--xy-step=$xystep ";
	$command.="--num-iter=$iters ";
	$command.="--num-part=$numpart ";
	if ($bin) $command.="--bin=$bin ";
	if ($csym) $command.="--csym=$csym ";
	if ($inverttempl) $command.="--invert-templates ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Run Ref-Based Alignment") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password))
			createAlignmentForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'partalign',False,False,False,8);
		// if errors:
		if ($sub)
			createAlignmentForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Alignment Run","Alignment Params");

		echo"
		<TABLE WIDTH='600' BORDER='1'>
		<TR><TD COLSPAN='2'>
		<B>Alignment Command:</B><br>
		$command
		</TD></tr>
		<TR><td>runname</TD><td>$runname</TD></tr>
		<TR><td>stackid</TD><td>$stackid</TD></tr>
		<TR><td>refids</TD><td>".templateIds()."</TD></tr>
		<TR><td>iter</TD><td>$iters</TD></tr>
		<TR><td>numpart</TD><td>$numpart</TD></tr>
		<TR><td>last ring</TD><td>$lastring</TD></tr>
		<TR><td>first ring</TD><td>$firstring</TD></tr>
		<TR><td>rundir</TD><td>$rundir</TD></tr>
		<TR><td>xysearch</TD><td>$xysearch</TD></tr>
		<TR><td>xystep</TD><td>$xystep</TD></tr>
		<TR><td>low pass</TD><td>$lowpass</TD></tr>l
		<TR><td>high pass</TD><td>$highpass</TD></tr>";
		echo"	</table>\n";
		processing_footer();
	}
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
	$templates=split(",", $templateList);
	foreach ($templates as $tmplt) {
		list($tmpltNum,$tmpltId)=split(":",$tmplt);
		$templateIds.="$tmpltId,";
	}
	$templateIds=substr($templateIds,0,-1);
	return $templateIds;
}

?>
