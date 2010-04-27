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

// IF valueS SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runTomoMaker();
}

// Create the form page
else {
	createTomoMakerForm();
}

function createTomoMakerForm($extra=false, $title='tomomaker.py Launcher', $heading='Run Tomogram Maker') {
	// check if coming directly from a session
	$expId=$_GET['expId'];

	$particle = new particledata();

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	
	$javafunctions .= writeJavaPopupFunctions('appion');  
	
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<form name='viewerform' method='POST' action='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$extrabin = ($_POST['extrabin']) ? $_POST['extrabin'] : '1';
	$thickness = ($_POST['thickness']) ? $_POST['thickness'] : '200';
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	$tiltseriesId2 = ($_POST['tiltseriesId2']) ? $_POST['tiltseriesId2'] : NULL;
	$alignruns = $particle->countFullTomograms($tiltseriesId);
	$alignerId = ($_POST['alignerId']) ? $_POST['alignerId'] : NULL;
	$autorunname = ($alignruns) ? 'full'.($alignruns+1):'full1';
	$runname = ($_POST['lasttiltseries']==$tiltseriesId) ? $_POST['runname']:$autorunname;
	$excludenumber = ($_POST['exclude']) ? $_POST['exclude']:'';
	$description = $_POST['description'];

	$alltiltseries = $particle->getTiltSeries($expId);
	$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId); 
	$tiltSeriesSelector = $seriesselector_array[0];
	echo "<input type='hidden' name='lasttiltseries' value='$tiltseriesId'>\n";
	$aligners = array();
	$alignIds = array();
	if ($tiltseriesId) {
		$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
		if (!empty($sessioninfo)) {
			$outdir=$sessioninfo['Image path'];
			$outdir=ereg_replace("leginon","appion",$outdir);
			$outdir=ereg_replace("rawdata","tomo/tiltseries".$tiltseriesinfos[0]['number'],$outdir);
			echo "<input type='hidden' name='outdir' value='$outdir'>\n";
		}
		$alignruns = $particle ->getTomoAlignmentRuns($tiltseriesId);
		if ($alignruns) {
			foreach ($alignruns as $run) {
				$alignId = $run['alignrunId'];
				$caligners =  $particle -> getTomoAlignerInfoFromAlignmentRun($alignId,false);
				if (!$caligners) $caligners = array();
				$aligners = array_merge($aligners, $caligners);
			}
		} else {
			$tiltseriesinfos = array();
		}
  } else {
		$tiltseriesinfos = array();
	}
	$alignerselector_array = $particle->getTomoAlignRunAlignerSelector($aligners, $alignerId,'alignerId');
	echo"
  <table border=3 class=tableborder>
  <tr>
    <td valign='TOP'>\n";
	echo"	<table border=3 class=tableborder>
				<tr>
					<td valign='TOP'>\n";
	echo $seriesselector_array[0];
	echo docpop('tiltseries', 'Choose a tilt series involved in the align run');
	if (count($tiltseriesinfos) && $tiltseriesId) {
		echo "
		<br/><b>First Image in the Tilt Series:</b><br/>"
			.$tiltseriesinfos[0]['filename'];
		echo "</td></tr><tr><td>";
		if (count($aligners)) {
			echo docpop('tomoaligner', 'Choose an alignment for tomogram creation');
			echo "<br/>";
			echo $alignerselector_array[0];
			$selection = $alignerselector_array[1];
			$currentaligner = (is_null($selection)) ? $aligners[0]['alignerid']:$selection;
		} else {
			echo "<b>No alignment available for reconstruction</b>";
		}
	} else {
		if ($tiltseriesId)
			echo "<br/><b>Bad Tilt Series! Do not use.</b><br/>";
	}
	echo "</td></tr></table>";
	if ($currentaligner) {
		echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$currentaligner&expId=$expId&type=shifty'><br/>\n";
		echo "<p>
			<input type='text' name='exclude' value='$excludednumber' size='10'>\n";
		echo docpop('tomoexclude', 'Exclude Images');
		echo "<p>
			<input type='text' name='runname' value='$runname' size='10'>\n";
		echo docpop('tomorunname', 'Runname');
		echo "<font>(full tomogram reconstruction run name)</font>";     
	
		echo"<P>
			  <b>Tomogram Description:</b><br>
				<textarea name='description' ROWS='2' COLS='40'>$description</textarea>
				</td>
			</tr>
			<tr>
				<td valign='TOP' class='tablebg'>";       

		echo "
			<b> <center>Tomogram Creation Params: </center></b>
				<P>
				<input type='text' name='extrabin' size='5' value='$extrabin'>\n";
			echo docpop('extrabin','Binning');
			echo "<font>(additional binning in tomogram)</font>
			<p>
				<input type='text' name='thickness' size='8' value='$thickness'>\n";
			echo docpop('tomothickness','Tomogram Thickness');
			echo "<font>(pixels in tilt images)</font>
			<p><br />";
	}
	if (!$sessionname) {
		echo "
		<br>
      <input type='text' name='sessionname' value='$sessionname' size='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<font> (leginon session name)</font>";
		echo "<P>";
	}
		echo "	  		
      </td>
   </tr>
    </table>
  </td>
  </tr>
  <td
  <tr>
    <td align='center'>
      <hr>
	";
	if ($currentaligner) {
		echo getSubmitForm("Make Tomogram");
	}
		echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runTomoMaker() {

	$projectId=getProjectId();
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "tomomaker.py ";

	$alignerId=$_POST['alignerId'];
	$runname=$_POST['runname'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$extrabin=$_POST['extrabin'];
	$thickness=$_POST['thickness'];
	$excludenumber=$_POST['exclude'];

	//make sure a tilt series was provided
	if (!$alignerId) createTomoMakerForm("<b>ERROR:</b> Select the alignment");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createTomoMakerForm("<b>ERROR:</b> Enter a brief description of the tomogram");

	$command.="--session=$sessionname ";
	$command.="--bin=$extrabin ";
	$command.="--alignerid=$alignerId ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
	$command.="--thickness=$thickness ";
	$command.="--exclude=$excludenumber ";
	$command.="--description=\"$description\" ";
	$command.="--commit ";
	// submit job to cluster
	if ($_POST['process']=="Make Tomogram") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTomoMakerForm("<b>ERROR:</b> You must be logged in to submit");
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'tomomaker',False,False,False);
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

	else processing_header("Tomogram Making Command","Tomogram Making Command");
	
	// rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>Full Tomogram Making Command:</b><br>
	$command
	</td></tr>
	<tr><td>aligner</td><td>$alignerId</td></tr>
	<tr><td>runname</td><td>$runname</td></tr>
	<tr><td>thickness</td><td>$thickness</td></tr>
	<tr><td>session</td><td>$sessionname</td></tr>
	<tr><td>description</td><td>$description</td></tr>
	</table>\n";
	processing_footer();
}


?> 

