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
	if ($_GET['lastaId']) {
		$lastalignerId = $_GET['lastaId'];
	}
	$particle = new particledata();

	$projectId=$_SESSION['projectId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&lastaId=$lastalignerId";
	
	$javafunctions .= writeJavaPopupFunctions('appion');  
	
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font COLOR='RED'>$extra</font>\n<HR>\n";
	}
  
	echo"<FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
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

	// Set any existing parameters in form that does not depend on other values
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	$tiltseriesId2 = ($_POST['tiltseriesId2']) ? $_POST['tiltseriesId2'] : NULL;
	$alignruns = $particle->countTomoAlignmentRuns($tiltseriesId);
	$autorunname = ($alignruns) ? 'align'.($alignruns+1):'align1';
	$runname = ($_POST['lasttiltseries']==$tiltseriesId) ? $_POST['runname']:$autorunname;
	$description = $_POST['description'];
	$protomocheck = ($_POST['alignmethod'] == 'protomo' || !($_POST['alignmethod'])) ? "CHECKED" : "";
	$imodcheck = ($_POST['alignmethod'] == 'imod-shift') ? "CHECKED" : "";
	echo"
  <table border=3 class=tableborder>
  <tr>
    <td Valign='TOP'>\n";
	echo"	<table border=3 class=tableborder>
				<tr>
					<td Valign='TOP'>\n";
	$leginondata = new leginondata();
	if ($lastalignerId) {
		$refinedata = $particle->getProtomoAlignmentInfo($lastalignerId);
		//get image size
		$imageinfo = $leginondata->getImageInfo($refinedata[0]['image']);
		$imagesize = ($_POST['imagesize']) ? $_POST['imagesize'] : $imageinfo['dimx'];
		$showncycles = $particle->getProtomoAlignerInfoFromAlignmentRun($refinedata[0]['alignrunid'],False);
		//good  cycle selector
		$validcycles = $showncycles;
		$i = 0;
		foreach ($showncycles as $cycle) {
			if ($cycle['alignerid'] >= $lastalignerId) {
				array_splice($validcycles,$i);
			} else {
				$i += 1;
			}
		}
		$alignerkey = (!is_null($_POST['goodalignerkey'])) ? $_POST['goodalignerkey'] : count($validcycles)-1;
		$alignerselector_array = $particle->getTomoAlignerSelector($validcycles, $alignerkey,'goodalignerkey');
		echo "<p>";
		//get valid region range
		$goodrefinedata = $particle->getProtomoAlignmentInfo($validcycles[$alignerkey]['alignerid']);
		$shiftmax = 0;
		foreach ($goodrefinedata as $r) {
			$shiftmax = ($shiftmax < abs($r['shift x'])) ? abs($r['shift x']) : $shiftmax; 
			$shiftmax = ($shiftmax < abs($r['shift y'])) ? abs($r['shift y']) : $shiftmax; 
		}
		$maxregion = 100 - floor(100 * 2 * $shiftmax / $imagesize);
		echo "<input type='hidden' name='maxregion' value='$maxregion'>\n";
		//determine accepted alignment numbers
		$runname = $refinedata[0]['runname'];
		$minx = ($_POST['minx'] && $_POST['minx'] >= 0) ? $_POST['minx'] : 0;	
		$maxx = ($_POST['maxx'] && $_POST['maxx'] < count($refinedata)) ? $_POST['maxx'] : count($refinedata)-1;
		if ($minx or $maxx != count($refinedata)) {
			echo "<img border='0' src='tomoaligngraph.php?w=512&h=256&aId=$lastalignerId&box=1"
				."&minx=$minx&maxx=$maxx&expId=$expId'><br/>\n";
		} else {
			echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$lastalignerId&expId=$expId&box=1'><br/>\n";
		}
		echo docpop('protomoreset','Reset alignment');
		echo " outside the ";
		echo docpop('protomoresetrange','range of the image number');
		echo " <p>\n";
		echo "from <input type='text' name='minx' onchange=submit() value='$minx' size='7'> to";
		echo " <input type='text' name='maxx' onchange=submit() value='$maxx' size='4'>\n";
		echo docpop('protomogoodcycle','back to iteration');
		echo $alignerselector_array[0];
	} else {
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
		echo "</td><td Valign='TOP'>\n";
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
		$imageinfo = $leginondata->getImageInfo($tiltseriesinfos[0]['imageid']);
		$imagesize = ($_POST['imagesize']) ? $_POST['imagesize'] : $imageinfo['dimx'];
	}
	echo "<input type='hidden' name='imagesize' value='$imagesize'>\n";
	echo "</td></table>";
	echo "<p>";
	//runname
	echo docpop('tomoalignrunname', 'Runname');
	if ($lastalignerId) {
		echo " ".$runname;
		echo "<input type='hidden' name='runname' value='$runname'>\n";
	} else {
    echo "<input type='text' name='runname' value='$runname' size='10'>\n";
	} 
	//description
	echo"<P>
      <b>Alignment Description:</b><br>
      <textarea name='description' ROWS='2' COLS='40'>$description</textarea>
			<p>\n";
	echo docpop('tomoalignmethod', 'Method');
	echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='protomo' $protomocheck>\n";
	echo "Protomo refinement<font size=-2><i>(default)</i></font>\n";
	if (!$lastalignerId) {
		echo "&nbsp;<input type='radio' onClick=submit() name='alignmethod' value='imod-shift' $imodcheck>\n";
		echo "Imod shift-only alignment\n";
	}
  echo "</td>
    </tr>
    <tr>
      <td Valign='TOP' class='tablebg'>";       
	if ($protomocheck) {
		if ($lastalignerId) {
			$lastalignparams = $refinedata[0];
			$defsample = 1;
			$sampleset = array(8,4,2,1.5,1);
			foreach ($sampleset as $s) {
				if ($lastalignparams['alismp'] > $s) {
					$defsample = $s;
					break;
				}
			}
			if ($defsample < 2) {
				$defregion = floor(0.95 * min($maxregion,100));
			} else {
				$defregion = floor(100 * $lastalignparams['SUBD|alibox|x'] *  $lastalignparams['alismp'] / $imagesize);
			}
			$defcycle = $lastalignparams['cycle'] + 1;
		} else {
			$defsample = ($imagesize) ? ceil($imagesize/512) : 4;
			$defregion = 50;
			$defcycle = 1;
		}
		$cycle = ($_POST['cycle']) ? $_POST['cycle'] : $defcycle;
		$sample = ($_POST['sample']) ? $_POST['sample'] : $defsample;
		$region = ($_POST['region']) ? $_POST['region'] : $defregion;
		echo "
			<b> <center>Tilt Series Alignment Params: </center></b>
      <P>";
		echo docpop('protomocycle','Alignment iteration');
		echo " ".$cycle;
		echo "<input type='hidden' name='cycle' value='$cycle'>\n";
		echo "<p>
      <input type='text' name='sample' size='5' value='$sample'>\n";
		echo docpop('protomosample','Alignment Sampling');
		echo "<font>(>=1.0)</font>
		<p>
      <input type='text' name='region' size='8' value='$region'>\n";
		echo docpop('protomoregion','Protomo Alignment Region');
		echo "<font>(% of image length (<100))</font>
		<p>";
		echo "Maximum region calculated from previous alignment is ".$maxregion;
	}
	if (!$sessionname) {
		echo "
		<br>
      <input type='text' name='sessionname' value='$sessionname' size='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<font> (leginon session name)</font>";
	}
		echo "	  		
		<P>
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

	if ($_GET['lastaId']) {
		$lastalignerId = $_GET['lastaId'];
		$goodstart=$_POST['minx'];
		$goodend=$_POST['maxx'];
	}
	$description=$_POST['description'];
	$tiltseriesId=$_POST['tiltseriesId'];
	$tiltseriesId2=$_POST['tiltseriesId2'];
	$runname=$_POST['runname'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$alignmethod = $_POST['alignmethod'];
	$cycle=$_POST['cycle'];
	$sample=$_POST['sample'];
	$region=$_POST['region'];
	$maxregion=$_POST['maxregion'];

	$command.="--session=$sessionname ";
	//make sure the protomo sampling is valid
	if ($sample < 1 && $alignmethod=='protomo') createTomoAlignerForm("<b>ERROR:</b> Sampling must >= 1");
	if (!$lastalignerId) {
		//make sure a tilt series was provided
		if (!$tiltseriesId) createTomoAlignerForm("<b>ERROR:</b> Select the tilt series");
		//make sure a description was provided
		if (!$description) createTomoAlignerForm("<b>ERROR:</b> Enter a brief description of the tomogram");
		$particle = new particledata();
		$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
		$tiltseriesnumber = $tiltseriesinfos[0]['number'];
		$command.="--tiltseriesnumber=$tiltseriesnumber ";
		if ($tiltseriesId2) {
			$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId2);
			$tiltseriesnumber2 = $tiltseriesinfos[0]['number'];
			$command.="--othertilt=$tiltseriesnumber2 ";
		}	
	} else {
		//make sure the region is not too large
		if ($maxregion < $region) 
			createTomoAlignerForm("<b>ERROR:</b> The alignment region can not be larger than ".$maxregion." % of the image");
		$command.="--goodaligner=$lastalignerId ";
		$command.="--goodstart=$goodstart ";
		$command.="--goodend=$goodend ";
	}
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
	// submit job to cluster
	if ($_POST['process']=="Align Tilt Series") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTomoAlignerForm("<b>ERROR:</b> You must be logged in to submit");
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
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>Tilt Series Aligning Command:</b><br>
	$command
	</td></tr>
	<tr><td>tiltseries number</td><td>$tiltseriesnumber</td></tr>
	<tr><td>runname</td><td>$runname</td></tr>
	<tr><td>region</td><td>$region</td></tr>
	<tr><td>session</td><td>$sessionname</td></tr>
	<tr><td>description</td><td>$description</td></tr>
	</table>\n";
	processing_footer();
}


?> 

