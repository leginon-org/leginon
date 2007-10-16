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
require "inc/ctf.inc";

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
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];
	$file=$_GET['file'];
	$templateId=$_GET['templateId'];
	$norefId=$_GET['norefId'];
	$stackId=$_GET['stackId'];
	
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

	writeTop($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo"<INPUT TYPE='hidden' NAME='sessionname' VALUE='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';
	$template = ($_POST['template']) ? $_POST['template'] : '';
	$file_hed = ($_POST['hed']) ? $_POST['hed'] : '';
	$description = $_POST['description'];
	
	// Set template path
	if  ($file) {
		if ( preg_match("/\.img/", $file) ) {
			$template=ereg_replace("\/classes_avg[0-9]*.img","",$file);
			$template=$template."/template$templateId.mrc";
		} elseif ( preg_match("/\.hed/", $file) ) {
			$template=ereg_replace("\/start.hed","",$file);
			$template=$template."/template$templateId.mrc";
		}
	}

	
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
	
	//get the class average file
	if (!$file_hed) {
		if (!$file) {
		} else {
			$file_hed = substr($file, 0, -3);
			$file_hed = $file_hed."hed";
		}
	}

	echo"
	<P>
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>
			<TABLE>
			<TR>
				<TD VALIGN='TOP'>
					<BR/>
					
					<B>Default template path:</B> <BR/> 
					<INPUT TYPE='text' NAME='template' VALUE='$template' SIZE='63'/>
					<BR/>
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
			<TR>
				<TD VALIGN='TOP' CLASS='tablebg'>
					<BR/>
					<B>Class average information:</B><BR/>
					<A HREF=\"javascript:infopopup('classpath')\">Class path</A>:
					<INPUT TYPE='text' NAME='hed' SIZE='55' VALUE='$file_hed'> <BR/>	
				</TD>
			</TR>
		  </TABLE>
		</TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <HR>
      <BR/>
      <INPUT type='submit' name='process' value='Upload Template'><BR/>
      <FONT COLOR='RED'>Submission will NOT upload the template,<BR/>
			only output a command that you can copy and paste into a unix shell</FONT>
    </TD>
	</TR>
  </TABLE>
  </FORM>
  </CENTER>\n";
	writeBottom();
	exit;
}

function runUploadTemplate() {
	//make sure a template root was entered
	$template=$_POST['template'];
	if (!$template) createUploadTemplateForm("<B>ERROR:</B> Enter a the root name of the template");

	//make sure a session was selected
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

	$hed=$_POST['hed'];
	if (!$hed) {
		if (!file_exists($template)) {
			createUploadTemplateForm("<B>ERROR:</B> Could not find file: ".$template);  
		}
		$template_command="File ".$template." exist. But make sure that this is the file that you want!";
	} else {
		$template_Id=ereg("template([0-9]*)",$template,$Id);
		$template_command.="proc2d ";
		$template_command.="$hed $template first=$Id[1] last=$Id[1]";
	}

	$command.="uploadTemplate.py ";
	$command.="template=$template ";
	$command.="session=$session ";
	$command.="apix=$apix ";
	$command.="diam=$diam ";
	$command.="description=\"$description\"";

	writeTop("UploadTemplate Run","UploadTemplate Params");

	echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>Create MRC as Template Command:</B><BR>
	$template_command
	</TD>
	<TR><TD COLSPAN='2'>
	<B>UploadTemplate Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>template name</TD><TD>$template</TD></TR>
	<TR><TD>apix</TD><TD>$apix</TD></TR>
	<TR><TD>diam</TD><TD>$diam</TD></TR>
	<TR><TD>session</TD><TD>$session</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
	writeBottom();
}

?>
