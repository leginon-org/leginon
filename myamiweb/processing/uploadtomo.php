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

	$particle = new particledata();

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	
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
		$outdir=ereg_replace("rawdata","tomo",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}

	// Set any existing parameters in form
	$extrabin = ($_POST['extrabin']) ? $_POST['extrabin'] : '1';
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	$volume = ($_POST['volume']) ? $_POST['volume'] : 'volume1';
	$tomoname = ($_POST['tomoname']) ? $_POST['tomoname'] : '';
	$snapshot = ($_POST['snapshot']) ? $_POST['snapshot'] : '';
	$description = $_POST['description'];
	$outdir .= $tomoname.'mrc';

	$alltiltseries = $particle->getTiltSeries($expId);
	$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId); 
	$tiltSeriesSelector = $seriesselector_array[0];
  
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	
  echo"
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
      <INPUT TYPE='text' NAME='extrabin' SIZE='5' VALUE='$extrabin'>\n";
		echo docpop('extrabin','Binning');
		echo "<FONT>(additional binning in tomogram)</FONT>
		
		<BR>";
		echo $seriesselector_array[0];
  #    <INPUT TYPE='text' NAME='tiltseries' VALUE='$tiltseries' SIZE='5'>\n";
		echo docpop('tiltseries', 'Tilt Series');
		#echo "<FONT>(tilt series)</FONT>";
   
	if (!$sessionname) {
		echo "
		<BR>
      <INPUT TYPE='text' NAME='sessionname' VALUE='$sessionname' SIZE='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<FONT> (leginon session name)</FONT>";
	}
		echo "	  		
		<BR>
      <INPUT TYPE='text' NAME='volume' VALUE='$volume' SIZE='5'>\n";
		echo docpop('volume', 'Volume');
   	echo "<FONT>(subvolume name of the full tomogram)</FONT>     

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
	$tiltseriesId=$_POST['tiltseriesId'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$extrabin=$_POST['extrabin'];
	$snapshot=$_POST['snapshot'];

	//make sure a tilt series was provided
	if (!$tiltseriesId) createUploadTomogramForm("<B>ERROR:</B> Select the tilt series");
//make sure a model root was entered
	if ($_POST['tomoname']) $model=$_POST['tomoname'];
	if (!$model) createUploadTomogramForm("<B>ERROR:</B> Enter a root name of the model");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createUploadTomogramForm("<B>ERROR:</B> Enter a brief description of the model");

	$particle = new particledata();
	$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
	$apix = $tiltseriesinfos[0]['ccdpixelsize'] * $tiltseriesinfos[0]['imgbin'] * $extrabin * 1e10;
	$tiltseriesnumber = $tiltseriesinfos[0]['number'];

	// filename will be the runid if running on cluster
	$runid = basename($model);
	$runid = $runid.'.upload';

	if (!$_GET['modelid']) $command.="-f $tomoname ";
	$command.="-s $sessionname ";
	$command.="-a $apix ";
	$command.="-t $tiltseriesnumber ";
	$command.="-v $volume ";
	$command.="-d \"$description\" ";
  if ($snapshot) 
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
	<TR><TD>tiltseries number</TD><TD>$tiltseriesnumber</TD></TR>
	<TR><TD>volume</TD><TD>$volume</TD></TR>
	<TR><TD>session</TD><TD>$sessionname</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
	processing_footer();
}


?> 

