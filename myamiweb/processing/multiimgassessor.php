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
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";

$particle=new particledata();

// check if coming directly from a session
$expId=$_GET['expId'];
$pickId=$_GET['pickId'];
$maskRunId=$_GET['maskId']; // The DEF_id for the mask maker run in ApMaskMakerRunData

$imgtypes = array('jpg','png','mrc','dwn.mrc');

if ($expId) {
	$sessionId=$expId;
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
} else {
	$sessionId=$_POST['sessionId'];
	$formAction=$_SERVER['PHP_SELF'];	
}
if ($pickId) {
	$_SERVER['PHP_SELF']."&pickId=$pickId";
	$pickdata = $particle->getSelectionRunData($pickId);
	$_POST['imgdir'] = $pickdata['path'];
	$_POST['imgrun'] = 0;
}
$displayMasks = False;
if ($maskRunId && !$_POST['imgrun']) {
	$displayMasks = True;
	$formAction = $formAction."&maskId=$maskRunId";
	$maskdata = $particle->getMaskMakerParams($maskRunId);
	$_POST['imgdir'] = $maskdata[0]['path']."/masks/";
	$_POST['imgrun'] = 0;
	// Try to find the type of images in the imgdir. 
	try {
		$type = findImageTypeInDir($_POST['imgdir'], $imgtypes );
		$_POST['imgtype'] = $type;
	} catch (Exception $e) {
    	$_POST['imgtype'] = "jpg";
	}
	
}
$projectId=getProjectId();

/////////// temporary fix for new database //////////////


$hasassrun=($particle->getLastAssessmentRun($expId)) ? true : false;
if ($hasassrun){
	$assessmentrid=$particle->getLastAssessmentRun($sessionId);
} else {
	$assrundata['name']='run1';
	$assrundata['REF|leginondata|SessionData|session']=$expId;
	$particle->mysql->SQLInsert('ApAssessmentRunData',$assrundata);
	$assessmentrid=$particle->getLastAssessmentRun($sessionId);
}


////////////////////////////////////////////////////////

$javascript="<script src='../js/viewer.js'></script>\n";
processing_header("Leginon Image Assessor","Image Assessor",$javascript);
echo"<form name='viewerform' method='POST' ACTION='$formAction'>\n";

$sessiondata=getSessionList($projectId,$expId);
$sessioninfo=$sessiondata['info'];
$presets=$sessiondata['presets'];

// add preset choice of all presets
if ($presets) {
	array_push($presets, 'all');
	asort($presets);
} else {
	$presets=array('all');
}
if (!empty($sessioninfo)) {
	$sessionpath=$sessioninfo['Image path'];
	$appionpath=getBaseAppionPath($sessioninfo);
	$extractpath=$appionpath."/extract/";
	$origjpgpath=preg_replace("%rawdata%","jpgs/",$sessionpath);
	$sessionname=$sessioninfo['Name'];
}

// Collect all Possible in an array
$run = array("label"=>"not selected","name"=>"as_input","imgtype"=>$_POST['imgtype'],"path"=>$_POST['imgdir']);
$allruns = array($run);

$run = array("label"=>"original mrcs","name"=>"rawdata","imgtype"=>"mrc","path"=>$sessionpath."/");
$allruns[] = $run;

if (file_exists($origjpgpath)) {
	$run = array("label"=>"original jpg files","name"=>"jpg","imgtype"=>"jpg","path"=>$origjpgpath);
	$allruns[] = $run;
}

// Add particle picking runs
$prtlrunInfos = $particle->getParticleRunIds($sessionId);
$count = count($prtlrunInfos);
$i = 0;
while ($i < $count) {
	$rindex = $count - 1 -$i;
	$prtlrun = $prtlrunInfos[$rindex];
	$runname=$prtlrun['name'];
	$prtlstats=$particle->getStats($prtlrun['DEF_id']);
	$totprtls=commafy($prtlstats['totparticles']);
	if (strlen($prtlrun['path']) > 10) $partpath = $prtlrun['path']."/jpgs/";
	else {
		// HACK for Particle Runs without Path Data
	        $partpath = $extractpath.$prtlrun['name']."/jpgs/";
	        if (!file_exists($partpath)) $partpath = $appionpath.$prtlrun['name']."/jpgs/";
	}
	$run = array("label"=>"particle picking: ".$runname." (".$totprtls." prtls)",
		"name"=>"prtl_".$prtlrun['DEF_id'],"imgtype"=>"jpg","path"=>$partpath);
	//echo $prtlrun['DEF_id']." == $pickId<br/>";
	if ($prtlrun['DEF_id'] == $pickId) {
		//echo "unshift<br/>";
		array_unshift($allruns, $run);
	} else {
		$allruns[] = $run;
	}
	//print_r($allruns);
	$i++;
}

// Add masking runs
$maskRunInfos = $particle->getMaskMakerRunIds($sessionId);
foreach ( $maskRunInfos as $maskRun ) {
	$runname = $maskRun['name'];

	if (strlen($maskRun['path']) > 10) $maskpath = $maskRun['path']."/masks/";
	else {
		// HACK for Particle Runs without Path Data
	        //$maskpath = $extractpath.$maskRun['name']."/masks/";
	        if (!file_exists($maskpath)) $maskpath = $appionpath.$maskRun['name']."/masks/";
	}
	
	// Find a file extension in this directory. There may be more than one, 
	// but let's at least start with a type that we know exists
	// If we fail to find a type, fail gracefully and just set the type to jpg.
	try {
		$type = findImageTypeInDir( $maskpath, $imgtypes );
		$imgtype = $type;
	} catch (Exception $e) {
		$imgtype = "jpg";
	}
			
	$run = array("label"=>"Masking Run: ".$runname,
		"name"=>"mask_".$maskRun['DEF_id'],"imgtype"=>$imgtype,"path"=>$maskpath);
	//echo $prtlrun['DEF_id']." == $pickId<br/>";
	if ($maskRun['DEF_id'] == $maskRunId) {
		//echo "unshift<br/>";
		array_unshift($allruns, $run);
	} else {
		$allruns[] = $run;
	}
}
	
// Choose best combination of settings
$lastimgrun = count($allruns)-1;
if ($_POST['oldimgtype'] != $_POST['imgtype']) {
	// Do not change $imgrun nor $imgdir if the change is $imgtype
	$imgrun = $_POST['imgrun'];
	$imgdir = $_POST['imgdir'];
	$imgtype = $_POST['imgtype'];
} else {
	if ($_POST['imgrun'] or count($_POST)) {
		// if selected run is changed, change the output directory etc.
		$imgrun = $_POST['imgrun'];
		if ($_POST['oldimgrun'] != $_POST['imgrun']) {
			$imgdir = $allruns[$imgrun]['path'];
			$imgtype = $allruns[$imgrun]['imgtype'];
		
		} else {

			$imgdir = $_POST['imgdir'];
			$imgtype = $_POST['imgtype'];
		}
	} else {
		// default at first loading.
		$imgrun = $lastimgrun;
		$imgdir = $allruns[$lastimgrun]['path'];
		$imgtype = $allruns[$lastimgrun]['imgtype'];
	}

	// if the output directory is specified so that is not in the available runs, change the run to "not selected"
	for ($i = 1; $i <=$lastimgrun; $i++) {
		$inselections += ($imgdir === $allruns[$i][path]) ? 1 : 0;
	}

	if ($inselections) {
		$imgdir = $allruns[$imgrun]['path'];
		$imgtype = $allruns[$imgrun]['imgtype'];
	} else {
		$imgrun = 0;
	}
}


// save for future comparison
echo "<INPUT TYPE='hidden' NAME='oldimgrun' VALUE='$imgrun'>";
echo "<INPUT TYPE='hidden' NAME='oldimgtype' VALUE='$imgtype'>";

// Read and Display images
echo"<TABLE CLASS='tableborder' CELLPADING='10' CELLSPACING='5'>\n";
echo"<TR><TD COLSPAN='3' ALIGN='CENTER'>\n";

// Find the mask assessment run id found in ApMaskAssessmentRunData
$maskAssessRunId = 0;
$maskRunSelected = strpos($imgdir, "/masks/");
if ( $maskRunSelected && !$maskRunId ) {
	$maskRunPath = rstrtrim($imgdir, "/masks/");
	$maskRunId = $particle->getMaskMakerRunByPath($sessionId,$maskRunPath);
}
if ( $maskRunId ) {
	$maskAssessRunId = $particle->getMaskAssessRunId($sessionId, $maskRunId);
}


$files = array();
$presettype = $_POST['presettype'];
if ($presettype=='all') {
	$typematch ='';
} else {
	$typematch =$presettype;
}


if ($imgdir) {
	// make sure imgdir ends with '/'
	if (substr($imgdir,-1,1)!='/') $imgdir.='/';
	if (!file_exists($imgdir))
		echo "<FONT class='apcomment'>Specified path: $imgdir does not exist</FONT><HR>\n";
	else {
		$starttime = microtime();
		// open image directory
		// get all files in directory, ordered by time created
		$ext= $imgtype ? $imgtype : "jpg";
		$i=0;
		if (!$typematch) {
			$allfiles = glob($imgdir."*.".$ext);
		} else {
			$allfiles = glob($imgdir."*".$typematch."[\._]*.".$ext);
			if (empty($allfiles)) $allfiles = glob($imgdir."*".$typematch."*.".$ext);
			//echo "TYPEMATCH: '".$typematch."'<br/>";
		}
		foreach ($allfiles as $filepath) {
			$filename = basename($filepath);
		    $excludeExt = "_tmp.jpg"; //This is a poor workaround for now. these tmp files are created for labeling regions.
		    // TODO: it would actually be better to use the tmp files as the overlay. 
			$exclude = strpos($filename, $excludeExt) ;
			if ( !$exclude && (!$typematch || preg_match('`'.$typematch.'(_[0-9][0-9])?\.`',$filename)) ) {
		      $files[$i][0] = $filename;
		      $files[$i][1] = filemtime($filepath);
		      // Add the original MRC image so that we can overlay masks on it.
		      $maskExts = array("_mask.png", "_mask.jpg");
		      foreach ( $maskExts as $maskExt ) {
			      if ( false !== strpos($filename, $maskExt) )
			      {
			      	$files[$i][0] = $sessionpath."/".rstrtrim($filename, $maskExt).".mrc";
			      	$files[$i][2] = $filename;
			      } 
		      }
		      $i++;
			}
		}
		if ($files) {
			// sort the files by time
			foreach($files as $t) $sortTime[] = $t[1];
			array_multisort($sortTime, SORT_ASC, $files);
			// save sorted file list
			foreach($files as $t) $fileList[] = $t[0];
			// display image			
			displayImagePanel( /*$fileList*/$files, $imgdir, $leginondata, $particle, $assessmentrid, $maskAssessRunId, $maskRunId );
			//echo "read ".count($files)." files in ".(microtime()-$starttime)." seconds<br/>\n";
		}
		else echo"<FONT class='apcomment'>No file found in this directory with extension: $ext or preset: $presettype </FONT><HR>\n";
	}

}
echo"</CENTER>\n";
echo"<hr></TD></tr>\n";

//SELECT A RUN CONTAINING IMAGES
echo"<TR ALIGN='CENTER'><TD VALIGN='TOP' COLSPAN='3'>\n";
echo "Select a run with images:
<SELECT NAME='imgrun' onchange='this.form.submit()'>\n";
$i = 0;
foreach ($allruns as $run){
		echo "<OPTION VALUE=".$i." ";
		$runname=$run['name'];
		$s = ($imgrun==$i) ? " SELECTED": '';
		echo " $s>".$run['label']."</OPTION>\n";
		$i++;
}
echo "</SELECT>\n";

echo"<br><hr></TD></tr>\n";

// HEADER FORM FOR FILLING IMAGE PATH
echo"<TR ALIGN='CENTER'><TD VALIGN='TOP'>\n";
echo"&nbsp;<B>Image Directory:</B><br>\n";
echo"<INPUT TYPE='text' NAME='imgdir' VALUE='$imgdir' SIZE='60' onchange='this.form.submit()'></TD>\n";

// IMAGE TYPE
echo"<TD VALIGN='TOP'>\n";
echo"<B>Image Type:</B><br>\n";
echo"<SELECT NAME='imgtype' onchange='this.form.submit()'>\n";
foreach ($imgtypes as $type) {
	$s = ($imgtype==$type) ? 'SELECTED' : '';
	echo "<OPTION $s>$type</OPTION>\n";
}
echo"</SELECT>\n";
echo"</TD>";

// PRESET
echo"<TD VALIGN='TOP'>\n";
echo"<B>Preset:</B><br>\n";
echo"<SELECT NAME='presettype' onchange='this.form.submit()'>\n";
foreach ($presets as $type) {
	$s = ($_POST['presettype']==$type) ? 'SELECTED' : '';
	echo "<OPTION $s>$type</OPTION>\n";
}
echo"</SELECT>\n";
echo"<br></TD></tr>\n";

echo"</table>\n";
echo"</FORM>\n";

echo appionRef();

processing_footer();

//****************************************
function displayImagePanel($files,$imgdir,$leginondata,$particle,$assessmentrid, $maskAssessRunId, $maskRunId ) {
	$numfiles = count($files);
	$imgindex = ($_POST['imgindex']) ? $_POST['imgindex'] : '0';
	$imgperpage = ($_POST['imgperpage']) ? $_POST['imgperpage'] : 15;

	//find first and last good images
	//if (!$_POST['firstindex'] || !$_POST['lastindex'] || $_POST['skipimages'] != $_POST['oldskipimages']) {
	$firstindex = getNextImage($files, 0, $numfiles, $leginondata, $particle, $assessmentrid)-1;
	$lastindex = getPrevImage($files, $numfiles, $firstindex, $leginondata, $particle, $assessmentrid);
	//echo "i$imgindex f$firstindex l$lastindex";

	# make sure status does not get updated when switching runs
	$same_run = ($_POST['imgrun'] && $_POST['imgrun']==$_POST['oldimgrun'] );
	if ($same_run && $maskAssessRunId) {
		updateMaskStatuses($files, $imgindex, $lastindex, $leginondata, $particle, $maskAssessRunId, $assessmentrid, $maskRunId );
	}
	
	if ($_POST['imgjump']) {
	// go directly to a particular image by number or filename
		$imgindex = $_POST['imgjump']-1;
		// make sure it's within range
		if ($imgindex < $firstindex)
			$imgindex = $firstindex;
		elseif ($imgindex > $lastindex)
			$imgindex = $lastindex;
	} elseif ($_POST['imagelist_back_x']) {
	// go to previous image
		updateImageStatuses($files, $imgindex, $lastindex, $leginondata, $particle, $assessmentrid);
		if ($_POST['previndex'])
			$imgindex = $_POST['previndex'];
		else
			$imgindex = getPrevImage($files, $imgindex-$imgperpage, $firstindex, $leginondata, $particle, $assessmentrid);
	} elseif ($_POST['imagelist_next_x']) {
	// go to next image
		echo "<INPUT TYPE='HIDDEN' NAME='previndex' VALUE='$imgindex'>\n";
		updateImageStatuses($files, $imgindex, $lastindex, $leginondata, $particle, $assessmentrid);
		$imgindex = $_POST['nextindex'];
	} elseif ($_POST['imagelist_first_x']) {
	// go to first image
		$imgindex = $firstindex;
	} elseif ($_POST['imagelist_last_x']) {
	// go to last image
		$imgindex = $lastindex;
	}

	//echo "i$imgindex f$firstindex l$lastindex";
	echo "<INPUT TYPE='HIDDEN' NAME='firstindex' VALUE='$firstindex'>\n";
	echo "<INPUT TYPE='HIDDEN' NAME='lastindex' VALUE='$lastindex'>\n";
	echo "<INPUT TYPE='HIDDEN' NAME='oldskipimages' VALUE='".$_POST['skipimages']."'>\n";
	echo "<INPUT TYPE='HIDDEN' NAME='imgindex' VALUE='$imgindex'>\n";
	echo "<INPUT TYPE='HIDDEN' NAME='imgperpage' VALUE='$imgperpage'>\n";

	echo"<table border='0' cellpadding='0' cellspacing='0'>";
	echo "<tr><td colspan='15' align='center'>";
	printToolBarRow();
	echo "</td></tr><tr><td rowspan='15'>\n";
	printToolBarSide();
	echo"</TD><td>\n";
	$tool = false;
	$curindex = $imgindex;
	for ($i = 0; $i < $imgperpage; $i += 1) {
		$file = $files[$curindex];
		//echo "c$curindex i$imgindex f$firstindex l$lastindex";
		displayImage($file, $imgdir, $curindex, $leginondata, $particle, $assessmentrid, $maskAssessRunId, $maskRunId);
		if ((($i+1) % 3) == 0) {
			if (!$tool) {
				$tool = true;
				echo"</TD><TD rowspan='15'>\n";
				printToolBarSide();
			}
			echo "</td></tr><tr><td>";
		} else {
			echo "</td><td>";
		}
		$nextindex = getNextImage($files, $curindex, $lastindex, $leginondata, $particle, $assessmentrid);
		if ($curindex == $nextindex)
			break;
		$curindex = $nextindex;
	}
	echo "<INPUT TYPE='HIDDEN' NAME='nextindex' VALUE='$nextindex'>\n";

	echo "</td></tr><tr><td colspan='15' align='center'>";
	printToolBarRow();
	echo "</td></tr></table>\n";

	//Scale factor, etc.
	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='5'>\n";
	echo"<TR><TD ALIGN='LEFT'>\n";
	echo"<FONT SIZE='+1'>Image ".($imgindex+1)." of $numfiles</FONT>\n";
	echo"</TD><TD ALIGN='RIGHT'>";
	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='2'>\n";
	echo"<TR><TD ALIGN='RIGHT'>\n";
	echo"Jump to image:<br>";
	echo"(number)\n";
	echo"</TD><TD ALIGN='LEFT'>\n";
	echo"<INPUT TYPE='text' NAME='imgjump' SIZE='5'>";
	echo"</TD></tr></table>";
	echo"</TD><TD ALIGN='RIGHT'>\n";
	$imgrescl= ($_POST['imgrescale']) ? $_POST['imgrescale'] : 0.075; 
	echo"Scale Factor: <INPUT TYPE='text' NAME='imgrescale' VALUE='$imgrescl' SIZE='4'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER' COLSPAN='3'>\n";
	$skipallcheck=($_POST['skipimages']=='all') ? 'CHECKED' : '';
	$skiprejcheck=($_POST['skipimages']=='rejectonly') ? 'CHECKED' : '';
	$skipcheck=($_POST['skipimages']!='all' && $_POST['skipimages']!='rejectonly') ? 'CHECKED' : '';

	echo"<input type='radio' name='skipimages' value='all' $skipallcheck>Skip all assessed images&nbsp;\n";
	echo"<input type='radio' name='skipimages' value='rejectonly' $skiprejcheck>Skip only rejected images\n";
	echo"<input type='radio' name='skipimages' value='none' $skipcheck>Show all images\n";

	echo"</TD></tr></table>\n</CENTER>\n";
}

//****************************************
function updateImageStatuses ($files, $imgindex, $lastindex, $leginondata, $particle, $assessmentrid) {
	//echo "updateImageStatuses<br/>\n";
	$curindex = $imgindex;
	for ($i = 0; $i < $_POST['imgperpage']; $i += 1) {
		$filename  = $_POST['filename'.$curindex];
		$statdata  = getImageStatus($filename, $leginondata, $particle, $assessmentrid);
		$oldstatus = $statdata['status'];
		$newstatus = $_POST['imgstatus'.$curindex];
		$imageid   = $_POST['imageid'.$curindex];
		//echo "</br>STATUS index $curindex imgid $imageid old $oldstatus new $newstatus</br></br>\n";
		if ($newstatus != $oldstatus) {
			if($newstatus == 'yes') {
				$particle->updateKeepStatus($imageid, $assessmentrid,'1');
				//echo "</br><font color='green'>KEEP</font> index $curindex imgid $imageid old $oldstatus new $newstatus</br>\n";
			} elseif($newstatus == 'no')  {
				$particle->updateKeepStatus($imageid, $assessmentrid,'0');
				//echo "</br><font color='red'>REJECT</font> index $curindex imgid $imageid old $oldstatus new $newstatus</br>\n";
			}
		}
		$nextindex = getNextImage($files, $curindex, $lastindex, $leginondata, $particle, $assessmentrid);
		if ($curindex == $nextindex)
			break;
		$curindex = $nextindex;
	}
}


//****************************************
function updateMaskStatuses( $files, $imgindex, $lastindex, $leginondata, $particle, $maskAssessRunId, $assessmentrid, $maskRunId ) 
{
	//echo "updateMaskStatuses<br/>\n";
	$curindex = $imgindex;
	for ($i = 0; $i < $_POST['imgperpage']; $i += 1) {
		$filename  = $_POST['filename'.$curindex];
		$statdata  = getMaskStatus($filename, $leginondata, $particle, $maskRunId);
		$oldstatus = $statdata;
		$newstatus = $_POST['maskstatus'.$curindex];
		$imageid   = $_POST['imageid'.$curindex];
		if ($newstatus != $oldstatus) {
			//echo "</br>STATUS index: $curindex imgid: $imageid old: $oldstatus new: $newstatus</br></br>\n";
			if($newstatus == 'yes') {
				$particle->updateMaskAssessmentByImage($imageid, $maskAssessRunId,'1');
				//echo "</br><font color='green'>KEEP</font> index $curindex imgid $imageid old $oldstatus new $newstatus</br>\n";
			} elseif($newstatus == 'no')  {
				$particle->updateMaskAssessmentByImage($imageid, $maskAssessRunId,'0');
				//echo "</br><font color='red'>REJECT</font> index $curindex imgid $imageid old $oldstatus new $newstatus</br>\n";
			}
		}
		$nextindex = getNextImage($files, $curindex, $lastindex, $leginondata, $particle, $maskAssessRunId);
		if ($curindex == $nextindex)
			break;
		$curindex = $nextindex;
	}
}
//****************************************
function getNextImage ($files, $imgindex, $lastindex, $leginondata, $particle, $assessmentrid) {
	$found = false;
	while (!$found) {
		$imgindex++;
		//echo "Checking next file: $imgindex";
		if ($imgindex > $lastindex) {
			echo "<FONT COLOR='RED'> At end of image list</FONT><br>\n";
			$imgindex = $lastindex;
			$statdata=getImageStatus($files[$imgindex][0],$leginondata,$particle,$assessmentrid);
			return $imgindex;
		}
		$statdata=getImageStatus($files[$imgindex][0],$leginondata,$particle,$assessmentrid);
		if ($_POST['skipimages']!='none' && $statdata['status']=='no')
			$found=false;
		elseif ($_POST['skipimages']=='all' && $statdata['status']=='yes')
			$found=false;
		else
			$found=true;
	}
	return $imgindex;
}

//****************************************
function getPrevImage ($files, $imgindex, $firstindex, $leginondata, $particle, $assessmentrid) {
	$found = false;
	while (!$found) {
		$imgindex--;
		//echo "Checking prev file: $imgindex";
		if ($imgindex < $firstindex) {
			echo "<FONT COLOR='RED'> At start of image list</FONT><br>\n";
			$imgindex = $firstindex;
			$statdata=getImageStatus($files[$imgindex][0], $leginondata, $particle, $assessmentrid);
			return $imgindex;
		}
		$statdata=getImageStatus($files[$imgindex][0], $leginondata, $particle, $assessmentrid);
		if ($_POST['skipimages']!='none' && $statdata['status']=='no')
			$found=false;
		elseif ($_POST['skipimages']=='all' && $statdata['status']=='yes')
			$found=false;
		else
			$found=true;
	}
	return $imgindex;
}

//****************************************
function displayImage ($file, $imgdir, $filenum, $leginondata, $particle, $assessmentrid, $maskAssessRunId, $maskRunId) {
	//echo $file."<br/>\n";
	$statdata = getImageStatus($file[0], $leginondata, $particle, $assessmentrid);
	//echo print_r($statdata)."<br/>\n";
	$imgname   = $statdata['name'];
	$imgid     = $statdata['id'];
	$imgstatus = $statdata['status'];
	$imgfull   = $imgdir.$imgname;

	echo"<INPUT TYPE='HIDDEN' NAME='filename$filenum' VALUE='$imgname'>\n";
	echo"<INPUT TYPE='HIDDEN' NAME='imageid$filenum' VALUE='$imgid'>\n";

	//Image and tool bars on side
	echo"<CENTER>\n<TABLE BORDER='0' CELLPADDING='5' CELLSPACING='5'><TR><TD align='center'>\n";
	//printToolBar();
	//echo"</TD><td>\n";
	if ( !empty($file[2]) )
	{
		$filename = $file[0];
		$overlay = $imgdir.$file[2];
	} else {
		$overlay = '';
		$filename = $imgfull;
	}
	
	$imgrescl = ($_POST['imgrescale']) ? $_POST['imgrescale'] : 0.075;
	$imgurl = "<img src='loadimg.php?filename=".$filename."&scale=".$imgrescl."&overlay=".$overlay."'>\n";
	echo $imgurl;
	//echo"</TD><td>\n";
	//printToolBar();

	echo"</td></tr><tr><td align='center'>\n";

	// Current Image status
	echo "<br\><i>";
	echo "image number ".($filenum+1)."<br/>\n";
	echo "<font size='-3'>";
	echo $imgname;
	echo "</font></i><br/>\n";
	echo "Image Assessment Status: <b>\n";
	if ($imgstatus=='no') {
		echo"<font color='red' size='+1'>REJECT</font>";
		$rejecton = "CHECKED";
	} elseif ($imgstatus=='yes') {
		echo "<font color='green' size='+1'>KEEP</font>";
		$keepon = "CHECKED";
	} else {
		echo "none";
		$noneon = "CHECKED";
	}
	echo "</b><br/>\n";

	// Set status
	echo"<input type='radio' name='imgstatus$filenum' value='no' $rejecton><FONT COLOR='RED'>Reject</FONT>&nbsp;\n";
	echo"<input type='radio' name='imgstatus$filenum' value='yes' $keepon><FONT COLOR='GREEN'>Keep</FONT>\n";
	echo"<input type='radio' name='imgstatus$filenum' value='none' $noneon>None\n";	

	// Mask Status
	if ($overlay != '') {
		
		$maskstatus = getMaskStatus( $file[0], $leginondata, $particle, $maskRunId );
		
		echo "<br/>";
		echo "Mask Assessment Status: <b>\n";
		if ($maskstatus == 'no') {
			echo"<font color='red' size='+1'>REJECT</font>";
			$mrejecton = "CHECKED";
		} elseif ($maskstatus == 'yes') {
			echo "<font color='green' size='+1'>KEEP</font>";
			$mkeepon = "CHECKED";
		} else {
			echo "status error";
			$mnoneon = "CHECKED";
		}
		echo "</b><br/>\n";
	
		// Set mask status
		// All masks are set to keep by default when they are created.
		echo"<input type='radio' name='maskstatus$filenum' value='no' $mrejecton><FONT COLOR='RED'>Reject</FONT>&nbsp;\n";
		echo"<input type='radio' name='maskstatus$filenum' value='yes' $mkeepon><FONT COLOR='GREEN'>Keep</FONT>\n";
		//echo"<input type='radio' name='maskstatus$filenum' value='none' $mnoneon>None\n";
	}	
	
	echo"</TD></tr></table>\n";
}

//****************************************
function printToolBarRow() {
	echo"<TABLE BORDER='0' CELLPADDING='3' CELLSPACING='5'>\n";
	echo"<TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0' TYPE='IMAGE' SRC='img/button-first.png' ALT='First' NAME='imagelist_first' VALUE='First'>\n";
	echo"</TD><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0' TYPE='IMAGE' SRC='img/button-back.png' ALT='Back' NAME='imagelist_back' VALUE='Back'>\n";
	echo"</TD><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0'TYPE='IMAGE' SRC='img/button-next.png' ALT='Next' NAME='imagelist_next' VALUE='Next'>\n";
	echo"</TD><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0' TYPE='IMAGE' SRC='img/button-last.png' ALT='Last' NAME='imagelist_last' VALUE='Last'>\n";
	echo"</TD></tr></table>";
}

//****************************************
function printToolBarSide() {
	echo"<TABLE BORDER='0' CELLPADDING='3' CELLSPACING='5'>\n";
	echo"<TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0' TYPE='IMAGE' SRC='img/button-first.png' ALT='First' NAME='imagelist_first' VALUE='First'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0' TYPE='IMAGE' SRC='img/button-back.png' ALT='Back' NAME='imagelist_back' VALUE='Back'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0'TYPE='IMAGE' SRC='img/button-next.png' ALT='Next' NAME='imagelist_next' VALUE='Next'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT BORDER='0' TYPE='IMAGE' SRC='img/button-last.png' ALT='Last' NAME='imagelist_last' VALUE='Last'>\n";
	echo"</TD></tr></table>";
}

function getImageId( $imgname, $leginondata )
{
	global $sessionId;
	$imgbase = basename($imgname);
	$imageId = $leginondata->getId(array('MRC|image'=>$imgbase,'REF|SessionData|session'=>$sessionId),'AcquisitionImageData','DEF_id');
	
	// There can be two images with the same name if the images were uploaded again.
	// In this case getId() returns an array. Just use the first one.
	// TODO: this needs to be sorted out - we must return the correct image ID.
	// Try adding session Id? This seems to have worked.
	if ( is_array($imageId) ){
		$id = $imageId[0];
	} else {
		$id = $imageId;
	}
	
	return $id;
}
//****************************************
function getImageStatus( $imgname,$leginondata,$particle,$assessmentrid ) 
{

	// get the status of the image index
	$statdata['id'] 	= getImageId( $imgname, $leginondata );
	$statdata['status'] = $particle->getKeepStatus($statdata['id'],$assessmentrid);
	$statdata['name'] 	= $imgname;
	
	return $statdata;
}

function getMaskStatus( $imgname, $leginondata, $particle, $maskRunId ) 
{
	$statdata['id'] = getImageId( $imgname, $leginondata );
	if ($statdata['id']) {
		$maskstatus = $particle->getMaskAssessment( $statdata['id'], $maskRunId );
	}
	//echo "mask stat: $maskstatus ";
	
	$maskstatus =  ($maskstatus == "1") ? 'yes' : 'no';
	return $maskstatus;
}
/**
 * Strip a string from the end of a string
 *
 * @param string $str      the input string
 * @param string $remove   OPTIONAL string to remove
 * 
 * @return string the modified string
  */
function rstrtrim($str, $remove=null)
{
    $str    = (string)$str;
    $remove = (string)$remove;   
   
    if(empty($remove))
    {
        return rtrim($str);
    }
   
    $len = strlen($remove);
    $offset = strlen($str)-$len;
    while($offset > 0 && $offset == strpos($str, $remove, $offset))
    {
        $str = substr($str, 0, $offset);
        $offset = strlen($str)-$len;
    }
   
    return rtrim($str);   
   
} //End of function rstrtrim($str, $remove=null) 

// Will return the first filetype to be found from a list of file types ($fileTypes)
// in a given directory ($dir). If non of the specified types are found, returns False.
// If the directory provided does not exist, throws an exception. Wrap this in a try block!
function findImageTypeInDir( $dir, $fileTypes )
{
	// If the directory is not there, throw exception.
	if ( !file_exists( $dir ) ) {
		throw new Exception(" $dir does not exist.");
	}
	
	// Find a file extension in this directory. There may be more than one, 
	// but let's at least start with a type that we know exists
	$foundtype = False;
	$files = scandir($dir);
	foreach ( $files as $file ) {
		foreach ( $fileTypes as $type ) {
			if ( substr($file, -strlen($type)) == $type ) {
				$foundtype = $type;
				break;
			}
		}
	}
	
	return $foundtype;
}	


?>
