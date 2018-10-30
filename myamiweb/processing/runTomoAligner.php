<?php
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Simple viewer to view a image using mrcmodule
 */


require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/forms/ddstackSelectTable.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runTomoAligner();
}

// Create the form page
else {
	createTomoAlignerForm();
}

function buildOutdir($sessioninfo,$tiltseriesnumber) {
	$outdir=$sessioninfo;
	$outdir=getBaseAppionPath($sessioninfo);
	$outdir .="/tomo/tiltseries".$tiltseriesnumber;
	$outdir=$outdir.'/align';
	return $outdir;	
}

function createTomoAlignerForm($extra=false, $title='tomoaligner.py Launcher', $heading='Run Tilt Series Aligner') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($_GET['lastaId']) {
		$lastalignerId = $_GET['lastaId'];
	}
	$particle = new particledata();

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&lastaId=$lastalignerId";
	
	$javafunctions .= writeJavaPopupFunctions('appion');  
	
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	$ddstackform = new DDStackSelectTable($expId);

	echo"<FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}
	// Set any existing parameters in form that does not depend on other values
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	$tiltseriesId2 = ($_POST['tiltseriesId2']) ? $_POST['tiltseriesId2'] : NULL;
	// Set alignmethod
	$defaultmethod = ($lastalignerId)? 'protomo': 'leginon';
	$alignmethod = ($_POST['alignmethod']) ? $_POST['alignmethod'] : $defaultmethod;
	$leginoncheck = ($_POST['alignmethod'] == 'leginon' || !($_POST['alignmethod'])) ? "CHECKED" : "";
	$imodcheck = ($_POST['alignmethod'] == 'imod-shift') ? "CHECKED" : "";

	$runtypes = array('leginon'=>'leginon','imod-shift'=>'imodxc','protomo'=>'protomo');
	$alignruns = $particle->countTomoAlignmentRuns($tiltseriesId);
	$autorunname = ($alignruns) ? $runtypes[$alignmethod].($alignruns+1):$runtypes[$alignmethod].'1';
	$runname = ($_POST && $_POST['lasttiltseries']==$tiltseriesId && $_POST['lastalignmethod']==$alignmethod && $_POST['lastrunname'] && $_POST['lastrunname']!=$_POST['runname']) ? $_POST['runname']:$autorunname;
	$description = $_POST['description'];
	// protomo2 parameters
	$maxIteration = $_POST['maxIteration'];
	$alignSample = $_POST['alignSample'];
	$windowX = $_POST['windowX'];
	$windowY = $_POST['windowY'];
	$LdiameterX = $_POST['LdiameterX'];
	$LdiameterY = $_POST['LdiameterY'];
	$HdiameterX = $_POST['HdiameterX'];
	$HdiameterY= $_POST['HdiameterY'];

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
		$tiltseriesinfos = $particle ->getTiltSeriesInfo($refinedata[0]['tiltseries']);
		//get image size
		$imageinfo = $leginondata->getImageInfo($refinedata[0]['image']);
		$imagesize = ($_POST['imagesize']) ? $_POST['imagesize'] : $imageinfo['dimx'];
		$showncycles = $particle->getTomoAlignerInfoFromAlignmentRun($refinedata[0]['alignrunid'],False);
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
		$alignerkey = (!is_null($_POST['goodcycle'])) ? $_POST['goodcycle'] : count($validcycles)-1;
		$alignerselector_array = $particle->getTomoAlignerSelector($validcycles, $alignerkey,'goodcycle');
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
		$refnum = ($_POST['refnum'] && $_POST['refnum'] >= 0) ? $_POST['refnum'] : $refinedata[0]['imgref'];	
		$minx = ($_POST['minx'] && $_POST['minx'] >= 0) ? $_POST['minx'] : 0;	
		$maxx = ($_POST['maxx'] && $_POST['maxx'] < count($refinedata)) ? $_POST['maxx'] : count($refinedata)-1;
		if ($minx or $maxx != count($refinedata)) {
			echo "<img border='0' src='tomoaligngraph.php?w=512&h=256&aId=$lastalignerId&box=1&ref=$refnum"
				."&minx=$minx&maxx=$maxx&expId=$expId'><br/>\n";
		} else {
			echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$lastalignerId&expId=$expId&box=1&ref=$refnum'><br/>\n";
		}
		echo docpop('protomoref','reference image expressed as sorted tilt number');
		echo " <input type='text' name='refnum' onchange=submit() value='$refnum' size='4'>";
		echo " <p>\n";
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
		// Hide secondary tilt series until dual tilt is processable
		if (false) {
			echo "</td><td Valign='TOP'>\n";
			echo $seriesselector_array2[0];
			echo docpop('tiltseriestwo', '2ndary Tilt Series');
		}
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
	echo "<br />\n";
	echo "<br />\n";
	echo $ddstackform->generateForm();
	echo "<br />\n";
	$outdir=buildOutdir($sessioninfo,$tiltseriesinfos[0]['number']);
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
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
		echo "<i>(Changing align method will change the runname)</i>";
		echo "<input type='hidden' name='lastrunname' value='$runname'>\n";
	} 
	//description
	echo"<P>
      <b>Alignment Description:</b><br>
      <textarea name='description' ROWS='2' COLS='40'>$description</textarea>
			<p>\n";
	echo docpop('tomoalignmethod', 'Method');
	echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='leginon' $leginoncheck>\n";
	echo docpop('tomoleginonalign', 'Leginon alignment');
	echo "<i>(default)</i>\n";
	if (!$lastalignerId) {
		echo "&nbsp;<input type='radio' onClick=submit() name='alignmethod' value='imod-shift' $imodcheck>\n";
		echo "Imod shift-only alignment\n";
		echo "<input type='hidden' name='lastalignmethod' value='$alignmethod'>\n";
	}
  echo "</td>
    </tr>
    <tr>
      <td Valign='TOP' class='tablebg'>";     

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
  <td>

  <tr>
    <td align='center'>
      <hr>
	";
	echo getSubmitForm("Align Tilt Series");
	echo "
        </td>
	</tr>
  </table>
	";
	if ($protomocheck || $protomo2check) {
		echo protomoRef();
	} else {
		echo imodRef();
	}
	echo "
  </form>\n";


	processing_footer();
	exit;
}

function runTomoAligner() {
	/* *******************
	PART 1: Get variables
	******************** */

	$projectId=getProjectId();
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$description=$_POST['description'];
	
	/** protomo 2 **/
	$maxIteration = $_POST['maxIteration'];
	$alignSample = $_POST['alignSample'];
	$sampleThickness = $_POST['sampleThickness'];
	$highestTiltAngle = $_POST['highestTiltAngle'];
	$windowX = $_POST['windowX'];
	$windowY = $_POST['windowY'];
	$lowDiameterX = $_POST['lowDiameterX'];
	$lowDiameterY = $_POST['lowDiameterY'];
	$highDiameterX = $_POST['highDiameterX'];
	$highDiameterY = $_POST['highDiameterY'];
	$mapSizeX = $_POST['mapSizeX'];
	$mapSizeY = $_POST['mapSizeY'];
	$mapSizeZ = $_POST['mapSizeZ'];
	/** end of protomo 2 **/
	
	$tiltseriesId=$_POST['tiltseriesId'];
	$tiltseriesId2=$_POST['tiltseriesId2'];
	$runname=$_POST['runname'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$alignmethod = $_POST['alignmethod'];
	$setting = $_POST['setting'];
	$cycle=$_POST['cycle'];
	if ($_GET['lastaId']) {
		$lastalignerId = $_GET['lastaId'];
		$goodcycle = is_numeric($_GET['goodcycle'])? $_GET['goodcycle']: max($cycle-2,0);
		$goodstart=$_POST['minx'];
		$goodend=$_POST['maxx'];
	}
	$sample=$_POST['sample'];
	$region=$_POST['region'];
	$maxregion=$_POST['maxregion'];
	$refnum=$_POST['refnum'];

	$markersize=$_POST['markersize'];
	$markernumber=$_POST['markernumber'];
	$reconbin=$_POST['reconbin'];
	$reconthickness=$_POST['reconthickness'];
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure the protomo sampling is valid
	if ($sample < 1 && $alignmethod=='protomo') createTomoAlignerForm("<b>ERROR:</b> Sampling must >= 1");
	if (!$lastalignerId) {
		//error check for first or only cycle of alignment
		//make sure a tilt series was provided
		if (!$tiltseriesId) createTomoAlignerForm("<b>ERROR:</b> Select the tilt series");
		//make sure a description was provided
		if (!$description) createTomoAlignerForm("<b>ERROR:</b> Enter a brief description of the tomogram");
		
		if($alignmethod == 'protomo2'){
			//make sure the number of alignment and geometry refinement iterations value is provided
			if (!$maxIteration) createTomoAlignerForm("<b>ERROR:</b> Enter the value of number of iterations.");
			//make sure the alignment sampling value is provided
			if (!$alignSample) createTomoAlignerForm("<b>ERROR:</b> Enter the value of alignment sampling");
			//make sure the sample thickness value is provided.
			if(!$sampleThickness) createTomoAlignerForm("<b>ERROR:</b> Enter the value of thickness at sampling.");
			//make sure the tilt angle value is provided.
			if(!$highestTiltAngle) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the tilt angle.");			
			//make sure the value of the x-asix's window size is provided
			if (!$windowX) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the x-asix's window size");
			//make sure the value of the y-asix's window size is provided
			if (!$windowY) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the y-asix's window size");
			//make sure the value of the lowpass diameter (x-axis) is provided
			if (!$lowDiameterX) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the lowpass diameter (x-axis)");
			//make sure the value of the lowpass diameter (y-axis) is provided
			if (!$lowDiameterY) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the lowpass diameter (y-axis)");
			//make sure the value of the highpass diameter (x-axis) is provided
			if (!$highDiameterX) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the highpass diameter (x-axis)");
			//make sure the value of the highpass diameter (y-axis) is provided
			if (!$highDiameterY) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the highpass diameter (y-axis)");
			//make sure the value of the map size (x-axis) is provided
			if (!$mapSizeX) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the map size (x-axis)");
			//make sure the value of the map size (y-axis) is provided
			if (!$mapSizeY) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the map size (y-axis)");
			//make sure the value of the map size (z-axis) is provided
			if (!$mapSizeZ) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the map size (z-axis)");
	
			
			if($setting == 'advance'){
				//put the advance parameters here
			}
		}
	} else {
		//make sure the region is not too large
		if ($maxregion < $region) 
			createTomoAlignerForm("<b>ERROR:</b> The alignment region can not be larger than ".$maxregion." % of the image");
	}

	/* *******************
	PART 3: Create program command
	******************** */
	$ddstackform = new DDStackSelectTable($expId);
	$command = "tomoaligner.py ";
	$command.="--session=$sessionname ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
	$command .= $ddstackform->buildCommand( $_POST );	
	if (!$lastalignerId) {
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
		$command.="--goodaligner=$lastalignerId ";
		$command.="--goodcycle=$goodcycle ";
		$command.="--goodstart=$goodstart ";
		$command.="--goodend=$goodend ";
	}
	$command.="--rundir=".$outdir.'/'.$runname." ";
	if ($alignmethod == 'protomo') {
		$command.="--cycle=$cycle ";
		$command.="--sample=$sample ";
		$command.="--region=$region ";
		if (!empty($refnum))
			$command.="--refimg=$refnum ";
	}
	if ($alignmethod == 'protomo2') {
		$command .="--sample=$alignSample ";
		$command .="--sample_thickness=$sampleThickness ";
		$command .="--highest_tilt_angle=$highestTiltAngle ";
		$command .="--windowsize_x=$windowX ";
		$command .="--windowsize_y=$windowY ";
		$command .="--lowpass_diameter_x=$lowDiameterX ";
		$command .="--lowpass_diameter_y=$lowDiameterY ";
		$command .="--highpass_diameter_x=$highDiameterX ";
		$command .="--highpass_diameter_y=$highDiameterY ";
		$command .="--map_size_x=$mapSizeX ";
		$command .="--map_size_y=$mapSizeY ";
		$command .="--map_size_z=$mapSizeZ ";
		$command .="--max_iterations=$maxIteration ";
		
	}

	$command.="--description=\"$description\" ";
	$command.="--alignmethod=$alignmethod ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= ($alignmethod == 'protomo') ? protomoRef(): imodRef();

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'tomoaligner', $nproc);

	// if error display them
	if ($errors)
		createTomoAlignerForm($errors);
	exit;
}
?>
