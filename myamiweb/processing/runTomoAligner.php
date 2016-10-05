<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

print "_POST:" . "<br>";
var_dump($_POST);
print "_GET:" . "<br>";
var_dump($_GET);
print "_SESSION:" . "<br>";
var_dump($_SESSION);

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runTomoAligner();
}

// Create the form page
else {
	createTomoAlignerForm();
}

function buildOutdir($sessioninfo,$tiltseriesnumber,$is_raptor) {
	$outdir=$sessioninfo;
	$outdir=getBaseAppionPath($sessioninfo);
	$outdir .="/tomo/tiltseries".$tiltseriesnumber;
	if (!$is_raptor)
		$outdir=$outdir.'/align';
	return $outdir;	
}

function createTomoAlignerForm($extra=false, $title='tomoaligner.py Launcher', $heading='Run Tilt Series Aligner') {
	// check if coming directly from a session
	//print "_POST:" . "<br>";
	//var_dump($_POST);
	//print "_GET:" . "<br>";
	//var_dump($_GET);
	//print "_SESSION:" . "<br>";
	//var_dump($_SESSION);
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
	$protomocheck = ($_POST['alignmethod'] == 'protomo') ? "CHECKED" : "";
	$raptorcheck = ($_POST['alignmethod'] == 'raptor') ? "CHECKED" : "";
	$protomo2check = ($_POST['alignmethod'] == 'protomo2') ? "CHECKED" : "";
	# For Jensen Lab
	#$raptorcheck = ($_POST['alignmethod'] == 'raptor' || !($_POST['alignmethod'])) ? "CHECKED" : "";
	#$protomo2check = ($_POST['alignmethod'] == 'protomo2') ? "CHECKED" : "";
	$imodcheck = ($_POST['alignmethod'] == 'imod-shift') ? "CHECKED" : "";

	$runtypes = array('leginon'=>'leginon','raptor'=>'raptor','imod-shift'=>'imodxc','protomo'=>'protomo', 'protomo2'=>'protomo');
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
	//raptor parameters
	$markersize = ($_POST['markersize']) ? $_POST['markersize'] : 10;
	$markernumber = ($_POST['markernumber']) ? $_POST['markernumber'] : 0;
	$reconbin = ($_POST['reconbin']) ? $_POST['reconbin'] : 2;
	$reconthickness = ($_POST['reconthickness']) ? $_POST['reconthickness'] : 500;

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
	$outdir=buildOutdir($sessioninfo,$tiltseriesinfos[0]['number'],$raptorcheck);
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
	echo "Leginon alignment<i>(default)</i>\n";
	echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='protomo' $protomocheck>\n";
	echo "Protomo refinement\n";
	if (!$lastalignerId) {
		echo "&nbsp;<input type='radio' onClick=submit() name='alignmethod' value='imod-shift' $imodcheck>\n";
		echo "Imod shift-only alignment\n";
		if (HIDE_FEATURE === false) {
			echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='raptor' $raptorcheck>\n";
			echo "Raptor<font size=-2><i></i></font>\n";
			echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='protomo2' $protomo2check>\n";
			echo "Protomo 2<font size=-2></font>\n";
		}
		echo "<input type='hidden' name='lastalignmethod' value='$alignmethod'>\n";
	}
  echo "</td>
    </tr>
    <tr>
      <td Valign='TOP' class='tablebg'>";     

	if ($protomo2check){
		if ($lastalignerId) {
			$lastalignparams = $refinedata[0];
			$defcycle = $lastalignparams['cycle'] + 1;
		} else {
			$defcycle = 1;
		}
		
		$basicCheck = (($protomo2check == "CHECKED" && $_POST['setting'] != 'advance') || !($_POST['alignmethod'])) ? "checked" : "";
		$advanceCheck = ($protomo2check == "CHECKED" && $_POST['setting'] == 'advance') ? "checked" : "";
		$cycle = ($_POST['cycle']) ? $_POST['cycle'] : $defcycle;
		$maxIteration = ($_POST['maxIteration']) ? $_POST['maxIteration'] : '1';
		$windowX = ($_POST['windowX']) ? $_POST['windowX'] : '512';
		$windowY = ($_POST['windowY']) ? $_POST['windowY'] : '512';
		$alignSample = ($_POST['alignSample']) ? $_POST['alignSample'] : '4';
		$sampleThickness = ($_POST['sampleThickness']) ? $_POST['sampleThickness'] : '40';
		$highestTiltAngle = ($_POST['highestTiltAngle']) ? $_POST['highestTiltAngle'] : '0.4848';
		$binning = (empty($_POST['binning']) && $advanceCheck=="checked") ? 'true' : $_POST['binning'];
		$preprocessing = (empty($_POST['preprocessing']) && $advanceCheck=="checked") ? 'true' : $_POST['preprocessing'];
		$logging = (empty($_POST['logging']) && $advanceCheck=="checked") ? 'false' : $_POST['logging'];
		$preprocessBorder = ($_POST['preprocessBorder']) ? $_POST['preprocessBorder'] : '100';
		$preprocessClipLow = ($_POST['preprocessClipLow']) ? $_POST['preprocessClipLow'] : '3.5';
		$preprocessClipHigh = ($_POST['preprocessClipHigh']) ? $_POST['preprocessClipHigh'] : '3.5';
		$maskGradient = (empty($_POST['maskGradient']) && $advanceCheck=="checked") ? 'true' : $_POST['maskGradient'];
		$maskIter = (empty($_POST['maskIter']) && $advanceCheck=="checked") ? 'true' : $_POST['maskIter'];
		$maskFilter = (empty($_POST['maskFilter']) && $advanceCheck=="checked") ? 'median' : $_POST['maskFilter'];		
		$maskKernelX = ($_POST['maskKernelX']) ? $_POST['maskKernelX'] : '5';
		$maskKernelY = ($_POST['maskKernelY']) ? $_POST['maskKernelY'] : '5';
		$maskClipLow = ($_POST['maskClipLow']) ? $_POST['maskClipLow'] : '3.0';
		$maksClipHigh = ($_POST['maksClipHigh']) ? $_POST['maksClipHigh'] : '3.0';
		$windowMaskX = ($_POST['windowMaskX']) ? $_POST['windowMaskX'] : '10';
		$windowMaskY = ($_POST['windowMaskY']) ? $_POST['windowMaskY'] : '10';
		$lowDiameterX = ($_POST['lowDiameterX']) ? $_POST['lowDiameterX'] : '';
		$lowDiameterY = ($_POST['lowDiameterY']) ? $_POST['lowDiameterY'] : '';
		$lowApodizationX = ($_POST['lowApodizationX']) ? $_POST['lowApodizationX'] : '0.01';
		$lowApodizationY = ($_POST['lowApodizationY']) ? $_POST['lowApodizationY'] : '0.01';
		$highDiameterX = ($_POST['highDiameterX']) ? $_POST['highDiameterX'] : '';
		$highDiameterY = ($_POST['highDiameterY']) ? $_POST['highDiameterY'] : '';
		$highApodizationX = ($_POST['highApodizationX']) ? $_POST['highApodizationX'] : '0.02';
		$highApodizationY = ($_POST['highApodizationY']) ? $_POST['highApodizationY'] : '0.02';	
		$mapSizeX = ($_POST['mapSizeX']) ? $_POST['mapSizeX'] : '256';
		$mapSizeY = ($_POST['mapSizeY']) ? $_POST['mapSizeY'] : '256';
		$mapSizeZ = ($_POST['mapSizeZ']) ? $_POST['mapSizeZ'] : '128';
		$mapLowpassDiameterX = ($_POST['mapLowpassDiameterX']) ? $_POST['mapLowpassDiameterX'] : '0.50';
		$mapLowpassDiameterY = ($_POST['mapLowpassDiameterY']) ? $_POST['mapLowpassDiameterY'] : '0.50';
		$mapLowpassApodizationX = ($_POST['mapLowpassApodizationX']) ? $_POST['mapLowpassApodizationX'] : '0.02';
		$mapLowpassApodizationY = ($_POST['mapLowpassApodizationY']) ? $_POST['mapLowpassApodizationY'] : '0.02';
		$alignEstimate = (empty($_POST['alignEstimate']) && $advanceCheck=="checked") ? 'true' : $_POST['alignEstimate'];
		$alignMaskX = ($_POST['alignMaskX']) ? $_POST['alignMaskX'] : '10';
		$alignMaskY = ($_POST['alignMaskY']) ? $_POST['alignMaskY'] : '10';
		$maxCorrection = ($_POST['maxCorrection']) ? $_POST['maxCorrection'] : '0.04';
		$correlationX = ($_POST['correlationX']) ? $_POST['correlationX'] : '128';
		$correlationY = ($_POST['correlationY']) ? $_POST['correlationY'] : '128';
		$peakSearchRadiusX = ($_POST['peakSearchRadiusX']) ? $_POST['peakSearchRadiusX'] : '49';
		$peakSearchRadiusY = ($_POST['peakSearchRadiusY']) ? $_POST['peakSearchRadiusY'] : '49';
		$corelationMode = (empty($_POST['corelationMode']) && $advanceCheck=="checked") ? 'mcf' : $_POST['corelationMode'];
		
?>	<table>
		<tr><td>
			<b><center>Tilt Series Alignment Params:</center></b>
		</td></tr>
		<tr><td>
			<b>Setting: </b>
			Basic <input type='radio' onClick=submit() name='setting' value='basic' <?php echo $basicCheck; ?>>
			Advance	<input type='radio' onClick=submit() name='setting' value='advance' <?php echo $advanceCheck; ?>>
		</td></tr>
		<tr><td>
			<b>Alignment Iteration: </b><?php echo $cycle; ?>
			<input type='hidden' name='cycle' value='<?php echo $cycle; ?>'>
			<hr />
		</td></tr>
		<tr><td>
			<input type='text' name='maxIteration' size='3' value='<?php echo $maxIteration; ?>'>
			Number of <b>refinement iterations</b>. (>=1)
		</td></tr>
		<tr><td>
			<input type='text' name='windowX' size='4' value='<?php echo $windowX; ?>'> x-axis, 
			<input type='text' name='windowY' size='4' value='<?php echo $windowY; ?>'> y-axis: 
			<b>Window Size</b>. (Number of Pixel)
		</td></tr>
		<tr><td>
			<input type='text' name='alignSample' size='4' value='<?php echo $alignSample; ?>'>
			<b>Alignment Sampling</b>. (S)
		</td></tr>
		<tr><td>
			<b>Back Projection Body Size</b> ( T / F )
			<table style="padding-left: 20px;">
				<tr><td>
					<input type='text' name='sampleThickness' size='3' value='<?php echo $sampleThickness; ?>'>
					<b>Thickness</b> at sampling. (T)
				</td></tr>
				<tr><td>
					<input type='text' name='highestTiltAngle' size='4' value='<?php echo $highestTiltAngle; ?>'>
					<b>cos( highest tilt angle )</b>. (F)
				</td></tr>
			</table>
		</td></tr>

		<?php if($advanceCheck){ ?>
		<tr><td>
			<b>Binning: </b> 
			<input type='radio' name='binning' value='true' <?php if($binning=='true') echo 'checked'; ?>> True
			<input type='radio' name='binning' value='false' <?php if($binning=='false') echo 'checked'; ?>> False			
		</td></tr>
		<tr><td>
			<b>Preprocessing: </b> 
			<input type='radio' name='preprocessing' value='true' <?php if($preprocessing=='true') echo 'checked'; ?>> True
			<input type='radio' name='preprocessing' value='false' <?php if($preprocessing=='false') echo 'checked'; ?>> False			
		</td></tr>
		<tr><td>
			<b>Preprocess: </b>
			<table style="padding-left: 20px;">
				<tr><td>
					<b>Logging: </b>
					<input type='radio' name='logging' value='true' <?php if($logging=='true') echo 'checked'; ?>> True
					<input type='radio' name='logging' value='false' <?php if($logging=='false') echo 'checked'; ?>> False
				</td></tr>
				<tr><td>
					<input type='text' name='preprocessBorder' size='4' value='<?php echo $preprocessBorder; ?>'>
					<b>Border</b>.
				</td></tr>
				<tr><td>
					<input type='text' name='preprocessClipLow' size='3' value='<?php echo $preprocessClipLow; ?>'> low, 
					<input type='text' name='preprocessClipHigh' size='3' value='<?php echo $preprocessClipHigh; ?>'> high: 
					<b>Clip</b>. (Specified as a multiple of the standard deviation)
				</td></tr>
				<tr><td>
					<b>Mask:</b>
					<table style="padding-left: 20px;">
						<tr><td>
							<b>Gradient: </b>
							<input type='radio' name='maskGradient' value='true' <?php if($maskGradient=='true') echo 'checked'; ?>> True
							<input type='radio' name='maskGradient' value='false' <?php if($maskGradient=='false') echo 'checked'; ?>> False
						</td></tr>
						<tr><td>
							<b>Iter: </b>
							<input type='radio' name='maskIter' value='true' <?php if($maskIter=='true') echo 'checked'; ?>> True
							<input type='radio' name='maskIter' value='false' <?php if($maskIter=='false') echo 'checked'; ?>> False
						</td></tr>
						<tr><td>
							<b>Filter: </b>
							<input type='radio' name='maskFilter' value='low' <?php if($maskFilter=='low') echo 'checked'; ?>> Low
							<input type='radio' name='maskFilter' value='median' <?php if($maskFilter=='median') echo 'checked'; ?>> Median
							<input type='radio' name='maskFilter' value='high' <?php if($maskFilter=='high') echo 'checked'; ?>> High
						</td></tr>
						<tr><td>
							<input type='text' name='maskKernelX' size='3' value='<?php echo $maskKernelX; ?>'> x-axis, 
							<input type='text' name='maskKernelY' size='3' value='<?php echo $maskKernelY; ?>'> y-axis: 
							<b>Kernel</b>. (Size of the window over which the median is computed)
						</td></tr>
						<tr><td>
							<input type='text' name='maskClipLow' size='3' value='<?php echo $maskClipLow; ?>'> low, 
							<input type='text' name='maksClipHigh' size='3' value='<?php echo $maksClipHigh; ?>'> high: 
							<b>Clip</b>. (Specified as a multiple of the standard deviation)
						</td></tr>
					</table>
				</td></tr>
			</table>
		</td></tr>
		<?php } ?>
		<tr><td>
			<b>Window: </b>
			<table style="padding-left: 20px;">
				<?php if($advanceCheck){ ?>
				<tr><td>
					<input type='text' name='windowMaskX' size='3' value='<?php echo $windowMaskX; ?>'> x-axis, 
					<input type='text' name='windowMaskY' size='3' value='<?php echo $windowMaskY; ?>'> y-axis: 
					<b>Mask Apodization</b>. ( 1 ~ 20 )
				</td></tr>
				<?php } ?>
				<tr><td>
					<input type='text' name='lowDiameterX' size='3' value='<?php echo $lowDiameterX; ?>'> x-axis, 
					<input type='text' name='lowDiameterY' size='3' value='<?php echo $lowDiameterY; ?>'> y-axis: 
					<b>Lowpass Diameter</b>.
				</td></tr>
				<?php if($advanceCheck){ ?>
				<tr><td>
					<input type='text' name='lowApodizationX' size='3' value='<?php echo $lowApodizationX; ?>'> x-axis, 
					<input type='text' name='lowApodizationY' size='3' value='<?php echo $lowApodizationY; ?>'> y-axis: 
					<b>Lowpass Apodization</b>. ( 1 / pixel )
				</td></tr>
				<?php } ?>
				<tr><td>
					<input type='text' name='highDiameterX' size='3' value='<?php echo $highDiameterX; ?>'> x-axis, 
					<input type='text' name='highDiameterY' size='3' value='<?php echo $highDiameterY; ?>'> y-axis: 
					<b>Highpass Diameter</b>.
				</td></tr>
				<?php if($advanceCheck){ ?>
				<tr><td>
					<input type='text' name='highApodizationX' size='3' value='<?php echo $highApodizationX; ?>'> x-axis, 
					<input type='text' name='highApodizationY' size='3' value='<?php echo $highApodizationY; ?>'> y-axis: 
					<b>Highpass Apodization</b>. ( 1 / pixel )
				</td></tr>
				<?php } ?>
			</table>
		</td></tr>
		<tr><td>
			<b>Map: </b>
			<table style="padding-left: 20px;">
				<tr><td>
					<input type='text' name='mapSizeX' size='3' value='<?php echo $mapSizeX; ?>'> x-axis, 
					<input type='text' name='mapSizeY' size='3' value='<?php echo $mapSizeY; ?>'> y-axis,  
					<input type='text' name='mapSizeZ' size='3' value='<?php echo $mapSizeZ; ?>'> z-axis:
					<b>Size</b>. ( Between 1 to image size )
				</td></tr>
				<?php if($advanceCheck){ ?>
				<tr><td>
					<input type='text' name='mapLowpassDiameterX' size='3' value='<?php echo $mapLowpassDiameterX; ?>'> x-axis, 
					<input type='text' name='mapLowpassDiameterY' size='3' value='<?php echo $mapLowpassDiameterY; ?>'> y-axis:
					<b>Lowpass Diameter</b>. ( Between 0 to 1 )
				</td></tr>
				<tr><td>
					<input type='text' name='mapLowpassApodizationX' size='3' value='<?php echo $mapLowpassApodizationX; ?>'> x-axis, 
					<input type='text' name='mapLowpassApodizationY' size='3' value='<?php echo $mapLowpassApodizationY; ?>'> y-axis:
					<b>Lowpass Apodization</b>. ( Between 0 to 1 )
				</td></tr>
				<?php } ?>
			</table>
		</td></tr>
		<?php if($advanceCheck){ ?>
		<tr><td>
			<b>Align: </b>
			<table style="padding-left: 20px;">
				<tr><td>
					<b>Estimate: </b>
					<input type='radio' name='alignEstimate' value='true' <?php if($alignEstimate=='true') echo 'checked'; ?>> True
					<input type='radio' name='alignEstimate' value='false' <?php if($alignEstimate=='false') echo 'checked'; ?>> False
				</td></tr>
				<tr><td>
					<input type='text' name='maxCorrection' size='4' value='<?php echo $maxCorrection; ?>'>
					<b>Max-Correction</b>. ( Between 0 to 0.1 )
				</td></tr>
				<tr><td>
					<input type='text' name='alignMaskX' size='3' value='<?php echo $alignMaskX; ?>'> x-axis, 
					<input type='text' name='alignMaskY' size='3' value='<?php echo $alignMaskY; ?>'> y-axis: 
					<b>Mask Apodization</b>. ( 1 ~ 20 )
				</td></tr>
				<tr><td>
					<b>Correlation Mode: </b>
					<select name='corelationMode'>
						<option value='mcf' <?php if($corelationMode=='mcf') echo 'selected="yes"'; ?>>mcf</option>
						<option value='xcf' <?php if($corelationMode=='xcf') echo 'selected="yes"'; ?>>xcf</option>
						<option value='pcf' <?php if($corelationMode=='pcf') echo 'selected="yes"'; ?>>pcf</option>
						<option value='dbl' <?php if($corelationMode=='dbl') echo 'selected="yes"'; ?>>dbl</option>
					</select>
				</td></tr>
				<tr><td>
					<input type='text' name='correlationX' size='3' value='<?php echo $correlationX; ?>'> x-axis, 
					<input type='text' name='correlationY' size='3' value='<?php echo $correlationY; ?>'> y-axis: 
					<b>Correlation Size</b> ( Between 1 to window size )
				</td></tr>
				<tr><td>
					<input type='text' name='peakSearchRadiusX' size='3' value='<?php echo $peakSearchRadiusX; ?>'> x-axis, 
					<input type='text' name='peakSearchRadiusY' size='3' value='<?php echo $peakSearchRadiusY; ?>'> y-axis: 
					<b>Peak-search Radius</b> ( Between 1 to half of the window size )
				</td></tr>
			</table>
		</td></tr>
		<?php } ?>
	</table>
<?php 		
	} elseif ($protomocheck) {
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
	} elseif ($raptorcheck) {
		echo "
			<b> <center>Raptor Alignment Reconstruction Params: </center></b>
      <P>";
		echo " <input type='text' name='markersize' size='5' value='$markersize'>\n";
		echo docpop('markersize','Marker Size (nm)');
		echo "<P>";
		echo " <input type='text' name='markernumber' size='5' value='$markernumber'>\n";
		echo docpop('tomomarkersize','Number of Markers to be used');
		echo "<font>(0 means automatically determined)</font>";
		echo "<P>";
		echo " <input type='text' name='reconbin' size='5' value='$reconbin'>\n";
		echo docpop('extrabin','Reconstruction Binning');
		echo "<P>";
		echo " <input type='text' name='reconthickness' size='5' value='$reconthickness'>\n";
		echo docpop('tomosamplethickness','Tomogram Thickness (pixels in tilt images)');
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
		if($alignmethod == 'raptor'){
			if (!is_numeric($markersize)) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the marker size (nm)");
			if (!is_numeric($markernumber)) createTomoAlignerForm("<b>ERROR:</b> Enter the estimated number of the marker");
			if (!is_numeric($reconbin)) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the bin factor  as integer for reconstruction ");
			if (!is_numeric($reconthickness)) createTomoAlignerForm("<b>ERROR:</b> Enter the value of the specimen thickness (nm)");
		}
	} else {
		//make sure the region is not too large
		if ($maxregion < $region) 
			createTomoAlignerForm("<b>ERROR:</b> The alignment region can not be larger than ".$maxregion." % of the image");
	}

	/* *******************
	PART 3: Create program command
	******************** */
	if ($alignmethod == 'raptor') {
		$command = "tomoraptor.py ";
	} else {
		$command = "tomoaligner.py ";
	}
	$command.="--session=$sessionname ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
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
	if ($alignmethod != 'raptor') {
		$command.="--alignmethod=$alignmethod ";
	}
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

	if ($alignmethod == 'raptor') {
		$command .="--markersize=".(int)$markersize." ";
		$command .="--markernumber=".(int)$markernumber." ";
		$command .="--reconbin=".(int)$reconbin." ";
		$command .="--thickness=".(int)$reconthickness." ";
	}
	$command.="--description=\"$description\" ";
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
