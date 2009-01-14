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

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$file=$_GET['file'];
	$templateId=$_GET['templateId'];
	$norefId=$_GET['norefId'];
	$norefClassId=$_GET['norefClassId'];
	$stackId=$_GET['stackId'];
	$avg=$_GET['avg'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&stackId=$stackId" : "";
	$formAction.=($file) ? "&file=$file" : "";
	$formAction.=($norefId) ? "&norefId=$norefId" : "";
	$formAction.=($norefClassId) ? "&norefClassId=$norefClassId" : "";
	$formAction.=($avg) ? "&avg=True" : "";
	$formAction.=($templateId) ? "&templateId=$templateId" : "";

	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';
	$template = ($_POST['template']) ? $_POST['template'] : '';
	$hed = ($_POST['hed']) ? $_POST['hed'] : '';
	$description = $_POST['description'];
	if (!$templateId && $templateId != "0") $templateId = $_POST['templateId'];
	if (!$stackId) $stackId = $_POST['stackId'];
	if (!$norefId) $norefId = $_POST['norefId'];
	if (!$norefClassId) $norefClassId = $_POST['norefClassId'];

	// Set template path
	if  ($file) {
		if ( preg_match("/\.(img|hed)/", $file) ) {
			$template=preg_replace("/\/\w+\.(hed|img)/","",$file);
			$template=($avg) ? $template."/template".$stackId."avg.mrc" : $template."/template$templateId.mrc";
		}
	}

	//get the class average file
	if (!$hed) {
		if (!$file) {
		} else {
			$hed = substr($file, 0, -3);
			$hed = $hed."hed";
		}
	}


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
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
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
	
	echo"<INPUT TYPE='hidden' NAME='hed' VALUE='$hed'>\n";
	echo"<INPUT TYPE='hidden' NAME='projectId' VALUE='$projectId'>\n";
	
	//query the database for parameters
	$particle = new particledata();
	$norefparams=$particle->getNoRefParams($norefId);	
	
	//set diameter
	if (!$diam) {
		$diam=$norefparams[particle_diam];
	}
	
	//get stack id in order to get apix
	if (!$stackId) {
		$stackId=$norefparams["REF|ApStackData|stack"];
	}
	
	//get apix from stack 
	if (!$apix) {
		$apix=($particle->getStackPixelSizeFromStackId($stackId))*1e10;
	}
	
	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>
			<TABLE> \n";
	
	//if neither a refId or stackId exist
	if (!$norefId && !$stackId) {
	echo "
			<TR>
				<TD VALIGN='TOP'>
					<BR/>
					<B>Template Name with path:</B> <BR/> 
					<INPUT TYPE='text' NAME='template' VALUE='$template' SIZE='63'/>
					<BR/>\n";
					
	} 

	//if either a refId or stackId exist
	if ($norefId || $stackId) {
	  $label=($norefId) ? "NoRef Class" : "Stack";
	  echo"<INPUT TYPE='hidden' NAME='template' VALUE='$template'>\n";
	  echo"
			<TR>
				<TD VALIGN='TOP'>
					<BR/>
					<B>$label information:</B> <BR/>
					<A HREF=\"javascript:infopopup('classpath')\">name & path</A>: $hed <BR/>	
					ID: "; 
	  if ($norefId) {
	    echo "$norefClassId<BR/>
                  <INPUT TYPE='hidden' NAME='norefClassId' VALUE='$norefClassId'>
                  <INPUT TYPE='hidden' NAME='norefId' VALUE='$norefId'>\n";
	  } 
	
	  elseif ($stackId){
	    echo "$stackId<BR/> <INPUT TYPE='hidden' NAME='stackId' VALUE='$stackId'>\n";
	    if ($avg) {
	      echo "<input type='hidden' name='avgstack' value='avg'>\n";
	    }
	  }

	//rest of the page
	  if ($norefId) echo"Image Number: $templateId<BR/>
                             <INPUT TYPE='hidden' NAME='templateId' VALUE='$templateId'>\n";
	  elseif ($avg) echo"Stack images will be averaged to create a template<br />\n";
	}
	
	echo "
					<BR/>
					<B>Template Description:</B><BR/>
					<TEXTAREA NAME='description' ROWS='3' COLS='70'>$description</TEXTAREA>
					<BR/>
					<BR/>
				</TD>
			</TR>
			<TR>
				<TD VALIGN='TOP' CLASS='tablebg'>
					<BR/>
					Particle Diameter:<BR/>
					<INPUT TYPE='text' NAME='diam' SIZE='5' VALUE='$diam'>
					<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT><BR>
					<BR/>
					Pixel Size:<BR/>
					<INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'>
					<FONT SIZE='-2'>(in &Aring;ngstroms per pixel)</FONT>
					<BR/>
					<BR/>
				</TD>
		  	</TR>
			
		  </TABLE>
		</TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <hr />
	";
	echo getSubmitForm("Upload Template");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runUploadTemplate() {
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];
	$projectId = $_POST['projectId'];

	$command.="uploadTemplate.py ";

	//make sure a template root or a class/stack root was entered
	$template=$_POST['template'];
	$hed=$_POST['hed'];
	if (!$template && !$hed) createUploadTemplateForm("<B>ERROR:</B> Enter a the root name of the template or stack/noref class");

	//make sure a description is provided
	$description=$_POST['description'];
	if (!$description) createUploadTemplateForm("<B>ERROR:</B> Enter a brief description of the template");

	//make sure a session was selected
	$session=$_POST['sessionname'];
	if (!$session) createUploadTemplateForm("<B>ERROR:</B> Select an experiment session");

	//make sure a diam was provided
	$diam=$_POST['diam'];
	if (!$diam) createUploadTemplateForm("<B>ERROR:</B> Enter the particle diameter");

	//make sure a apix was provided
	$apix=$_POST['apix'];
	if (!$apix) createUploadTemplateForm("<B>ERROR:</B> Enter the pixel size");

	// filename will be the runid if running on cluster
	$runid = basename($template);
	$runid = $runid.'.upload';

	$templateId=$_POST['templateId'];
	$stackId=$_POST['stackId'];
	$norefId=$_POST['norefId'];
	$avgstack=$_POST['avgstack'];
	$norefClassId=$_POST['norefClassId'];

	//check if the template is an existing file (wild type is not searched)
	if (!file_exists($template)) {
		$template_warning="File ".$template." does not exist. This is OK if you are uploading more than one template"; 
	} else {
		$template_warning="File ".$template." exist. Make sure that this is the file that you want!";
	}
	
	// set runname as time
	$runname = getTimestring();

	//putting together command
	$command.="-t $template ";
	$command.="-p $projectId ";
	$command.="-s $session ";
	$command.="--apix=$apix ";
	$command.="--diam=$diam ";
	$command.="-d \"$description\" ";
	$command.="-n $runname ";
	if ($templateId || $templateId == "0") $command.="--stackimgnum=$templateId ";
	if ($stackId) $command.="--stackid=$stackId ";
	if ($norefClassId) $command.="--norefid=$norefClassId ";
	if ($avgstack) $command.="--avgstack ";

	// submit job to cluster
	if ($_POST['process']=="Upload Template") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadTemplateForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'uploadtemplate',True);
		// if errors:
		if ($sub) createUploadTemplateForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runid.'/'.$runid.'.appionsub.log';
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

		//display this line if there's a norefId or stackId
		if ($norefId || $stackId) echo"<font class='apcomment'><b>This command will create a new MRC file called:</b><br />$template</font><br /><br />";
		else echo"$template_warning<br />";
	}
	//rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	$template_command 
	<B>UploadTemplate Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>template name</TD><TD>$template</TD></TR>
	<TR><TD>apix</TD><TD>$apix</TD></TR>
	<TR><TD>diam</TD><TD>$diam</TD></TR>
	<TR><TD>session</TD><TD>$session</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>";
	if ($templateId || $templateId == 0) echo"<TR><TD>stack image number</TD><TD>$templateId</TD></TR>";
	if ($stackId) echo"<TR><TD>stack id</TD><TD>$stackId</TD></TR>";
	if ($norefId) echo"<TR><TD>noref id</TD><TD>$norefId</TD></TR>";
	echo"
	</TABLE>\n";
	processing_footer();
}

?>
