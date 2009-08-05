<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *  Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

function getNumClassesFromFile ($imagicfile) {
	$hedfile = $imagicfile;
	if (substr($imagicfile, -4) == ".img")
		$hedfile = substr($imagicfile, 0, -4).".hed";
	if (!file_exists($hedfile)) {
		echo "MISSING HED FILE: $hedfile<br/>";
		return 0;
	}
	$size = filesize($hedfile);
	//echo "SIZE $size<br/>";
	$numclass = ceil($size/1024.0/2.0);
	return $numclass;
}

$leginondata = new leginondata();

// check if coming directly from a session
$expId=$_GET['expId'];
if ($expId){
	$sessionId=$expId;
	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
	$sessionId=$_POST['sessionId'];
	$formAction=$_SERVER['PHP_SELF'];  
}

$sessioninfo = $leginondata->getSessionInfo($expId);

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.=eulerImgJava();

$data = processing_header("Appion Data Processing","Appion Data Processing", $javascript);
// --- main window starts here --- //

$particle=new particleData();
// show exemplar reconstrucion, if set
$reconRuns = $particle->getExemplarReconsFromSession($expId);

if (!$reconRuns) {
	processing_footer();
	exit();
}
# get list of png files in directory
$pngimages = getPngList($reconRuns[0]['path']);

foreach ($reconRuns as $recon) {
	$reconid = $recon['refdataid'];
	$reconrunid = $recon['refrunid'];
	$stackid = $recon['REF|ApStackData|stack'];
	$presetinfo = $particle->getPresetFromStackId($stackid);
	$j = "Exemplar Iteration ID: $reconid";
	echo apdivtitle($j);
	$stackparams = $particle->getStackParams($stackid);
	$avgmedjump = $particle->getAverageMedianJump($reconrunid);
	if ($avgmedjump['count'] > 0) {
		$avgmedjumpstr .= "<A HREF='eulergraph.php?expId=$expId&hg=1&recon=$reconrunid'>";
		$avgmedjumpstr .= sprintf("%2.2f &plusmn; %2.1f </A>", $avgmedjump['average'], $avgmedjump['stdev']);
	} else $avgmedjumpstr = NULL;

	# get number of images for preset
	$presetsummary = $leginondata->getSummary($sessionId, $presetinfo['name']);
	$totimgs = $presetsummary[0]['nb'];

	# get info for nominal defocus range
	$cstats=$leginondata->getDefocus($sessionId, $presetinfo['name'], true);
	$cstats['name']=$presetinfo['name'];
	$minNomDF = sprintf("%.1f", $cstats['min']*-1e6);
	$maxNomDF = sprintf("%.1f", $cstats['max']*-1e6);
	$dfstats['nominal'][]=$cstats;

	# get ACE results
	$hasCTF = $particle->hasCtfData($sessionId);
	if ($hasCTF) {
		echo "<h4>CTF info</h4>\n";
		echo "<a href='processing/ctfreport.php?expId=$sessionId'>report &raquo;</a>\n";
		$display_keys = array ( 'preset', 'nb', 'min', 'max', 'avg', 'stddev');
		$fields = array('defocus1', 'confidence', 'confidence_d','difference');
		$bestctf = $particle->getBestStats($fields, $sessionId);
		$dfstats = array_merge($dfstats,$bestctf);
		$display_keys = array ( 'name', 'nb', 'min', 'max', 'avg', 'stddev');
		echo displayCTFstats($dfstats, $display_keys);
	}


	# get particle runs contributing to the stack
	$selectionRuns = $particle->getParticleRunsFromStack($stackid);
	echo "<h4>Particle Selection info</h4>\n";
	foreach ($selectionRuns as $srun){
		$numinspected=$particle->getNumAssessedImages($sessionId);
		if ($numinspected) 
			echo"Inpected images: $numinspected, ";
		if ($numinspected>0) 
			echo'<a href="showinspectdata.php?Id='.$sessionId.'&vd=1">[inspected data]</a>'."\n";
		$display_keys = array ( 'totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev');
		echo $particle->displayParticleStats($srun, $display_keys, False, False, False);
		$pickertype = $particle->getSelectionParams($srun[0]['DEF_id'],True);
		$particlestats = $particle->getStats($srun[0]['DEF_id']);
	}	

	// stack information
	// get pixel size
	$apix=($particle->getStackPixelSizeFromStackId($stackid))*1e10;
	$boxsz=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];

	// stack info
	$stackparticles = $particle->getNumStackParticles($stackid);
	echo ministacksummarytable($stackid);
	// initial model info
	echo modelsummarytable($recon['REF|ApInitialModelData|initialModel']);

	// reconstruction info
	$syminfo = $particle->getSymInfo($recon['REF|ApSymmetryData|symmetry']);

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$res = $particle->getResolutionInfo($recon['REF|ApResolutionData|resolution']);
	$RMeasure = $particle->getRMeasureInfo($recon['REF|ApRMeasureData|rMeasure']);
	$fscid = ($res) ? $reconid : False;
	$fscfile = ($res) ? $recon['path'].'/'.$res['fscfile'] : "None" ;
	$halfres = ($res) ? sprintf("%.2f",$res['half']) : "None" ;
	$rmeasureres = ($RMeasure) ? sprintf("%.2f",$RMeasure['rMeasure']) : "None" ;
	$badprtls = array();
	$goodprtls = array();
	$clsavgs = array();
	$refinetypes = array('EMAN','SpiCoran','MsgP');
	foreach ($refinetypes as $type) {
		switch ($type) {
			case 'EMAN':
				$clsavgfield = 'emanClassAvg';
				break;
			case 'SpiCoran':
				$clsavgfield = 'SpiCoranGoodClassAvg';
			  break; 	 
			case 'MsgP':
				$clsavgfield = 'MsgPGoodClassAvg';
			  break;
		}
		if ($recon[$clsavgfield]) {
			$clsavgs[$type] = $recon[$clsavgfield]; 
			$badprtls[$type]=$particle->getSubsetParticlesInStack($reconid, 'bad', $type, True);
			$goodprtls[$type]=$particle->getSubsetParticlesInStack($reconid, 'good', $type, True);
		}
	}
	# old data has no class average distinction, only eman bad particles
	if ((count($badprtls)==0) || ($recon['package']=='EMAN/MsgP' && (!array_key_exists('EMAN',$badprtls)))) 
		$badprtls['EMAN']=$particle->getSubsetParticlesInStack($reconid, 'bad', 'EMAN', True);
		$goodprtls['EMAN']=$particle->getSubsetParticlesInStack($reconid, 'good', 'EMAN', True);
	# old data has no class average distinction, force association 
	if ((count($clsavgs)==0 && ($recon['package'] == 'EMAN')) || ($recon['package']=='EMAN/MsgP' && (!array_key_exists('EMAN',$clsavgs)))) { 
		$clsavgs['EMAN']= $recon['classAverage'];
	} elseif (count($clsavgs)==0 && $recon['package']=='EMAN/SpiCoran') {
		$classnamearray = explode('.',$recon['classAverage']);
		$newnamearray = array_slice($classnamearray,0,count($classnamearray)-1);
		array_push($newnamearray,'old',$classnamearray[count($classnamearray)-1]);
		$clsavgs['EMAN'] = implode('.',$newnamearray);
		$clsavgs['SpiCoran']= $recon['classAverage'];
	}
	$html .= "<tr>\n";

	// gather resolution/fsc info
	$reshtml="<table border='0' cellpadding='3' cellspacing='0'><tr><td>\n";
	if ($halfres!='None' && $fscid)
		$reshtml .= "<a href='fscplot.php?expId=$expId&fscid=$fscid&width=800&height=600&apix=$apix&box=$boxsz' target='snapshot'><img src='fscplot.php?expId=$expId&fscid=$fscid&width=100&height=80&nomargin=TRUE'></a></td><td>";
	elseif ($halfres!='None' && $fscfile) 
		$reshtml .= "<a href='fscplot.php?expId=$expId&fscfile=$fscfile&width=800&height=600&apix=$apix&box=$boxsz' target='snapshot'><img src='fscplot.php?expId=$expId&fscfile=$fscfile&width=100&height=80&nomargin=TRUE'></a></td><td>";
	$reshtml .= "<i>FSC 0.5:</i> $halfres\n";
  	if ($rmeasureres!='None')
		$reshtml .= "<br /><i>Rmeas:</i> $rmeasureres\n";
	$reshtml.="</td></tr></table>\n";

	// gather class information

	$classhtml = "";
	foreach ($refinetypes as $type) {
		if (array_key_exists($type,$clsavgs)) {
			$clsavgfile = $recon['path'].'/'.$clsavgs[$type];
			$classhtml .= "<br /><a target='stackview' href='viewstack.php?file=$clsavgfile'>".$clsavgs[$type]."</a>";
		}
	}
	$numclasses = getNumClassesFromFile($clsavgfile);
	$classhtml .= "$numclasses classes\n";
	//Euler plots
	$eulerhtml = "<table border='0'><tr>\n";
	foreach ($pngimages['eulerfiles'] as $eulername) {
		if (eregi($reconrunid."_".$recon['iteration']."\.png$", $eulername)) {
			$eulerfile = $recon['path'].'/'.$eulername;
			$opname = ereg_replace("euler","",$eulername);
			$opname = ereg_replace("-".$reconrunid."_".$recon['iteration']."\.png$","",$opname);
			if (file_exists($eulerfile)) {
			  $eulerhtml .= "<td align='center'>\n";
			  $eulerhtml .= "<a id='eulerlink".$iteration['iteration']."' href='loadimg.php?filename=".$eulerfile."' target='snapshot'>"
			    ."<img name='eulerimg".$iteration['iteration']."' src='loadimg.php?scale=.125&filename=".$eulerfile."'>\n";
			  $eulerhtml .= "<br />$opname</a></td>\n";
			}
		}
	}
	$eulerhtml .= "</tr></table>\n";

	// particle stacks classification/viewing 
	$phtml="<table border='0' cellpadding='3' cellspacing='2'><tr><td>\n";
	foreach ($refinetypes as $type) {
		if (array_key_exists($type,$badprtls)) {
			$prtlsused=$stackparticles-$badprtls[$type];
			$phtml .= "$type<br />";
			if ($prtlsused != $goodprtls[$type]) $phtml .= "Not all prtls accounted for!";
			$phtml .= "<a target='stackview' href='viewstack.php?expId=$expId&refinement=$reconid&substack=good&refinetype=$type'>[$goodprtls[$type]-good]</a><br />\n"
			."<a target='stackview' HREF='viewstack.php?expId=$expId&refinement=$reconid&substack=bad&refinetype=$type'>[$badprtls[$type]-bad]</a></td><td>\n";
		}
	}	
	$phtml .= "</tr></table>\n";
	
	$modhtml = "<table class='tableborder' border='1'>\n";
	$modhtml .= "<tr><td>volume: ".$recon['volumeDensity']."</td></tr><tr><td>\n";
	foreach ($pngimages['pngfiles'] as $snapshot) {
		if (eregi($recon['volumeDensity'],$snapshot)) {
			$snapfile = $recon['path'].'/'.$snapshot;
			$modhtml .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><img src='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
		}
	}
	$modhtml .= "</td>\n";
	$modhtml .= "</tr>\n";
	$modhtml .= "</table>\n";

	$title = "recon info\n";
	$reconinfo = array(
	'id'=>"<A HREF='reconsummary.php?expId=$expId'>$reconrunid</A>",
	'iteration'=>"<a class='aptitle' href='iterationreport.php?expId=$expId&rId=".$reconrunid."&itr=".$recon['iteration']."')\">$recon[iteration]</a>",
	'ang incr'=> $recon['ang']."&deg;",
	'name'=>$recon['name'],
	'description'=>$recon['description'],
	'path'=>$recon['path'],
	'refine package'=>$recon['package'],
	'symmetry'=>$syminfo['symmetry'].", ".$syminfo['description'],
	'median euler jump'=>$avgmedjumpstr,
	'resolution'=>$reshtml,
	'classes'=>$classhtml,
	'eulers'=>$eulerhtml,
	'particles'=>$phtml,
);
	$particle->displayParameters($title,$reconinfo,array(),$expId);
	echo $modhtml;

	// get camera & scope info
	$camera = $leginondata->getInstrumentInfo($sessioninfo['CameraId']);
	if (eregi("tecnai", $camera[0]['hostname'])) $scope = "Tecnai F20 Twin";
	else $scope = "Tecnai G2 Spirit Twin";
	$cam = ($camera[0]['name'] == 'Tietz SCX') ? 'Tietz F415' : $camera[0]['name'];
	$camsize = ($camera['0']['name'] == 'Tietz PXL') ? "2K x2K" : "4K x 4K";

	$mag = commafy($presetinfo['magnification']);
	$pix = $presetinfo['ccdpixelsize']*1e9;
	$campix = "15";
	$dose = round($presetinfo['dose']/1e20);
	$kvolt = $presetinfo['hightension']/1e3;

	$m = "<h4>Data Collection</h4>\n";
	$m .= "<table class='tableborder' border='1' width='600'><tr><td>\n";
	$m .= "Data were acquired using a $scope transmission electron microscope operating at $kvolt kV, \n";
	$m .= "using a dose of ~".$dose." e-/&Aring;&sup2; and a nominal underfocus ranging from $maxNomDF to $minNomDF &micro;m.\n";
	//	$m .= "A Gatan side-entry cryostage/room temp stage was used for data collection.\n";
	$m .= "$totimgs images were automatically collected at a nominal magnification of $mag x at a pixel size of $pix nm at the specimen level.\n";
	$m .= "All images were recorded with a $cam $camsize pixel CCD camera ($campix &micro;m pixel)\n";
	$m .= "utilizing the Leginon data collection software (Suloway 2005).\n";
	$m .= "Experimental data were processed by the Appion software package, which interfaces with the Leginon database infrastructure.\n";
	// CTF
	if ($hasCTF)
	  $m .= "The contrast transfer function (CTF) for each micrograph was estimated using the Automated CTF Estimation (ACE) package. \n";
	// Particle picking
	$m .= commafy($particlestats['totparticles'])." particles were ";
	if ($pickertype=='DOG Picker')
		$m .= "automatically selected from the micrographs using an algorithm based on a difference of gaussians (Yoshioka 2008) \n";
	elseif ($pickertype=='Template Correlator')
		$m .= "automatically selected from the micrographs using a template-based particle picker (Roseman, 2003) \n";
	else $m .= "manually selected from the micrographs \n";
	$m .= "and extracted at a box size of ".$stackparams['boxSize']." pixels. \n";
	if ($hasCTF) {
		$acecutoff=($stackparams['aceCutoff']) ? $stackparams['aceCutoff']*100 : '' ;
		if ($acecutoff)
			$m .= "Only particles whose CTF estimation had an ACE confidence of ".$acecutoff."% or better were extracted. \n";
		if ($stackparams['phaseFlipped']==1)
			$m .= "Phase correction of the single particles was carried out by ".$stackparams['fliptype']." during creation of the particle stack. \n";
	}
	if ($stackparams['bin']) $m .= "Stacked particles were binned by a factor of ".$stackparams['bin']." for the final reconstruction. \n";
	$m .= "The final stack contained ".commafy($stackparticles)." particles. \n";
	if ($clsavgs['SpiCoran']) {
	  $m .= "The 3D reconstruction was carried out using a combination of both the SPIDER and EMAN reconstruction packages (Frank 1996, Ludtke 1999). \n";
	  $m .= "Creation of projections of the 3D model and subsequent classification of the particles was performed by EMAN, \n";
	  $m .= "after which a SPIDER script was employed to perform a reference-free hierarchical clustering analysis of the particles in each class\n";
	  $m .= "The resulting SPIDER class that exhibited the highest cross-correlation value to the original model projection of the given class was\n";
	  $m .= "used in the creation of the 3D density for the following iteration by using EMAN.\n";
	  // calculate % of particles used
	  $tossed = round((($stackparticles - $badprtls['SpiCoran'])/$stackparticles)*100);
	  $m .= "With this methodology, $tossed % of the initial stacked particles were used in the final reconstruction. \n";
	}
	else $m .= "The 3D reconstruction was carried out using the EMAN reconstruction package (Ludtke 1999). \n";
	$m .= "Resolution was assessed by calculating the Fourier Shell Correlation (FSC) at a cutoff of 0.5, \n";
	$m .= "which provided a value of $halfres &Aring; resolution.\n";
	$m .= "Calculation of the resolution by rmeasure (Sousa and Gridgorieff 2007) at a 0.5 cutoff yielded a resolution of $rmeasureres &Aring;. \n";
	$m .= "</td></tr></table>\n";
	echo $m;
}
processing_footer();
?>
