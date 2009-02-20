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
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	// Runname is determined by tiltseries if not manually set
	$alignruns = $particle->countTomoAlignmentRuns($tiltseriesId);
	$autorunname = 'upload'.($alignruns+1);
	$runname = ($_POST['lasttiltseries']==$tiltseriesId) ? $_POST['runname']:$autorunname;
	// Volumename is determined by tiltseries amd runname if not manually set
	$volumeruns = $particle->countTomogramsByAlignment($tiltseriesId,$runname);
	$autovolumename = 'volume'.($volumeruns+1);
	$volume = ($_POST['lastrunname']==$runname && $_POST['lasttiltseries']==$tiltseriesId) ? $_POST['volume']:$autovolumename;
	$tomofilename = ($_POST['tomofilename']) ? $_POST['tomofilename'] : '';
	$xffilename = ($_POST['xffilename']) ? $_POST['xffilename'] : '';
	$snapshot = ($_POST['snapshot']) ? $_POST['snapshot'] : '';
	$description = $_POST['description'];
	$outdir .= $tomofilename.'mrc';

	$alltiltseries = $particle->getTiltSeries($expId);
	$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId); 
	$tiltSeriesSelector = $seriesselector_array[0];
	// Need these to notify that the values has changed in the next reload
	echo "<input type='hidden' name='lasttiltseries' value='$tiltseriesId'>\n";
	echo "<input type='hidden' name='lastrunname' value='$runname'>\n";
  
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	
  echo"
	<B>Original Tomogram file name with path:</B><BR/>
      <INPUT TYPE='text' NAME='tomofilename' VALUE='$tomofilename' SIZE='50'><br />\n
	<B>Original Full Tomogram Transform file name (.xf) with path:</B><BR/>
      <INPUT TYPE='text' NAME='xffilename' VALUE='$xffilename' SIZE='50'><br />\n
	<B>Original Snapshot file name with path:</B><BR/>
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
		<p><br />";
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
		<p><br />
      <INPUT TYPE='text' NAME='runname' VALUE='$runname' SIZE='5'>\n";
		echo docpop('tomorunname', 'Runname');
   	echo "<FONT>(full tomogram reconstruction run name)</FONT>";     
		echo "	  		
		<p><br />
      <INPUT TYPE='text' NAME='volume' VALUE='$volume' SIZE='5'>\n";
		echo docpop('volume', 'Volume');
   	echo "<FONT>(subvolume name)</FONT>     

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

	$projectId=$_SESSION['projectId'];
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "uploadTomo.py ";

	$tomofilename=$_POST['tomofilename'];
	$xffilename=$_POST['xffilename'];
	$tiltseriesId=$_POST['tiltseriesId'];
	$runname=$_POST['runname'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$extrabin=$_POST['extrabin'];
	$snapshot=$_POST['snapshot'];

	//make sure a tilt series was provided
	if (!$tiltseriesId) createUploadTomogramForm("<B>ERROR:</B> Select the tilt series");
//make sure a tomogram was entered
	if (!$tomofilename) createUploadTomogramForm("<B>ERROR:</B> Enter a tomogram to be uploaded");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createUploadTomogramForm("<B>ERROR:</B> Enter a brief description of the tomogram");

	$particle = new particledata();
	$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
	$apix = $tiltseriesinfos[0]['ccdpixelsize'] * $tiltseriesinfos[0]['imgbin'] * $extrabin * 1e10;
	$tiltseriesnumber = $tiltseriesinfos[0]['number'];

	$command.="--file=$tomofilename ";
	$command.="--session=$sessionname ";
	$command.="--bin=$extrabin ";
	$command.="--tiltseries=$tiltseriesnumber ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
	if ($volume) $command.="--volume=$volume ";
	if ($xffilename) $command.="--xffile=$xffilename ";
	$command.="--description=\"$description\" ";
  if ($snapshot) 
		$command.="--image=$snapshot ";

	
	// submit job to cluster
	if ($_POST['process']=="Upload Tomogram") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadTomogramForm("<B>ERROR:</B> You must be logged in to submit");
		$uploaddir = $outdir.'/'.$runname;
		$sub = submitAppionJob($command,$uploaddir,$volume,$expId,'uploadtomo',True,True);
		// if errors:
		if ($sub) createUploadTomogramForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $uploaddir.'/'.$volume.'/'.$volume.'.appionsub.log';
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

