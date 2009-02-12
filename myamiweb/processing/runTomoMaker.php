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
	runTomoMaker();
}

// Create the form page
else {
	createTomoMakerForm();
}

function createTomoMakerForm($extra=false, $title='UploadTomogram.py Launcher', $heading='Upload an Initial Tomogram') {
	// check if coming directly from a session
	$expId=$_GET['expId'];

	$particle = new particledata();

	$projectId=$_SESSION['projectId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	
	$javafunctions .= writeJavaPopupFunctions('appion');  
	
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
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
	$thickness = ($_POST['thickness']) ? $_POST['thickness'] : '200';
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	$alignruns = $particle->countTomoAlignmentRuns($tiltseriesId);
	$autorunname = 'full'.($alignruns+1);
	$runname = ($_POST['lasttiltseries']==$tiltseriesId) ? $_POST['runname']:$autorunname;
	$description = $_POST['description'];

	$alltiltseries = $particle->getTiltSeries($expId);
	$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId); 
	$tiltSeriesSelector = $seriesselector_array[0];
	echo "<input type='hidden' name='lasttiltseries' value='$tiltseriesId'>\n";
	if ($tiltseriesId) {
		$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
  } else {
		$tiltseriesinfos = array();
	}
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	echo "<p>";
	echo $seriesselector_array[0];
	echo docpop('tiltseries', 'Tilt Series');
	if (count($tiltseriesinfos) && $tiltseriesId) {
		echo "
		<br/><b>First Image in the Tilt Series:</b><br/>"
			.$tiltseriesinfos[0]['filename'];
	} else {
		if ($tiltseriesId)
			echo "<br/><b>Bad Tilt Series! Do not use.</b><br/>";
	}
	echo "<p>
    <INPUT TYPE='text' NAME='runname' VALUE='$runname' SIZE='5'>\n";
	echo docpop('tomorunname', 'Runname');
  echo "<FONT>(full tomogram reconstruction run name)</FONT>";     
	
	echo"<P>
      <B>Tomogram Description:</B><BR/>
      <TEXTAREA NAME='description' ROWS='2' COLS='40'>$description</TEXTAREA>
      </TD>
    </TR>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>";       

	echo "
		<B> <CENTER>Tomogram Creation Params: </CENTER></B>
      <P>
      <INPUT TYPE='text' NAME='extrabin' SIZE='5' VALUE='$extrabin'>\n";
		echo docpop('extrabin','Binning');
		echo "<FONT>(additional binning in tomogram)</FONT>
		<p>
      <INPUT TYPE='text' NAME='thickness' SIZE='8' VALUE='$thickness'>\n";
		echo docpop('tomothickness','Tomogram Thickness');
		echo "<FONT>(pixels in tilt images)</FONT>
		<p><br />";
   
	if (!$sessionname) {
		echo "
		<BR>
      <INPUT TYPE='text' NAME='sessionname' VALUE='$sessionname' SIZE='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<FONT> (leginon session name)</FONT>";
	}
		echo "	  		
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
	echo getSubmitForm("Make Tomogram");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runTomoMaker() {

	$projectId=$_SESSION['projectId'];
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "tomomaker.py ";

	$tiltseriesId=$_POST['tiltseriesId'];
	$runname=$_POST['runname'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$extrabin=$_POST['extrabin'];
	$thickness=$_POST['thickness'];

	//make sure a tilt series was provided
	if (!$tiltseriesId) createTomoMakerForm("<B>ERROR:</B> Select the tilt series");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createTomoMakerForm("<B>ERROR:</B> Enter a brief description of the tomogram");

	$particle = new particledata();
	$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
	$apix = $tiltseriesinfos[0]['ccdpixelsize'] * $tiltseriesinfos[0]['imgbin'] * $extrabin * 1e10;
	$tiltseriesnumber = $tiltseriesinfos[0]['number'];

	$command.="--session=$sessionname ";
	$command.="--bin=$extrabin ";
	$command.="--tiltseriesnumber=$tiltseriesnumber ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
	$command.="--thickness=$thickness ";
	$command.="--description=\"$description\" ";
	
	// submit job to cluster
	if ($_POST['process']=="Create Tomogram") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTomoMakerForm("<B>ERROR:</B> You must be logged in to submit");
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'tomomaker',True,True);
		// if errors:
		if ($sub) createTomoMakerForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runname.'/'.$runname.'.appionsub.log';
		$status = "Tomogram was uploaded";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while creating tomogram, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Make Tomogram", "Make Tomogram");
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
	<TR><TD>tomo name</TD><TD>$tomofilename</TD></TR>
	<TR><TD>transform file</TD><TD>$xffilename</TD></TR>
	<TR><TD>snapshot file</TD><TD>$snapshot</TD></TR>
	<TR><TD>apix</TD><TD>$apix</TD></TR>
	<TR><TD>tiltseries number</TD><TD>$tiltseriesnumber</TD></TR>
	<TR><TD>runname</TD><TD>$runname</TD></TR>
	<TR><TD>volume</TD><TD>$volume</TD></TR>
	<TR><TD>session</TD><TD>$sessionname</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
	processing_footer();
}


?> 

