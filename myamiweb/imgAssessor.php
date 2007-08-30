<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
require ('inc/leginon.inc');

$particledata=new particledata();

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
$projectId=$_POST['projectId'];

/////////// temporary fix for new database //////////////

$hasassrun=($particledata->getLastAssessmentRun($expId)) ? true : false;
if ($hasassrun){
	$assessmentrid=$particledata->getLastAssessmentRun($sessionId);
}
else {
	$assrundata['name']='run1';
	$assrundata['dbemdata|SessionData|session']=$expId;
	$particledata->mysql->SQLInsert('ApAssessmentRunData',$assrundata);
	$assessmentrid=$particledata->getLastAssessmentRun($sessionId);
}

////////////////////////////////////////////////////////

$imgtypes=array('jpg','png','mrc','dwn.mrc');

$javascript="<script src='js/viewer.js'></script>\n";
writeTop("Leginon Image Assessor","Image Assessor",$javascript);
echo"<form name='viewerform' method='POST' ACTION='$formAction'>\n";
echo"<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
$sessioninfo=$sessiondata['info'];
$presets=$sessiondata['presets'];

// add preset choice of all presets
array_push($presets, 'all');
asort($presets);

if (!empty($sessioninfo)) {
        $sessionpath=$sessioninfo['Image path'];
	$sessionpath=ereg_replace("leginon","appion",$sessionpath);
	$sessionpath=ereg_replace("rawdata","extract/",$sessionpath);
	$sessionname=$sessioninfo['Name'];
}
// if session is changed, change the output directory
$sessionpathval=(($_POST['sessionId']==$_POST['lastSessionId'] || $expId) && $_POST['lastSessionId']) ? $_POST['imgdir'] : $sessionpath;

echo"<BR><A HREF='processing.php?expId=$sessionId'>[processing page]</A>\n";
echo"<P>\n";
echo"<TABLE BORDER=0 CLASS=tableborder WIDTH='600'>\n";
echo"<TR><TD VALIGN='TOP'>\n";
echo"<B>Image Directory:</B><BR>\n";
echo"<INPUT TYPE='text' NAME='imgdir' VALUE='$sessionpathval' SIZE='60' onchange='this.form.submit()'></TD>\n";
echo"<TD VALIGN='TOP'>\n";
echo"<B>Image Type:</B><BR>\n";
echo"<SELECT NAME='imgtype' onchange='this.form.submit()'>\n";
foreach ($imgtypes as $type) {
        $s = ($_POST['imgtype']==$type) ? 'SELECTED' : '';
	echo "<OPTION $s>$type</OPTION>\n";
}
echo"</SELECT>\n";
echo"</TD>";
echo"<TD VALIGN='TOP'>\n";
echo"<B>Preset:</B><BR>\n";
echo"<SELECT NAME='presettype' onchange='this.form.submit()'>\n";
foreach ($presets as $type) {
        $s = ($_POST['presettype']==$type) ? 'SELECTED' : '';
	echo "<OPTION $s>$type</OPTION>\n";
}
echo"</SELECT>\n";
echo"</TD></TR>\n";
echo"<TR><TD COLSPAN='2' ALIGN='CENTER'>\n";

$imgdir=$_POST['imgdir'];
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
        if (file_exists($imgdir)) {
                // open image directory
                $pathdir=opendir($imgdir);
		// get all files in directory, ordered by time created
		$ext=$_POST['imgtype'];
		$i=0;
		while ($filename=readdir($pathdir)) {
		  if ($filename == '.' || $filename == '..') continue;
		  if (preg_match('`\.'.$ext.'$`i',$filename)) {
                    if (preg_match('`'.$typematch.'\.`',$filename)) {
		      $files[$i][0] = $filename;
		      $files[$i][1] = filemtime($imgdir.$filename);
		      $i++;
                    }
		  }
		}
		closedir($pathdir);
		if ($files) {
		  // sort the files by time
		  foreach($files as $t) $sortTime[] = $t[1];
		  array_multisort($sortTime, SORT_ASC, $files);
		  // save sorted file list
		  foreach($files as $t) $fileList[] = $t[0];
		  // display image
		  $skipcheck=($_POST['skipdone']=='on') ? 'CHECKED' : '';
		  $skiprejcheck=($_POST['skiprejected']=='on') ? 'CHECKED' : '';
		  echo "<INPUT TYPE='CHECKBOX' NAME='skipdone' $skipcheck>Skip assessed images<BR>\n"; 
		  echo "<INPUT TYPE='CHECKBOX' NAME='skiprejected' $skiprejcheck>Skip rejected images<BR>\n"; 
		  displayImage($_POST,$fileList,$imgdir,$leginondata,$particledata,$assessmentrid);
		}
		else echo"<HR><FONT COLOR='RED'>No files found in this directory with extension: $ext</FONT>\n";
	}
	else echo "<HR><FONT COLOR='RED'>Specified path: $_POST[imgdir] does not exist</FONT>\n";
}

echo"</CENTER>\n";
echo"</TD></TR>\n";
echo"</TABLE>\n";
echo"</FORM>\n";
writeBottom();


function displayImage ($_POST,$files,$imgdir,$leginondata,$particledata,$assessmentrid){

        $numfiles=count($files);
	$imlst=$_POST['imagelist'];
        $imgindx= ($_POST['imgindex']) ? $_POST['imgindex'] : 0;
	$imgrescl= ($_POST['imgrescale']) ? $_POST['imgrescale'] : 0.5; 
	echo "<BR>\n";

	// go directly to a particular image number
	if ($_POST['imgjump']) {
		$key = array_search($_POST['imgjump'],$files);
		if ($key) {
			$imgindx=$key;
		} else {
	        	$imgindx=$_POST['imgjump']-1;
		}
		// make sure it's within range
		if ($imgindx < 0) $imgindx=0;
		elseif ($imgindx > $numfiles-1) $imgindx=$numfiles-1;
		$statdata=getImageStatus($files[$imgindx],$leginondata,$particledata,$assessmentrid);
	}
	// otherwise, increment or decrement the displayed image
	else {
	        if ($imlst=='Back') {
		        while ($found!='TRUE') {
		                $imgindx--;
				if ($imgindx < 0) {
				        echo "<FONT COLOR='RED'> At beginning of image list</FONT><BR>\n";
					$imgindx=0;
					$statdata=getImageStatus($files[$imgindx],$leginondata,$particledata,$assessmentrid);
					break;
				}
				$statdata=getImageStatus($files[$imgindx],$leginondata,$particledata,$assessmentrid);
				if ($_POST['skipdone']=='on') {
				        if ($statdata['status']=='no' || $statdata['status']=='yes') $found='FALSE';
					else $found='TRUE';
				}
				if ($_POST['skiprejected']=='on') {
				        if ($statdata['status']=='no') $found='FALSE';
					else $found='TRUE';
				}
				else break;
			}
		}
		elseif ($imlst=='Next' || $imlst=='Keep' || $imlst=='Remove') {
		        if($imlst=='Keep') $particledata->updateKeepStatus($_POST['imageid'],$assessmentrid,'1');
			if($imlst=='Remove') $particledata->updateKeepStatus($_POST['imageid'],$assessmentrid,'0');
		        while ($found!='TRUE') {
			        $imgindx++;
				if ($imgindx > $numfiles-1) {
				        echo "<FONT COLOR='RED'> At end of image list</FONT><BR>\n";
					$imgindx=$numfiles-1;
					$statdata=getImageStatus($files[$imgindx],$leginondata,$particledata,$assessmentrid);
					break;
				}
				$statdata=getImageStatus($files[$imgindx],$leginondata,$particledata,$assessmentrid);
				if ($_POST['skipdone']=='on') {
				        if ($statdata['status']=='no' || $statdata['status']=='yes') $found='FALSE';
					else $found='TRUE';
				}
				if ($_POST['skiprejected']=='on') {
				        if ($statdata['status']=='no') $found='FALSE';
					else $found='TRUE';
				}
				else break;
			}
		}
		else {
		        if ($imlst=='First') $imgindx=0;
			elseif ($imlst=='Last') $imgindx=$numfiles-1;
			$statdata=getImageStatus($files[$imgindx],$leginondata,$particledata,$assessmentrid);
		}
	}


	$imgname=$statdata['name'];
	$imgid=$statdata['id'];
	$imgstatus=$statdata['status'];

	$thisnum=$imgindx+1;
	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='0' WIDTH='400'>\n";
	echo"<TR><TD ALIGN='LEFT'>\n";
	echo"Image $thisnum of $numfiles</TD>\n";
	echo"<TD ALIGN='RIGHT'>Jump to image:";
	echo"<INPUT TYPE='text' NAME='imgjump' SIZE='5'>\n";
        echo"Scale Factor:<INPUT TYPE='text' NAME='imgrescale' VALUE='$imgrescl' SIZE='4'>\n";
	echo"</TD></TR></TABLE>";
	echo"<BR>$imgname<HR>\n<B>Current Status: ";
	if ($imgstatus=='no') echo"<FONT COLOR='RED'>REJECT</FONT>";
	elseif ($imgstatus=='yes') echo "<FONT COLOR='GREEN'>KEEP</FONT>";
	else echo"none";
	echo "</B>\n";

	$imgfull=$imgdir.$imgname;
	echo"<INPUT TYPE='HIDDEN' NAME='imgindex' VALUE='$imgindx'>\n";
	echo"<INPUT TYPE='HIDDEN' NAME='imageid' VALUE='$imgid'>\n";
	echo"<TABLE BORDER='0' CELLPADDING='5' CELLSPACING='0'><TR><TD>\n";
	echo"<INPUT TYPE='IMAGE' WIDTH='30' SRC='img/firstbutton.jpg' ALT='First' NAME='imagelist' VALUE='First'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/backbutton.jpg' ALT='Back' NAME='imagelist' VALUE='Back'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/stopbutton.jpg' ALT='Remove' NAME='imagelist' VALUE='Remove'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/playbutton.jpg' ALT='Keep' NAME='imagelist' VALUE='Keep'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/nextbutton.jpg' ALT='Next' NAME='imagelist' VALUE='Next'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' WIDTH='30' SRC='img/lastbutton.jpg' ALT='Last' NAME='imagelist' VALUE='Last'>\n";
	echo"</TD></TR></TABLE>\n";
	echo"<IMG SRC='loadimg.php?filename=$imgfull&scale=$imgrescl'><P>\n";
}

function getImageStatus ($imgname,$leginondata,$particledata,$assessmentrid) {
	// get the status of the image index
	//$particledata2=new particledata();
	
	$imgbase=split("\.",$imgname);
	$imgbase=$imgbase[0].".mrc";
	$statdata['id']=$leginondata->getId(array('MRC|image'=>$imgbase),'AcquisitionImageData','DEF_id');
	$statdata['status']=$particledata->getKeepStatus($statdata['id'],$assessmentrid);
	$statdata['name']=$imgname;
	return $statdata;
}
?>
