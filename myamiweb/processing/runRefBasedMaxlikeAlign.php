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
  runMaxLikeAlign();
}

 // Create the form page
elseif ($_POST['templates']) {
  createMaxLikeAlignForm();
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
function createMaxLikeAlignForm($extra=false, $title='maxlikeAlignment.py Launcher', $heading='Maximum Likelihood Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectId();

	if ($expId){
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$formAction=$_SERVER['PHP_SELF'];
	}

	// connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($expId);
	$alignrunsarray = $particle->getAlignStackIds($expId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set max last ring radius
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
	$javascript .= "	if (bestbin < 1) {\n";
	$javascript .= "	var bestbin = 1 ;}\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	$javascript .= "	estimatetime();\n";
	// set particle & mask radius and lp
	$javascript .= "}\n";
	$javascript .= "
		function enablefastmode() {
			if (document.viewerform.fast.checked){
				document.viewerform.fastmode.disabled=false;
			} else {
				document.viewerform.fastmode.disabled=true;
			}

		}
		function estimatetime() {
			var secperiter = 0.12037;
			var stackval = document.viewerform.stackval.value;
			var stackArray = stackval.split('|--|');
			var numpart = document.viewerform.numpart.value;
			var boxsize = stackArray[2];
			var numpix = Math.pow(boxsize/document.viewerform.bin.value, 2);
			var calctime = (numpart/1000.0) * document.viewerform.numtemplates.value * numpix * secperiter / document.viewerform.angle.value / (document.viewerform.nproc.value - 1);
			if (document.viewerform.mirror.checked) {
				calctime = calctime*2.0;
			}
			if (calctime < 70) {
				var time = Math.round(calctime*100.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' seconds';
			} else if (calctime < 3700) {
				var time = Math.round(calctime*0.6)/100.0
				document.viewerform.timeestimate.value = time.toString()+' minutes';
			} else if (calctime < 3700*24) {
				var time = Math.round(calctime/36.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' hours';
			} else {
				var time = Math.round(calctime/36.0/24.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' days';
			}
		}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<span style='font-size: larger; color:#bb3333;'>$extra</span><br />\n";
	}
  
	echo "<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'maxlike'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'maxlike'.($alignruns+1);
	$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = split('\|--\|',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '4';
	$angle = ($_POST['angle']) ? $_POST['angle'] : '5';
	$maxiter = ($_POST['maxiter']) ? $_POST['maxiter'] : '30';
	$mirror = ($_POST['mirror']=='on' || !$_POST['mirror']) ? 'checked' : '';
	$fast = ($_POST['fast']=='on' || !$_POST['fast']) ? 'checked' : '';

	// deal with templates
	$templateid = $_POST['templateid'];
	$templateform .= "<input type='hidden' name='templateid' value='$templateid'>\n";
	$templateinfo = $particle->getTemplatesFromId($templateid);
	$templatelist= ($_POST['templatelist']) ? $_POST['templatelist']: '';
	$numtemplates = ($_POST['numtemplates']) ? $_POST['numtemplates']: 0;
	if (!$templatelist) {
		$templatetable.="<table><TR>\n";
		for ($i=1; $i<=$numtemplates; $i++) {
			$templateimg = "template".$i;
			if ($_POST[$templateimg]){
				$templatetable.="<td valign='top'><table class='tableborder'>\n";
				$templateIdName="templateId".$i;
				$templateId=$_POST[$templateIdName];
				$templatelist.=$i.":".$templateId.",";
				$templateinfo=$particle->getTemplatesFromId($templateId);
				$filename=$templateinfo[path]."/".$templateinfo['templatename'];
				$templatetable.="<TR><TD VALIGN='TOP'><img src='loadimg.php?w=125&filename=$filename' WIDTH='125'></TD></tr>\n";
				$templatetable.="<TR><TD VALIGN='TOP'>".$templateinfo['templatename']."</TD></tr>\n";
				$templateform.="<INPUT TYPE='hidden' NAME='$templateIdName' VALUE='$templateId'>\n";
				$templateform.="<INPUT TYPE='hidden' NAME='$templateimg' VALUE='$templateId'>\n";
				$templatetable.="</table></TD>\n";
			}
		}
		$templatetable.="</tr></table>\n";
		if ($templatelist) { $templatelist=substr($templatelist,0,-1);}
		else {
			echo "<br><B>no templates chosen, go back and choose templates</B>\n";
			exit;
		}
	} else {
		//get template info if coming from resubmitting input
		$templateIds = templateIds();
		$templatearray=split(",",$templateIds);
		$templatetable.="<table><TR>\n";
		foreach ($templatearray as $templateId) {
			$templatetable.="<TD VALIGN='TOP'><TABLE CLASS='tableborder'>\n";
			$templateinfo=$particle->getTemplatesFromId($templateId);
			$filename=$templateinfo[path]."/".$templateinfo['templatename'];
			$templatetable.="<TR><TD VALIGN='TOP'><img src='loadimg.php?w=125&filename=$filename' WIDTH='125'></TD></tr>\n";
			$templatetable.="<TR><TD VALIGN='TOP'>".$templateinfo['templatename']."</TD></tr>\n";
			$templatetable.="</table></TD>\n";
		}
		$templatetable.="</tr></table>\n";
	}
	echo "<input type='hidden' name='templatelist' value='$templatelist'>\n";
	echo "<input type='hidden' name='templates' value='continue'>\n";
	echo "<input type='hidden' name='numtemplates' value='$numtemplates'>\n";
	// end templates

	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>MaxLike Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Max Like Alignment:</b>');
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

	echo "<INPUT TYPE='text' NAME='nproc' SIZE='4' VALUE='$nproc' onChange='estimatetime()'>\n";
	echo "Number of Processors";
	echo "<br/>\n";

	echo "</TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE cellpading='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	//echo "<B>Particle Params:</B></A><br>\n";

	echo "<b>Particle-specific Radii (in &Aring;ngstroms)</b>\n";
	echo "<br />\n";
	if  (!$apix) {
        	echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}
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

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='angle' VALUE='$angle' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('angleinc','Angular Increment');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='maxiter' VALUE='$maxiter' SIZE='4'>\n";
	echo docpop('xmippmaxiter','Maximum number of iterations');
	echo "<br/>\n";

	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='inverttempl' $invert>\n";
	echo docpop('invert','Invert density of all templates');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='mirror' onChange='estimatetime()' $mirror>\n";
	echo docpop('mirror','Use Mirrors in Alignment');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='fast' onClick='estimatetime(this)' checked disabled>\n";
	echo docpop('fastmode','Use Fast Mode');
	echo "<br/>\n";

	echo "Search space reduction criteria";
	echo "<br/>\n";
	echo "&nbsp;&nbsp;<select name='fastmode' ";
	if (!$fast) echo " disabled";
	echo ">\n";
	echo " <option value='normal'>Normal search</option>\n";
	echo " <option value='narrow'>Faster, narrower search</option>\n";
	echo " <option value='wide'>Slower, wider search</option>\n";
	echo "</select>\n";
	echo "<br/>\n";

	echo "Convergence stopping criteria";
	echo "<br/>\n";
	echo "&nbsp;&nbsp;<select name='converge'>\n";
	echo " <option value='normal'>Normal search</option>\n";
	echo " <option value='fast'>Faster, shorter search</option>\n";
	echo " <option value='slow'>Slower, longer search</option>\n";
	echo "</select>\n";
	echo "<br/>\n";

	echo "<br/>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo "Time estimate for first iteration: ";
	echo "<INPUT TYPE='text' NAME='timeestimate' SIZE='16' onFocus='this.form.elements[0].focus()'>\n";
	echo "<br/>\n";
	echo getSubmitForm("Run Max Like Alignment");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	echo "$templateform\n";
	echo "$templatetable\n";

	processing_footer();
	exit;
}

function runMaxLikeAlign() {
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackval=$_POST['stackval'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$angle=$_POST['angle'];
	$maxiter=$_POST['maxiter'];
	$numtemplates=$_POST['numtemplates'];
	$bin=$_POST['bin'];
	$description=$_POST['description'];
	//$fast = ($_POST['fast']=="on") ? true : false;
	$fast = true;
	$fastmode = $_POST['fastmode'];
	$converge = $_POST['converge'];
	$mirror = ($_POST['mirror']=="on") ? true : false;
	$commit = ($_POST['commit']=="on") ? true : false;
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 1;

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);
	//make sure a session was selected

	if (!$description)
		createMaxLikeAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	if (!$numtemplates || $numtemplates < 1)
		createMaxLikeAlignForm("<B>ERROR:</B> No templates selected");

	if ($nproc > 16)
		createMaxLikeAlignForm("<B>ERROR:</B> Let's be reasonable with the nubmer of processors, less than 16 please");

	//make sure a stack was selected
	if (!$stackid)
		createMaxLikeAlignForm("<B>ERROR:</B> No stack selected");

	// classification
	if ($numpart < 10)
		createMaxLikeAlignForm("<B>ERROR:</B> Must have more than 10 particles");

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createMaxLikeAlignForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than the number of particles in the stack ($totprtls)");

	// determine calc time
	$stackdata = $particle->getStackParams($stackid);
	$boxsize = ($stackdata['bin']) ? $stackdata['boxSize']/$stackdata['bin'] : $stackdata['boxSize'];
	$secperiter = 0.12037;
	$calctime = ($numpart/1000.0)*$numtemplates*($boxsize/$bin)*($boxsize/$bin)/$angle*$secperiter/$nproc;
	if ($mirror) $calctime *= 2.0;
	// kill if longer than 10 hours
	if ($calctime > 10.0*3600.0)
		createMaxLikeAlignForm("<b>ERROR:</b> Run time per iteration greater than 10 hours<br/>"
			."<b>Estimated calc time:</b> ".round($calctime/3600.0,2)." hours\n");
	elseif (!$fast && $calctime > 1800.0)
		createMaxLikeAlignForm("<b>ERROR:</b> Run time per iteration greater than 30 minutes without fast mode<br/>"
			."<b>Estimated calc time:</b> ".round($calctime/60.0,2)." minutes\n");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// setup command
	$command ="refBasedMaxlikeAlign.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--template-list=".templateIds()." ";
	$command.="--stack=$stackid ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	if ($inverttempl) $command.="--invert-templates ";
	$command.="--num-part=$numpart ";
	$command.="--bin=$bin ";
	$command.="--angle-interval=$angle ";
	$command.="--max-iter=$maxiter ";
	if ($nproc && $nproc>1)
		$command.="--nproc=$nproc ";
	if ($fast) {
		$command.="--fast ";
		$command.="--fast-mode=$fastmode ";
	} else
		$command.="--no-fast ";
	if ($mirror)
		$command.="--mirror ";
	else
		$command.="--no-mirror ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	$command.="--converge=$converge ";
	// submit job to cluster
	if ($_POST['process']=="Run Max Like Alignment") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createMaxLikeAlignForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'partalign',False,False,False,$nproc);
		// if errors:
		if ($sub) createMaxLikeAlignForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("Max Like Align Run Params","Max Like Align Params");
		echo "<table width='600' class='tableborder' border='1'>";
		echo "<tr><td colspan='2'><br/>\n";
		if ($calctime < 60)
			echo "<span style='font-size: larger; color:#999933;'>\n<b>Estimated calc time:</b> "
				.round($calctime,2)." seconds\n";
		elseif ($calctime < 3600)
			echo "<span style='font-size: larger; color:#33bb33;'>\n<b>Estimated calc time:</b> "
				.round($calctime/60.0,2)." minutes\n";
		else
			echo "<span style='font-size: larger; color:#bb3333;'>\n<b>Estimated calc time:</b> "
				.round($calctime/3600.0,2)." hours\n";
		echo "for the first iteration</span><br/>"
			."<i>it gets much faster after the first iteration with the fast mode</i><br/><br/></td></tr>\n";
		echo "
			<tr><td colspan='2'>
			<b>MaxLike Alignment Command:</b><br />
			$command
			</td></tr>
			<tr><td>run id</td><td>$runname</td></tr>
			<tr><td>stack id</td><td>$stackid</td></tr>
			<tr><td>low pass</td><td>$lowpass</td></tr>
			<tr><td>high pass</td><td>$highpass</td></tr>
			<tr><td>num part</td><td>$numpart</td></tr>
			<tr><td>angle increment</td><td>$angle</td></tr>
			<tr><td>maximum iterations</td><td>$maxiter</td></tr>
			<TR><td>refids</TD><td>".templateIds()."</TD></tr>
			<tr><td>binning</td><td>$bin</td></tr>
			<tr><td>fast</td><td>$fast</td></tr>
			<tr><td>fast mode</td><td>$fastmode</td></tr>
			<tr><td>converge</td><td>$converge</td></tr>
			<tr><td>mirror</td><td>$mirror</td></tr>
			<tr><td>run dir</td><td>$rundir</td></tr>
			<tr><td>commit</td><td>$commit</td></tr>
			</table>\n";
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
	$templatelist=$_POST['templatelist'];
	$templates=split(",", $templatelist);
	foreach ($templates as $tmplt) {
		list($tmpltNum,$tmpltId)=split(":",$tmplt);
		$templateIds.="$tmpltId,";
	}
	$templateIds=substr($templateIds,0,-1);
	return $templateIds;
}

?>
