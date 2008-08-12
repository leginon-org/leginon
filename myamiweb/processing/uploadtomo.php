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
	runUploadTomogram();
}

// Create the form page
else {
	createUploadTomogramForm();
}

function createUploadTomogramForm($extra=false, $title='UploadTomogram.py Launcher', $heading='Upload an Initial Tomogram') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$rescale=$_GET['rescale'];

	$particle = new particledata();

	// find out if rescaling an existing initial model
	if ($rescale) {
		$modelid=$_GET['modelid'];
		$modelinfo = $particle->getInitTomogramInfo($modelid);
	}

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($rescale) $formAction .="&rescale=TRUE&modelid=$modelid";
	
	$javafunctions .= writeJavaPopupFunctions('appion');  
	
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","models",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
  
	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$res = ($_POST['res']) ? $_POST['res'] : '';
	$tiltseries = ($_POST['tiltseries']) ? $_POST['tiltseries'] : ' ';
	$tomospace = ($_POST['tomospace']) ? $_POST['tomospace'] : ' ';
	$tomoname = ($_POST['tomoname']) ? $_POST['tomoname'] : '';
	$description = $_POST['description'];
	$outdir.'/rescale.mrc';
  
	$syms = $particle->getSymmetries();
	$tomotype = array("number","shape");

	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	
   if ($rescale) echo "";
       else echo"
	<B>Tomogram file name with path:</B><BR/>
      <INPUT TYPE='text' NAME='tomoname' VALUE='$tomoname' SIZE='50'><br />\n
	<B>Snapshot file name with path:</B><BR/>
      <INPUT TYPE='text' NAME='snapshot' VALUE='$snapshot' SIZE='50'><br />\n";
	
	echo"<P>
      <B>Tomogram Description:</B><BR/>
      <TEXTAREA NAME='description' ROWS='2' COLS='40'>$description</TEXTAREA>
      </TD>
    </TR>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>";       


	echo "
	
		<B> <CENTER>Tomogram Params: </CENTER></B>

      <P>
      <INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'>\n";
		echo docpop('apix','Pixel Size');
		echo "<FONT>(in &Aring;ngstroms per pixel)</FONT>
		
		<BR>
      <INPUT TYPE='text' NAME='tiltseries' VALUE='$tiltseries' SIZE='5'>\n";
		echo docpop('tiltseries', 'Tilt Series');
		echo "<FONT>(# tomogram tilt)</FONT>
      
		<BR>
      <INPUT TYPE='text' NAME='session' VALUE='$session' SIZE='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<FONT> (specific to database capture)</FONT>
  		
		<BR>
      <INPUT TYPE='text' NAME='tomospace' VALUE='$tomospace' SIZE='5'>\n";
		echo docpop('tomospace', 'TomoSpace');
   	echo "<FONT>(subset area of image)</FONT>     

		<P>
      </TD>
   </TR>
    </TABLE>
  </TD>
  </TR>
  <td

  <TR>
    <TD ALIGN='CENTER'>
      <hr>
	";
	echo getSubmitForm("Upload Tomogram");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runUploadTomogram() {

	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "uploadTomo.py ";

	$tomoname=$_POST['tomoname'];
	$tiltseries=$_POST['tiltseries'];
	$tomospace=$_POST['tomospace'];
	$session=$_POST['session'];
	$apix=$_POST['apix'];
	$snapshot=$_POST['snapshot'];

	//make sure a model root was entered
	$model=$_POST['model'];
	if ($_POST['tomoname']) $model=$_POST['tomoname'];

	//make sure a apix was provided
	$apix=$_POST['apix'];
	if (!$apix) createUploadTomogramForm("<B>ERROR:</B> Enter the pixel size");
  
	
	if (!$model) createUploadTomogramForm("<B>ERROR:</B> Enter a root name of the model");
  
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createUploadTomogramForm("<B>ERROR:</B> Enter a brief description of the model");


	// filename will be the runid if running on cluster
	$runid = basename($model);
	$runid = $runid.'.upload';

	if (!$_GET['modelid']) $command.="-f $tomoname ";
	$command.="-s $session ";
	$command.="-a $apix ";
	$command.="-t $tiltseries ";
	$command.="-p $tomospace ";
	$command.="-d \"$description\" ";
	$command.="-i $snapshot ";

	
	// submit job to cluster
	if ($_POST['process']=="Upload Tomogram") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadTomogramForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'uploadtomo',True,True);
		// if errors:
		if ($sub) createUploadTomogramForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runid.'/'.$runid.'.appionsub.log';
		$status = "Tomogram was uploaded";
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
		processing_header("Tomogram Upload", "Tomogram Upload");
		echo "$status\n";
	}

	else processing_header("UploadTomogram Command","UploadTomogram Command");
	
	// rest of the page
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>UploadTomogram Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>tomo name</TD><TD>$model</TD></TR>
	<TR><TD>apix</TD><TD>$apix</TD></TR>
	<TR><TD>tiltseries</TD><TD>$tiltseries</TD></TR>
	<TR><TD>tomospace</TD><TD>$tomospace</TD></TR>
	<TR><TD>session</TD><TD>$session</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
	processing_footer();
}


?> 

