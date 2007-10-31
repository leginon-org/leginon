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
	runCreateModel();
}

// Create the form page
else {
	createCreateModelForm();
}

function createCreateModelForm($extra=false, $title='CreateModel.py Launcher', $heading='Create a model') {
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
	$exclude=$_GET['exclude'];
	$norefId=$_GET['noref'];
	$norefClassId=$_GET['norefClass'];
	$file=$_GET['file'];
	

	// Set any existing parameters in form
	if (!$description) $description = $_POST['description'];
	if (!$exclude) $exclude = $_POST['exclude'];
	if (!$norefId) $norefId = $_POST['norefId'];
	if (!$norefClassId) $norefClassId = $_POST['norefClassId'];
	if (!$file) $file = $_POST['file'];
	if (!$symm) $symm = $_POST['symm'];
	if (!$lp) $lp = $_POST['lp'];
	if (!$mask) $mask = $_POST['mask'];
	if (!$rounds) $rounds = $_POST['rounds'];
	if (!$apix) $apix = $_POST['apix'];

	$javafunctions="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
		function infopopup(infoname){
			var newwindow=window.open('','name','height=250,width=400');
			newwindow.document.write('<HTML><BODY>');
			
			if (infoname=='classpath'){
				newwindow.document.write('This is the path and name of the reference free class average file which will be used to create an initial model');
			}

			if (infoname=='rounds'){
				newwindow.document.write('This is rounds of Euler angle determination to use');
			}
			if (infoname=='mask'){
				newwindow.document.write('Mask radius');
			}
			if (infoname=='lowpass'){
				newwindow.document.write('Lowpass filter radius in Fourier pixels');
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
	
	
	//get the path for where the model is going to be created
	if  ($file) {
		if ( preg_match("/\.img/", $file) ) {
			$path=ereg_replace("\/classes_avg[0-9]*.img","",$file);
		}
	}
	
	//query the database for parameters
	$particle = new particledata();
	$norefparams=$particle->getNoRefParams($norefId);	
	
	//get stack id in order to get apix
	if (!$stackId) {
		$stackId=$norefparams["REF|ApStackData|stack"];
	}
	
	//get apix from stack 
	if (!$apix) {
		$apix=($particle->getStackPixelSizeFromStackId($stackId))*1e10;
	}

	$syms = $particle->getSymmetries();
	
	echo"
	<P>
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>
			<TABLE> \n";
	
	echo"<INPUT TYPE='hidden' NAME='path' VALUE='$path'>\n";
	echo"<INPUT TYPE='hidden' NAME='file' VALUE='$file'>\n";
	echo"<INPUT TYPE='hidden' NAME='apix' VALUE='$apix'>\n";
	echo"
			<TR>
				<TD VALIGN='TOP'>
					<BR/>
					<B>NoRef Class information:</B> <BR/>
					<A HREF=\"javascript:infopopup('classpath')\">Class name & path</A>: $file <BR/>	
					Class ID: $norefClassId<BR/> <INPUT TYPE='hidden' NAME='norefClassId' VALUE='$norefClassId'> <INPUT TYPE='hidden' NAME='norefId' VALUE='$norefId'>
					Excluded Classes: $exclude
					<INPUT TYPE='hidden' NAME='exclude' VALUE='$exclude'>
					<BR/>\n";
	echo "
					<BR/>
					<B>Model Description:</B><BR/>
					<TEXTAREA NAME='description' ROWS='3' COLS='70'>$description</TEXTAREA>
					<BR/>
					<BR/>
				</TD>
			</TR>
			<TR>
				<TD VALIGN='TOP' CLASS='tablebg'>
					<TABLE WIDTH='350' BORDER='0'>
					<TR><TD COLSPAN='2'>
						
						<B>Required Parameters:</B><BR/>
						<TR><TD>Model Symmetry:</TD><TD>
						
						<SELECT NAME='symm'>
      						<OPTION VALUE=''>Select One</OPTION>\n";
    						foreach ($syms as $sym) {
      							if (preg_match("/^C/", $sym[symmetry])) {
								echo "<OPTION VALUE='$sym[DEF_id]'";
      								if ($sym['DEF_id']==$_POST['symm']) echo " SELECTED";
								echo ">$sym[symmetry]";
							}
      								if ($sym['symmetry']=='C1') echo " (no symmetry)";					
							echo "</OPTION>\n";
    						}
    						echo"
      						</SELECT>					
						<TR><TD><A HREF=\"javascript:infopopup('lowpass')\">Low Pass Filter</A>:</TD><TD>
						<INPUT TYPE='text' NAME='lp' SIZE='5' VALUE='$lp'>
						<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT></TD></TR>
						<TR><TD><B>Optional Parameters:</B><BR/></TD></TR>
						<TR><TD><A HREF=\"javascript:infopopup('mask')\">Mask</A>:</TD><TD>
						<INPUT TYPE='text' NAME='mask' SIZE='5' VALUE='$mask'>
						<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT></TD></TR>
						
						<TR><TD><A HREF=\"javascript:infopopup('rounds')\">Rounds</A>:</TD><TD>
						<INPUT TYPE='text' NAME='rounds' SIZE='5' VALUE='$rounds'>
						<FONT SIZE='-2'>(2-5)</FONT></TD></TR>
												
					</TABLE>
				</TD>
		  	</TR>
			
		  </TABLE>
		</TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <HR>
      <BR/>
      <INPUT type='submit' name='process' value='Create Model'><BR/>
      <FONT class='apcomment'>Submission will NOT create the model,<BR/>
			only output a command that you can copy and paste into a unix shell</FONT>
    </TD>
	</TR>
  </TABLE>
  </FORM>
  </CENTER>\n";

	writeBottom();
	exit;
}

function runCreateModel() {
	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createCreateModelForm("<B>ERROR:</B> Enter a brief description of the model");

	//make sure a session was selected
	$session=$_POST['sessionname'];
	if (!$session) createCreateModelForm("<B>ERROR:</B> Select an experiment session");

	$symm=$_POST['symm'];
	if (!$symm) createCreateModelForm("<B>ERROR:</B> Select a symmetry for the model");

	$lp=$_POST['lp'];
	if (!$lp) createCreateModelForm("<B>ERROR:</B> Select a low pass filter value");

	$path=$_POST['path'];
	$mask=$_POST['mask'];
	$rounds=$_POST['rounds'];
	$exclude=$_POST['exclude'];
	$norefId=$_POST['norefId'];
	$norefClassId=$_POST['norefClassId'];
	$apix=$_POST['apix'];

	$particle = new particledata();
	$syms = $particle->getSymmetries();

	foreach ($syms as $sym) {
		if ($sym[DEF_id] == $symm) {
			preg_match("/(^C[0-9]+)/", $sym[symmetry], $match);
			$symm_name = $match[0];
		}
	}

	//putting together command
	$command.="createModel.py ";
	$command.="--session=$session ";
	$command.="--noref=$norefId ";
	$command.="--norefClass=$norefClassId ";
	$command.="--apix=$apix ";
	$command.="--description=\"$description\" ";
	if ($exclude != "") { $command.="--exclude=$exclude "; }
	if ($symm != "") { $command.="--symm=$symm,$symm_name "; }
	if ($lp != "") { $command.="--lp=$lp "; }
	if ($mask != "") { $command.="--mask=$mask "; }
	if ($rounds != "") { $command.="--rounds=$rounds "; }
	
	writeTop("Create Model Run", "CreateModel Params");

	echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>";
	
	//rest of the page
	echo"
	$template_command 
	<B>UploadTemplate Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>session</TD><TD>$session</TD></TR>
	<TR><TD>noref id</TD><TD>$norefId</TD></TR>
	<TR><TD>noref class id</TD><TD>$norefClassId</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	<TR><TD>excluded classes</TD><TD>$exclude</TD></TR>
	<TR><TD>symmetry name</TD><TD>$symm_name</TD></TR>
	<TR><TD>symmetry id</TD><TD>$symm</TD></TR>
	<TR><TD>lp</TD><TD>$lp</TD></TR>";

	if ($mask) echo"<TR><TD>mask</TD><TD>$mask</TD></TR>";
	if ($rounds) echo"<TR><TD>rounds</TD><TD>$rounds</TD></TR>";
	
	echo"
	</TABLE>\n";
	writeBottom();
}

?>
