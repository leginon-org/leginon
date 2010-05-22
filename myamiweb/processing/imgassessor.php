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
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";

$particle=new particledata();

// check if coming directly from a session
$expId=$_GET['expId'];
if ($expId) {
	$sessionId=$expId;
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
	$sessionId=$_POST['sessionId'];
	$formAction=$_SERVER['PHP_SELF'];	
}
$projectId=getProjectId();


/////////// temporary fix for new database //////////////

$hasassrun=($particle->getLastAssessmentRun($expId)) ? true : false;
if ($hasassrun){
	$assessmentrid=$particle->getLastAssessmentRun($sessionId);
}
else {
	$assrundata['name']='run1';
	$assrundata['REF|leginondata|SessionData|session']=$expId;
	$particle->mysql->SQLInsert('ApAssessmentRunData',$assrundata);
	$assessmentrid=$particle->getLastAssessmentRun($sessionId);
}

////////////////////////////////////////////////////////

$imgtypes=array('jpg','png','mrc','dwn.mrc');

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
	$extractpath=ereg_replace("rawdata","extract/",$sessionpath);
	$appionpath=ereg_replace("leginon","appion",$extractpath);
	$origjpgpath=ereg_replace("rawdata","jpgs/",$sessionpath);
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
	$allruns[] = $run;
	$i++;
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

			$imgdir = $_POST[imgdir];
			$imgtype = $_POST[imgtype];
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
		$imgdir = $allruns[$imgrun][path];
		$imgtype = $allruns[$imgrun][imgtype];
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
		// open image directory
		// get all files in directory, ordered by time created
		$ext = $imgtype ? $imgtype : "jpg";
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
			if (!$typematch || preg_match('`'.$typematch.'(_[0-9][0-9])?\.`',$filename)) {
		      $files[$i][0] = $filename;
		      $files[$i][1] = filemtime($filepath);
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
			displayImage($_POST,$fileList,$imgdir,$leginondata,$particle,$assessmentrid);
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


function displayImage ($_POST,$files,$imgdir,$leginondata,$particle,$assessmentrid) {

	$numfiles=count($files);
	$imlst=$_POST['imagelist'];
	$imgindx= ($_POST['imgindex']) ? $_POST['imgindex'] : 0;
	$imgrescl= ($_POST['imgrescale']) ? $_POST['imgrescale'] : 0.5; 
	//echo "<br>\n";

	//find first and last good images
	$imgstart=array('first','last');
	foreach ($imgstart as $start) {
			if ($start == 'first') {
				$timgindx=-1;
			} else {
				$timgindx=$numfiles;
			}
			while ($tfound!='TRUE') {
				if ($start == 'last')
					$timgindx--;
				else $timgindx++;

				if ($timgindx < 0) {
					$timgindx=0;
					$statdata=getImageStatus($files[$timgindx],$leginondata,$particle,$assessmentrid);
					break;
				}
				if ($imgindx > $numfiles-1 ) {
					$timgindx=$numfiles;
					$statdata=getImageStatus($files[$timgindx],$leginondata,$particle,$assessmentrid);
					break;
				}
				$statdata=getImageStatus($files[$timgindx],$leginondata,$particle,$assessmentrid);
				if ($_POST['skipimages']!='none' && $statdata['status']=='no')
					$tfound='FALSE';
				elseif ($_POST['skipimages']=='all' && $statdata['status']=='yes')
					$tfound='FALSE';
				else
					$tfound='TRUE';
			}
			if ($start =='first') $firstindx = $timgindx;
			else $lastindx = $timgindx-1;
	}
		
	// go directly to a particular image by number or filename
	if ($_POST['imgjump']) {
		// change the name to the same tail as the files
		$pieces = explode(".", $files[0]);
		if (count($pieces) > 1) {
			$tailpieces = array_slice($pieces,1);
			$tail = implode(".",$tailpieces);
			$jpieces = explode(".", $_POST['imgjump']);
			if (count($jpieces) > 1) {
				$jhead = $jpieces[0];
				$jumpimg = $jhead.'.'.$tail;
			} else {
				$jumpimg = $_POST['imgjump'];
			}
		} else {
			$jumpimg = $_POST['imgjump'];
		}

		$key = array_search($jumpimg,$files);
		if ($key) {
			$imgindx=$key;
		} else {
			$imgindx=$_POST['imgjump']-1;
		}
		// make sure it's within range
		if ($imgindx < $firstindx) $imgindx = $firstindx;
		elseif ($imgindx > $lastindx) $imgindx= $lastindx;

		$statdata=getImageStatus($files[$imgindx],$leginondata,$particle,$assessmentrid);
	}
	// otherwise, increment or decrement the displayed image
	else {
		if ($imlst=='Back') {
			while ($found!='TRUE') {
				$imgindx--;
				if ($imgindx < $firstindx) {
					echo "<FONT COLOR='RED'> At beginning of image list</FONT><br>\n";
					$imgindx=$firstindx;
					$statdata=getImageStatus($files[$imgindx],$leginondata,$particle,$assessmentrid);
					break;
				}
				$statdata=getImageStatus($files[$imgindx],$leginondata,$particle,$assessmentrid);
				if ($_POST['skipimages']!='none' && $statdata['status']=='no')
					$found='FALSE';
				elseif ($_POST['skipimages']=='all' && $statdata['status']=='yes')
					$found='FALSE';
				else
					$found='TRUE';
			}
		}
		elseif ($imlst=='Next' || $imlst=='Keep' || $imlst=='Remove') {
			if($imlst=='Keep') $particle->updateKeepStatus($_POST['imageid'],$assessmentrid,'1');
			if($imlst=='Remove') $particle->updateKeepStatus($_POST['imageid'],$assessmentrid,'0');
			while ($found!='TRUE') {
				$imgindx++;
				if ($imgindx > $lastindx) {
					echo "<FONT COLOR='RED'> At end of image list</FONT><br>\n";
					$imgindx= $lastindx;
					$statdata=getImageStatus($files[$imgindx],$leginondata,$particle,$assessmentrid);
					break;
				}
				$statdata=getImageStatus($files[$imgindx],$leginondata,$particle,$assessmentrid);
				if ($_POST['skipimages']!='none' && $statdata['status']=='no')
					$found='FALSE';
				elseif ($_POST['skipimages']=='all' && $statdata['status']=='yes')
					$found='FALSE';
				else
					$found='TRUE';
			}
		}
		else {
			if ($imlst=='First') $imgindx=$firstindx;
			elseif ($imlst=='Last') $imgindx=$lastindx;
			$statdata=getImageStatus($files[$imgindx],$leginondata,$particle,$assessmentrid);
		}
	}
	
	$imgname=$statdata['name'];
	$imgid=$statdata['id'];
	$imgstatus=$statdata['status'];

	$thisnum=$imgindx+1;
	echo"<br\>$imgname<br>\n<B>Current Status: ";
	if ($imgstatus=='no') echo"<FONT COLOR='RED'>REJECT</FONT>";
	elseif ($imgstatus=='yes') echo "<FONT COLOR='GREEN'>KEEP</FONT>";
	else echo"none";
	echo "</B>\n";

	$imgfull=$imgdir.$imgname;
	echo"<INPUT TYPE='HIDDEN' NAME='imgindex' VALUE='$imgindx'>\n";
	echo"<INPUT TYPE='HIDDEN' NAME='imageid' VALUE='$imgid'>\n";

	//Image and tool bars on side
	echo"<CENTER>\n<TABLE BORDER='0' CELLPADDING='5' CELLSPACING='5'><TR><td>\n";
	printToolBar();
	echo"</TD><td>\n";
	echo"<img src='loadimg.php?filename=$imgfull&scale=$imgrescl'>\n";
	echo"</TD><td>\n";
	printToolBar();
	echo"</TD></tr></table>\n";

	//Scale factor, etc.
	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='5'>\n";
	echo"<TR><TD ALIGN='LEFT'>\n";
	echo"<FONT SIZE='+1'>Image $thisnum of $numfiles</FONT>\n";
	echo"</TD><TD ALIGN='RIGHT'>";
	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='2'>\n";
	echo"<TR><TD ALIGN='RIGHT'>\n";
	echo"Jump to image:<br>";
	echo"(name or number)\n";
	echo"</TD><TD ALIGN='LEFT'>\n";
	echo"<INPUT TYPE='text' NAME='imgjump' SIZE='5'>";
	echo"</TD></tr></table>";
	echo"</TD><TD ALIGN='RIGHT'>\n";
	echo"Scale Factor: <INPUT TYPE='text' NAME='imgrescale' VALUE='$imgrescl' SIZE='4'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER' COLSPAN='3'>\n";
	$skipallcheck=($_POST['skipimages']=='all') ? 'CHECKED' : '';
	$skiprejcheck=($_POST['skipimages']=='rejectonly') ? 'CHECKED' : '';
	$skipcheck=($_POST['skipimages']!='all' && $_POST['skipimages']!='rejectonly') ? 'CHECKED' : '';
	echo"<input type='radio' name='skipimages' value='all' $skipallcheck>Skip all assessed images&nbsp;\n";
	//echo "<INPUT TYPE='CHECKBOX' NAME='skipdone' $skipcheck>Skip assessed images\n";
	echo"<input type='radio' name='skipimages' value='rejectonly' $skiprejcheck>Skip only rejected images\n";
	echo"<input type='radio' name='skipimages' value='none' $skipcheck>Show all images\n";
	//echo "<INPUT TYPE='CHECKBOX' NAME='skiprejected' $skiprejcheck>Skip rejected images\n"; 
	echo"</TD></tr></table>\n</CENTER>\n";
}

function printToolBar() {
	echo"<TABLE BORDER='0' CELLPADDING='3' CELLSPACING='5'>\n";
	echo"<TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/button-first.png' ALT='First' NAME='imagelist' VALUE='First'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/button-back.png' ALT='Back' NAME='imagelist' VALUE='Back'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/button-reject.png' ALT='Reject' NAME='imagelist' VALUE='Remove'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/button-keep.png' ALT='Keep' NAME='imagelist' VALUE='Keep'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/button-next.png' ALT='Next' NAME='imagelist' VALUE='Next'>\n";
	echo"</TD></tr><TR><TD ALIGN='CENTER'>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/button-last.png' ALT='Last' NAME='imagelist' VALUE='Last'>\n";
	echo"</TD></tr></table>";
}

function getImageStatus ($imgname,$leginondata,$particle,$assessmentrid) {
	// get the status of the image index
	
	$imgbase=split("\.",$imgname);
	$imgbase=$imgbase[0].".mrc";
	$statdata['id']=$leginondata->getId(array('MRC|image'=>$imgbase),'AcquisitionImageData','DEF_id');
	$statdata['status']=$particle->getKeepStatus($statdata['id'],$assessmentrid);
	$statdata['name']=$imgname;
	return $statdata;
}
?>
