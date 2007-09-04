<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
require ('inc/ssh.inc');
require ('inc/appionloop.inc');
 
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runjpgmaker();
}

// CREATE FORM PAGE
else {
	createJMForm();
}


function createJMForm($extra=false, $title='JPEG Maker', $heading='Automated JPEG convertion with jpgmaker') {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=$_POST['projectId'];

	// --- find hosts to run maskmaker 
	$hosts=getHosts();
 

	$particle=new particleData;
	$javascript="
	<script src='js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
		 function enabledtest(){
			 if (document.viewerform.testimage.checked){
				 document.viewerform.testfilename.disabled=false;
				 document.viewerform.testfilename.value='';
			 }	
			 else {
				 document.viewerform.testfilename.disabled=true;
				 document.viewerform.testfilename.value='mrc file name';
			 }
		 }
		 function enable(thresh){
			 if (thresh=='auto') {
				 document.viewerform.autopik.disabled=false;
				 document.viewerform.autopik.value='';
				 document.viewerform.thresh.disabled=true;
				 document.viewerform.thresh.value='0.4';
			 }
			 if (thresh=='manual') {
				 document.viewerform.thresh.disabled=false;
				 document.viewerform.thresh.value='';
				 document.viewerform.autopik.disabled=true;
				 document.viewerform.autopik.value='100';
			 }
		 }
		 function infopopup(infoname){
			 var newwindow=window.open('','name','height=150,width=300');
			 newwindow.document.write('<HTML><BODY>');
			 if (infoname=='runid'){
				 newwindow.document.write('Specifies the name associated with the Template Correlator results unique to the specified session and parameters.	An attempt to use the same run name for a session using different Template Correlator parameters will result in an error.');
			 }
			 newwindow.document.write('</BODY></HTML>');
			 newwindow.document.close();
		 }
	</SCRIPT>\n";
	$javascript.=appionLoopJavaCommands();
	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];

	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	$process = ($_POST['process']) ? $_POST['process'] :'';
	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
		<TD VALIGN='TOP'>";
	createAppionLoopTable($sessiondata, 'jpgs', "", 1);
	echo"
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>
		<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
		Test these setting on image:
		<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
		<HR>
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		Host: <select name='host'>\n";
	foreach($hosts as $host) {
		$s = ($_POST['host']==$host) ? 'selected' : '';
		echo "<option $s >$host</option>\n";
	}
	echo "</select>
	<BR>
	User: <INPUT TYPE='text' name='user' value=".$_POST['user'].">
	Password: <INPUT TYPE='password' name='password' value=".$_POST['password'].">\n";
	echo"
		</select>
		<BR>
		<input type='submit' name='process' value='Just Show Command'>
		<input type='submit' name='process' value='Run JPEG Maker'><BR>
		<FONT COLOR='RED'>Submission will NOT run JPEG Maker, only output a command that you can copy and paste into a unix shell</FONT>
		<BR>
		</TD>
	</TR>
	</TABLE>
	</TD>
	</TR> 
	</TABLE>\n";
	?>

	</CENTER>
	</FORM>
	<?
	writeBottom();
}

function runjpgmaker() {
	$process = $_POST['process'];

	$outdir = $_POST['outdir'];
	$runid = $_POST['runid'];
	$dbimages = $_POST[sessionname].",".$_POST[preset];
	$norejects = ($_POST[norejects]=="on") ? "0" : "1";
	$nowait = ($_POST[nowait]=="on") ? "0" : "1";
	$commit = ($_POST[commit]=="on") ? "1" : "0";
	$apcontinue = $_POST[apcontinue];
	
	$command="jpgmaker.py ";
	
	if ($runid) $apcommand.=" runid=$runid";
	if ($outdir) $apcommand.=" outdir=$outdir";
	if ($testimage) $apcommand.=" $testimage";
	elseif ($dbimages) $apcommand.=" dbimages=$dbimages";
	else $apcommand.=" alldbimages=$_POST[sessionname]";
	//if ($norejects) $apcommand.=" norejects";
	//if ($nowait) $apcommand.=" nowait";
	//if ($commit) $apcommand.=" commit";
	//if (!$apcontinue) $apcommand.=" nocontinue";
	//else $apcommand.=" continue";
	
	//$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createMMForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	if ($_POST['testimage']=="on") {
		$command .= " test";
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
	}

	if ($testimage && $_POST['process']=="Run JPEG Maker") {
		$host = $_POST['host'];
		$user = $_POST['user'];
		$password = $_POST['password'];
		if (!($user && $password)) {
			createDogPickerForm("<B>ERROR:</B> Enter a user name and password");
			exit;
		}
		$command="source /ami/sw/ami.csh;".$command;
		$command="source /ami/sw/share/python/usepython.csh cvs32;".$command;
		$cmd = "$command > maskMakerLog.txt";
		$result=exec_over_ssh($host, $user, $password, $cmd, True);
	}

	writeTop("JPEG Maker Results","JPEG Maker Results",$javascript);

	if ($testimage) {
		$outdir=$_POST[outdir];
		// make sure outdir ends with '/'
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$runid=$_POST[runid];
		echo  " <B>MaskMaker Command:</B><BR>$command<HR>";
		$testjpg=ereg_replace(".mrc","",$testimage);
		$testdir=$outdir.$runid."/tests/";
        	if (file_exists($testdir)) {
                	// open image directory
                	$pathdir=opendir($testdir);
			// get all files in directory
			$ext='jpg';
			while ($filename=readdir($pathdir)) {
		        	if ($filename == '.' || $filename == '..') continue;
				if (preg_match('`\.'.$ext.'$`i',$filename)) $files[]=$filename;
			}
			closedir($pathdir);
		}
//		echo"<form name='viewerform' method='POST' ACTION='$formAction'>\n";
		if (count($files) > 0) 	{
			$images=displayTestResults($testimage,$testdir,$files);
		} else {
			echo "<FONT COLOR='RED'><B>NO RESULT YET</B><BR>";
			echo "<FONT COLOR='RED'><B>Refresh this page when ready</B><BR>";
		}
		createMMForm($images,'Particle Selection Results','');
		exit;
	}


	echo"
  
  <P>
  <TABLE WIDTH='600'>
  <TR><TD COLSPAN='2'>
  <B>JPEG Maker Command:</B><BR>
  $command<HR>
  </TD></TR>
  <TR><TD>outdir</TD><TD>$outdir</TD></TR>
  <TR><TD>runname</TD><TD>$runid</TD></TR>
  <TR><TD>dbimages</TD><TD>$dbimages</TD></TR>
  ";
  
  //<TR><TD>norejects</TD><TD>$norejects</TD></TR>
  //<TR><TD>nowait</TD><TD>$nowait</TD></TR>
  //<TR><TD>commit</TD><TD>$commit</TD></TR>
  //<TR><TD>continue</TD><TD>$apcontinue</TD></TR>

  
	//appionLoopSummaryTable();
	echo"</TABLE>\n";
	writeBottom();
}


function writeTestResults($testdir,$filelist){
	echo"<CENTER>\n";
	if (count($filelist)>1) echo "<BR>\n";
	foreach ($filelist as $file){
		echo $testdir.$file;
		echo"<A HREF='loadimg.php?filename=$testdir.$file&scale=0.25'>\n";
		echo"<IMG SRC='loadimg.php?filename=$testdir$file&scale=0.25'></A>\n";
	}
	echo"</CENTER>\n";
}

function displayTestResults($testimage,$imgdir,$files){
	echo "<CENTER>\n";
	echo"<form name='viewerform' method='POST' ACTION='$formAction'>\n";
//	$formAction=$_SERVER['PHP_SELF'];	
//	$javascript="<script src='js/viewer.js'></script>\n";
//	writeTop("Mask Maker Test","Mask Maker Test Results",$javascript);

//
        $numfiles=count($files);
	$prefix = '';
	$n = 0;

	sort($files);

	$imlst=($_POST['imagelist']) ? $_POST['imagelist'] : 'First';
        $imgindx= ($_POST['imgindex']) ? $_POST['imgindex'] : 0;
	$imgrescl= ($_POST['imgrescale']) ? $_POST['imgrescale'] : 0.25; 
	$process= ($_POST['process']) ? $_POST['process'] : '';
	// go directly to a particular image number
	if ($_POST['imgjump']) {
	        $imgindx=$_POST['imgjump']-1;
		// make sure it's within range
		if ($imgindx < 0) $imgindx=0;
		elseif ($imgindx > $numfiles-1) $imgindx=$numfiles-1;
		$imgname=$files[$imgindx];
	}
	// otherwise, increment or decrement the displayed image
	else {
	        if ($imlst=='Back') {
				$imgindx--;
				if ($imgindx < 0) {
				        echo "<FONT COLOR='RED'> At beginning of image list</FONT><BR>\n";
					$imgindx=0;
					$imgname=$files[$imgindx];
				}
				$imgname=$files[$imgindx];
		}
		elseif ($imlst=='Next') {
			        $imgindx++;
				if ($imgindx > $numfiles-1) {
					$imgindx=$numfiles-1;
					$imgname=$files[$imgindx];
				        echo "<FONT COLOR='RED'> At end of image list</FONT><BR>\n";
				}
				$imgname=$files[$imgindx];
		}
		else {
		        if ($imlst=='First') $imgindx=0;
			elseif ($imlst=='Last') $imgindx=$numfiles-1;
			$imgname=$files[$imgindx];
		}
	}

	$thisnum=$imgindx+1;

	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='0' WIDTH='400'>\n";
	echo"<TR><TD ALIGN='LEFT'>\n";
        echo"<B>$testimage</B>\n";
	echo"</TD></TR><TR><TD ALIGN='CENTER'>\n";
        echo"Scale Factor:<INPUT TYPE='text' NAME='imgrescale' VALUE='$imgrescl' SIZE='4'>\n";
	echo"</TD></TR></TABLE>";

	$imgfull=$imgdir.$imgname;
	echo"<INPUT TYPE='HIDDEN' NAME='imgindex' VALUE='$imgindx'>\n";
	echo"<HR>\n";
	echo"<TABLE BORDER='0' CELLPADDING='5' CELLSPACING='0'><TR><TD>\n";
	echo"<INPUT TYPE='IMAGE' WIDTH='30' SRC='img/firstbutton.jpg' ALT='First' NAME='imagelist' VALUE='First'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/backbutton.jpg' ALT='Back' NAME='imagelist' VALUE='Back'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/nextbutton.jpg' ALT='Next' NAME='imagelist' VALUE='Next'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' WIDTH='30' SRC='img/lastbutton.jpg' ALT='Last' NAME='imagelist' VALUE='Last'>\n";
	echo"</TD></TR></TR></TABLE>\n";
	echo"<B>$imgname</B>\n<P>";
	echo"<IMG SRC='loadimg.php?filename=$imgfull&scale=$imgrescl'><P>\n";
	echo "</CENTER>\n";
	echo"<INPUT TYPE='HIDDEN' NAME='process' VALUE=$process>\n";
}
?>
