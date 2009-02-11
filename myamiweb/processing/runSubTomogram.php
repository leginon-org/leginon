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
	runSubTomogram();
}

// Create the form page
else {
	createSubTomogramForm();
}

function createSubTomogramForm($extra=false, $title='tomomaker.py Launcher', $heading='Create Tomogram Subvolume from Particle Picks') {
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
	}

	// Set any existing parameters in form
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	$tiltseriesnumber = ($_POST['tiltseriesnumber']) ? $_POST['tiltseriesnumber'] : NULL;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'subtomo1';
	$fulltomoval = ($_POST['fulltomoId']) ? $_POST['fulltomoId'] : NULL;
	$prtlrunval = ($_POST['prtlrunId']) ? $_POST['prtlrunId'] : NULL;
	$sizex = ($_POST['sizex']) ? $_POST['sizex'] : NULL;
	$sizey = ($_POST['sizey']) ? $_POST['sizey'] : NULL;
	$sizez = ($_POST['sizez']) ? $_POST['sizez'] : 100;
	$offsetz = ($_POST['offsetz']) ? $_POST['offsetz'] : 0;
	$description = $_POST['description'];

	$alltiltseries = $particle->getTiltSeries($expId);
	$prtlrunIds = $particle->getParticleRunIds($expId);
	$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId); 
	$tiltSeriesSelector = $seriesselector_array[0];
  
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	
	$prtlruns=count($prtlrunIds);

	if (!$prtlrunIds) {
		echo"<font class='apcomment' size='+2'><b>No Particles for this Session</b></font>\n";
	}
	else {
		echo docpop('stackparticles','Particles:');
		echo "<select name='prtlrunId'onchange=submit()>\n";
		foreach ($prtlrunIds as $prtlrun){
			$prtlrunId=$prtlrun['DEF_id'];
			$prtlrunname=$prtlrun['name'];
			$prtlstats=$particle->getStats($prtlrunId);
			$totprtls=commafy($prtlstats['totparticles']);
			echo "<OPTION value='$prtlrunId'";
			// select previously set prtl on resubmit
			if ($prtlrunval==$prtlrunId) {
				echo " SELECTED";
				$runname = 'subtomo_pick'.$prtlrunval;
			}
			echo">$prtlrunname ($totprtls prtls)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo "<br/>\n";
  echo "<P>";
	echo docpop('subtomorunname','Runname');
  echo "<INPUT TYPE='text' NAME='runname' SIZE='15' VALUE='$runname'>\n";
	echo "<FONT>(subtomogram creating run name)</FONT>
		<br/>";
	echo "
      <P>";
	echo docpop('tomobox','Box size');
	echo "
      <INPUT TYPE='text' NAME='sizex' SIZE='5' VALUE='$sizex'>\n
      <INPUT TYPE='text' NAME='sizey' SIZE='5' VALUE='$sizey'>\n
      <INPUT TYPE='text' NAME='sizez' SIZE='5' VALUE='$sizez'>\n";
	echo "<FONT>(boxing size in (x,y,z)</FONT>
		<br />";
	echo "
      <P>";
	echo docpop('zoffset','Box center in z');
	echo "
      <INPUT TYPE='text' NAME='offsetz' SIZE='5' VALUE='$offsetz'>\n";
	echo "<FONT>(pixels on full tomogram)</FONT>
		<br />";
	echo"<P>
			<B> Sub-Tomogram Description:</B><BR/>
			<TEXTAREA NAME='description' ROWS='2' COLS='40'>$description</TEXTAREA>
		  </TD>
    </TR>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>";       


	echo "
		<B> <CENTER>Tomogram Params: </CENTER></B>
    <P>";
	echo $seriesselector_array[0];
	echo docpop('tiltseries', 'Tilt Series');
   
	if (!$sessionname) {
		echo "
			<BR>
      <INPUT TYPE='text' NAME='sessionname' VALUE='$sessionname' SIZE='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<FONT> (leginon session name)</FONT>";
	}
	if ($tiltseriesId) {
		$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
		$tiltseriesnumber = $tiltseriesinfos[0]['number'];
		$outdir .= '/tiltseries'.$tiltseriesnumber;
		echo "<input type='hidden' name='tiltseriesnumber' value='$tiltseriesnumber'>\n";
		$fulltomos = $particle->checkforFullTomogram($tiltseriesId);
		$tomoruns=count($fulltomos);
		echo "<p><br />";
		if (!$fulltomos) {
			echo"<font class='apcomment' size='+2'><b>No Full Tomograms for this tilt series</b></font>\n";
		}
		else {
			echo docpop('tomorunname', 'Full tomogram');
			echo "<select name='fulltomoId'onchange=submit()>\n";
			foreach ($fulltomos as $fulltomo){
				$fulltomoId = $fulltomo['DEF_id'];
				echo "<OPTION value='$fulltomoId'";
				// select previously set prtl on resubmit
				if ($fulltomoval==$fulltomoId) {
					echo " SELECTED";
					$outdir .= '/'.$fulltomo['runname'];
				}
				echo ">".$fulltomo['runname']." </OPTION>\n";
			}
			echo "</SELECT>\n";
			echo "<FONT>(full tomogram reconstruction)</FONT>";     
			echo "<input type='hidden' name='outdir' value='$outdir'>\n";
		}
	}	
	echo "	  		
		<p><br />
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
	echo getSubmitForm("Create SubTomogram");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runSubTomogram() {

	$projectId=$_SESSION['projectId'];
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "tomomaker.py ";

	$xffilename=$_POST['xffilename'];
	$tiltseriesId=$_POST['tiltseriesId'];
	$tiltseriesnumber = $_POST['tiltseriesnumber'];
	$runname=$_POST['runname'];
	$prtlrunId=$_POST['prtlrunId'];
	$sizex=$_POST['sizex'];
	$sizey=$_POST['sizey'];
	$sizez=$_POST['sizez'];
	$offsetz=$_POST['offsetz'];
	$sessionname=$_POST['sessionname'];
	$fulltomoId=$_POST['fulltomoId'];

	//make sure a tilt series was provided
	if (!$tiltseriesId) createSubTomogramForm("<B>ERROR:</B> Select the tilt series");
//make sure a tomogram was entered
	if (!$runname) createSubTomogramForm("<B>ERROR:</B> Select a full tomogram to be boxed");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createSubTomogramForm("<B>ERROR:</B> Enter a brief description of the tomogram");

	$particle = new particledata();

	$command.="--session=$sessionname ";
	$command.="--tiltseries=$tiltseriesnumber ";
	$command.="--projectid=$projectId ";
	$command.="--fulltomoId=$fulltomoId ";
	$command.="--runname=$runname ";
	$command.="--selexonId=$prtlrunId ";
	$command.="--sizex=$sizex ";
	$command.="--sizey=$sizey ";
	if ($sizez > 0)
		$command.="--sizez=$sizez ";
	$command.="--offsetz=$offsetz ";
	$command.="--description=\"$description\" ";
	$command.="--subvolumeonly ";

	// submit job to cluster
	if ($_POST['process']=="Create SubTomogram") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createSubTomogramForm("<B>ERROR:</B> You must be logged in to submit");
		$rundir = $outdir.'/'.$runname;
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'tomomaker',True,True);
		// if errors:
		if ($sub) createSubTomogramForm("<b>ERROR:</b> $sub");

		// check that process finished properly
		$jobf = $rundir.'/'.$runname.'.appionsub.log';
		$status = "SubTomograms were created";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while processing, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Creating SubTomogram", "Create SubTomogram");
		echo "$status\n";
	}

	else processing_header("SubTomogram Command","SubTomogram Command");
	
	// rest of the page
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>SubTomogram Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>subtomogram runname</TD><TD>$runname</TD></TR>
	<TR><TD>particle selection id</TD><TD>$prtlrunId</TD></TR>
	<TR><TD>tiltseries number</TD><TD>$tiltseriesnumber</TD></TR>
	<TR><TD>fulltomogram id</TD><TD>$fulltomoId</TD></TR>
	<TR><TD>session</TD><TD>$sessionname</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
	processing_footer();
}

?> 

