<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadTemplate();
}

// Create the form page
else {
	createUploadTemplateForm();
}

function createUploadTemplateForm($extra=false, $title='UploadTemplate.py Launcher', $heading='Upload a template') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$templateIds=$_GET['templateIds'];
	$alignId=$_GET['alignId'];
	$clusterId=$_GET['clusterId'];
	$stackId=$_GET['stackId'];
	$avg=$_GET['avg'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&stackId=$stackId" : "";
	$formAction.=($clusterId) ? "&clusterId=$clusterId" : "";
	$formAction.=($alignId) ? "&alignId=$alignId" : "";
	$formAction.=($avg) ? "&avg=True" : "";
	$formAction.=($templateIds!="") ? "&templateIds=$templateIds" : "";

	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';
	$template = ($_POST['template']) ? $_POST['template'] : '';
	$description = $_POST['description'];
	if ($templateIds=="") $templateIds = $_POST['templateIds'];
	if (!$stackId) $stackId = $_POST['stackId'];
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	$javafunctions="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
		function infopopup(infoname){
			var newwindow=window.open('','name','height=250,width=400');
			newwindow.document.write('<HTML><BODY>');
			if (infoname=='classpath'){
				newwindow.document.write('This is the path of the class average or stack used for extracting the MRC file. Leave this blank if the template file specified by template path above already exist');
			}
			newwindow.document.write('</BODY></HTML>');
			newwindow.document.close();
		}

	</SCRIPT>\n";

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=$sessioninfo['Image path'];
	$outdir=ereg_replace("leginon","appion",$outdir);
	$outdir=ereg_replace("rawdata","templates",$outdir);

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' VALUE='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
	
	echo"<INPUT TYPE='hidden' NAME='projectId' VALUE='$projectId'>\n";
	
	//query the database for parameters
	$particle = new particledata();

	echo"<table border='3' class='tableborder'>";
	echo"<tr><td valign='top'>\n";
	echo"<table border='0' cellpading='5' cellspacing='5'><tr><td valign='top'>\n";

	//if neither a refId or stackId exist
	if (!$stackId && !$alignId && !$clusterId) {
		echo "<br>\n";
		echo "Template Name with path <i>(wild cards are acceptable)</i>: <br> \n";
		echo "<INPUT TYPE='text' NAME='template' VALUE='$template' SIZE='55'/>\n";
		echo "<br>\n";			
	} 

	if ($stackId) {
		echo openRoundBorder();
		echo ministacksummarytable($stackId);
	    echo "<input type='hidden' name='stackId' value='$stackId'>\n";
		echo closeRoundBorder();
		echo "<br/>\n";
	} elseif($alignId) {
		echo openRoundBorder();
		echo alignstacksummarytable($alignId, true);
	    echo "<input type='hidden' name='alignId' value='$alignId'>\n";
		echo closeRoundBorder();
		echo "<br/>\n";
	} elseif($clusterId) {
		echo openRoundBorder();
		echo "Cluster Id: $clusterId\n";
	    echo "<input type='hidden' name='clusterId' value='$clusterId'>\n";
		echo closeRoundBorder();
		echo "<br/>\n";
	}

	if ($avg) {
		echo "<input type='hidden' name='avgstack' value='avg'>\n";
	  	echo"<font size='+1'><i>Stack images will be averaged to create a template</i></font>\n";
		echo "<br/>\n";
	} elseif ($templateIds!="") {
		echo"<font size='+1'>Selected Image Numbers: <i>$templateIds</i></font>\n";
		echo "<input type='hidden' name='templateIds' value='$templateIds'>\n";
		echo "<br/>\n";
	}

	echo "<br/>\n";

	echo "Template Description:<br>";
	echo "<TEXTAREA NAME='description' ROWS='3' COLS='70'>$description</TEXTAREA>";

	echo "</TD></tr><TR><TD VALIGN='TOP'>";

	echo "Particle Diameter:<br>\n"
			."<INPUT TYPE='text' NAME='diam' SIZE='5' VALUE='$diam'>\n"
			."<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
		echo "<br/>\n";

	if (!$stackId && !$alignId && !$clusterId) {
		echo "Pixel Size:<br>\n"
			."<INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'>\n"
			."<FONT SIZE='-2'>(in &Aring;ngstroms per pixel)</FONT>\n";
		echo "<br/>\n";
	}
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br/>\n";


	echo "<br/>\n";
	echo "</td></tr></table></td></tr><tr><td align='center'><hr/>";
	echo getSubmitForm("Upload Template");
	echo "</td></tr></table></form>\n";
	processing_footer();
	exit;
}

function runUploadTemplate() {
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];
	$projectId = getProjectId();
	$templateIds=$_POST['templateIds'];
	$stackId=$_POST['stackId'];
	$alignId=$_POST['alignId'];
	$clusterId=$_POST['clusterId'];
	$avgstack=$_POST['avgstack'];
	$diam=$_POST['diam'];
	$session=$_POST['sessionname'];
	$description=$_POST['description'];
	$apix=$_POST['apix'];
	$template=$_POST['template'];
	$commit=$_POST['commit'];

	//make sure a description is provided
	if (!$description) createUploadTemplateForm("<B>ERROR:</B> Enter a brief description of the template");

	//make sure a session was selected
	if (!$session) createUploadTemplateForm("<B>ERROR:</B> Select an experiment session");

	//make sure a diam was provided
	if (!$diam) createUploadTemplateForm("<B>ERROR:</B> Enter the particle diameter");

	//make sure a apix was provided
	if (!$stackId && !$alignId && !$clusterId) {
		if (!$apix) createUploadTemplateForm("<B>ERROR:</B> Enter the pixel size");
		if (!$template) createUploadTemplateForm("<B>ERROR:</B> Enter a the root name of the template or stack/alignment/cluster");
		//check if the template is an existing file (wild type is not searched)
		if (!file_exists($template)) {
			$template_warning="File ".$template." does not exist. This is OK if you are uploading more than one template"; 
		} else {
			$template_warning="File ".$template." exist. Make sure that this is the file that you want!";
		}
	}



	// set runname as time
	$runname = "template".getTimestring();

	//putting together command
	$command = "uploadTemplate.py ";
	if ($stackId)
		$command.="--stackid=$stackId ";
	elseif ($alignId)
		$command.="--alignid=$alignId ";
	elseif ($clusterId)
		$command.="--clusterid=$clusterId ";
	else 
		$command.="--template=$template ";

	$command.="--projectid=$projectId ";
	$command.="--session=$session ";
	if ($apix)
		$command.="--apix=$apix ";
	$command.="--diam=$diam ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	if ($templateIds!="") $command.="--imgnums=$templateIds ";
	if ($avgstack) $command.="--avgstack ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";


	// submit job to cluster
	if ($_POST['process']=="Upload Template") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadTemplateForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'uploadtemplate',True);
		// if errors:
		if ($sub) createUploadTemplateForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runname.'/'.$runname.'.appionsub.log';
		$status = "Template was uploaded";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while uploading, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Template Upload", "Template Upload");
		echo "$status\n";
	}

	else {
		processing_header("UploadTemplate Command", "UploadTemplate Command");
		if ($template_warning) echo"$template_warning<br />";
	}
	//rest of the page
	echo"
	<table class='tableborder' width='600' border='1'>
	<tr><td colspan='2'>
	$template_command 
	<B>UploadTemplate Command:</B><br>
	$command
	</TD></tr>
	<TR><td>template name</TD><td>$template</TD></tr>
	<TR><td>apix</TD><td>$apix</TD></tr>
	<TR><td>diam</TD><td>$diam</TD></tr>
	<TR><td>session</TD><td>$session</TD></tr>
	<tr><td>commit</td><td>$commit</td></tr>
	<TR><td>description</TD><td>$description</TD></tr>";

	if ($templateIds!="") echo"<TR><td>image numbers</TD><td>$templateIds</TD></tr>";
	if ($stackId) echo"<TR><td>stack id</TD><td>$stackId</TD></tr>";
	echo"
	</table>\n";
	processing_footer();
}

?>
