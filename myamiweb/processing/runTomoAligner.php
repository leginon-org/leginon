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
	runTomoAligner();
}

// Create the form page
else {
	createTomoAlignerForm();
}

function createTomoAlignerForm($extra=false, $title='tomoaligner.py Launcher', $heading='Run Tilt Series Aligner') {
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
	$cycle = ($_POST['cycle']) ? $_POST['cycle'] : '1';
	$sample = ($_POST['sample']) ? $_POST['sample'] : '4';
	$region = ($_POST['region']) ? $_POST['region'] : '50';
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	$tiltseriesId2 = ($_POST['tiltseriesId2']) ? $_POST['tiltseriesId2'] : NULL;
	$alignruns = $particle->countTomoAlignmentRuns($tiltseriesId);
	$autorunname = ($alignruns) ? 'align'.($alignruns+1):'align1';
	$runname = ($_POST['lasttiltseries']==$tiltseriesId) ? $_POST['runname']:$autorunname;
	$description = $_POST['description'];
	$protomocheck = ($_POST['alignmethod'] == 'protomo' || !($_POST['alignmethod'])) ? "CHECKED" : "";
	$imodcheck = ($_POST['alignmethod'] == 'imod-shift') ? "CHECKED" : "";
	// Select tilt series
	$alltiltseries = $particle->getTiltSeries($expId);
	$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId); 
	$seriesselector_array2 = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId2,'tiltseriesId2'); 
	$tiltSeriesSelector = $seriesselector_array[0];
	echo "<input type='hidden' name='lasttiltseries' value='$tiltseriesId'>\n";
	if ($tiltseriesId) {
		$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
  } else {
		$tiltseriesinfos = array();
	}
	$tiltSeriesSelector2 = $seriesselector_array2[0];
	if ($tiltseriesId2) {
		$tiltseriesinfos2 = $particle ->getTiltSeriesInfo($tiltseriesId2);
  } else {
		$tiltseriesinfos2 = array();
	}
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	echo"	<TABLE BORDER=3 CLASS=tableborder>
				<TR>
					<TD VALIGN='TOP'>\n";
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
	echo "</TD><TD VALIGN='TOP'>\n";
	echo $seriesselector_array2[0];
	echo docpop('tiltseriestwo', '2ndary Tilt Series');
	if (count($tiltseriesinfos2) && $tiltseriesId2) {
		if ($tiltseriesId2==$tiltseriesId){
			echo "<br/><b>2nd tilt series must be different.</b><br/>";
		} else {
			echo "
				<br/><b>First Image in the Tilt Series:</b><br/>"
				.$tiltseriesinfos2[0]['filename'];
		}
	} else {
		if ($tiltseriesId2)
			echo "<br/><b>Bad Tilt Series! Do not use.</b><br/>";
	}
	echo "</td></table>";
	echo "<p>
    <INPUT TYPE='text' NAME='runname' VALUE='$runname' SIZE='10'>\n";
	echo docpop('tomorunname', 'Runname');
  echo "<FONT>(alignment run name)</FONT>";     
	
	echo"<P>
      <B>Alignment Description:</B><br>
      <TEXTAREA NAME='description' ROWS='2' COLS='40'>$description</TEXTAREA>
			<p>\n";
	echo docpop('tomoalignmethod', 'Method');
  echo "<FONT>(alignment method)</FONT>";     
	echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='protomo' $protomocheck>\n";
	echo "Protomo refinement<font size=-2><i>(default)</i></font>\n";
	echo "&nbsp;<input type='radio' onClick=submit() name='alignmethod' value='imod-shift' $imodcheck>\n";
	echo "Imod shift-only alignment\n";
  echo "</TD>
    </tr>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>";       
	if ($protomocheck) {
		echo "
			<B> <CENTER>Tilt Series Alignment Params: </CENTER></B>
      <P>
      <INPUT TYPE='text' NAME='cycle' SIZE='5' VALUE='$cycle'>\n";
		echo docpop('protomocycle','Alignment iteration');
		echo "<p>
      <INPUT TYPE='text' NAME='sample' SIZE='5' VALUE='$sample'>\n";
		echo docpop('protomosample','Alignment Sampling');
		echo "<FONT>(>=1.0)</FONT>
		<p>
      <INPUT TYPE='text' NAME='region' SIZE='8' VALUE='$region'>\n";
		echo docpop('protomoregion','Protomo Alignment Region');
		echo "<FONT>(% of image length (<100))</FONT>
		<p><br />";
	}
	if (!$sessionname) {
		echo "
		<br>
      <INPUT TYPE='text' NAME='sessionname' VALUE='$sessionname' SIZE='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<FONT> (leginon session name)</FONT>";
	}
		echo "	  		
		<P>
      </TD>
   </tr>
    </table>
  </TD>
  </tr>
  <td

  <TR>
    <TD ALIGN='CENTER'>
      <hr>
	";
	echo getSubmitForm("Align Tilt Series");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runTomoAligner() {

	$projectId=$_SESSION['projectId'];
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "tomoaligner.py ";

	$tiltseriesId=$_POST['tiltseriesId'];
	$tiltseriesId2=$_POST['tiltseriesId2'];
	$runname=$_POST['runname'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$alignmethod = $_POST['alignmethod'];
	$cycle=$_POST['cycle'];
	$sample=$_POST['sample'];
	$region=$_POST['region'];

	//make sure a tilt series was provided
	if (!$tiltseriesId) createTomoAlignerForm("<B>ERROR:</B> Select the tilt series");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createTomoAlignerForm("<B>ERROR:</B> Enter a brief description of the tomogram");

	$particle = new particledata();
	$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
	$tiltseriesnumber = $tiltseriesinfos[0]['number'];

	$command.="--session=$sessionname ";
	$command.="--tiltseriesnumber=$tiltseriesnumber ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
	$command.="--alignmethod=$alignmethod ";
	if ($alignmethod == 'protomo') {
		$command.="--cycle=$cycle ";
		$command.="--sample=$sample ";
		$command.="--region=$region ";
	}
	$command.="--description=\"$description\" ";
	$command.="--commit ";
	if ($tiltseriesId2) {
		$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId2);
		$tiltseriesnumber = $tiltseriesinfos[0]['number'];
		$command.="--othertilt=$tiltseriesnumber ";
	}	
	// submit job to cluster
	if ($_POST['process']=="Align Tilt Series") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTomoAlignerForm("<B>ERROR:</B> You must be logged in to submit");
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'tomoaligner',True,True);
		// if errors:
		if ($sub) createTomoAlignerForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runname.'/'.$runname.'.appionsub.log';
		$status = "Alignment result was uploaded";
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
		processing_header("Align Tilt Series", "Align Tilt Series");
		echo "$status\n";
	}

	else processing_header("Tilt Series Aligning Command","Tilt Series Aligning Command");
	
	// rest of the page
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>Tilt Series Aligning Command:</B><br>
	$command
	</TD></tr>
	<TR><td>tiltseries number</TD><td>$tiltseriesnumber</TD></tr>
	<TR><td>runname</TD><td>$runname</TD></tr>
	<TR><td>region</TD><td>$region</TD></tr>
	<TR><td>session</TD><td>$sessionname</TD></tr>
	<TR><td>description</TD><td>$description</TD></tr>
	</table>\n";
	processing_footer();
}


?> 

