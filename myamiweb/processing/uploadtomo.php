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
	runUploadTomogram();
}

// Create the form page
else {
	createUploadTomogramForm();
}

function createUploadTomogramForm($extra=false, $title='UploadTomogram.py Launcher', $heading='Upload Tomogram') {
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
	$extrabin = ($_POST['extrabin']) ? $_POST['extrabin'] : '1';
	$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
	// Runname is determined by tiltseries if not manually set
	$alignruns = $particle->countTomoAlignmentRuns($tiltseriesId);
	$autorunname = 'upload'.($alignruns+1);
	$runname = ($_POST['lasttiltseries']==$tiltseriesId) ? $_POST['runname']:$autorunname;
	// Volumename is determined by tiltseries amd runname if not manually set
	$volumeruns = $particle->countTomogramsByAlignment($tiltseriesId,$runname);
	$autovolumename = 'volume'.($volumeruns+1);
	$volume = ($_POST['lastrunname']==$runname && $_POST['lasttiltseries']==$tiltseriesId) ? $_POST['volume']:$autovolumename;
	$tomofilename = ($_POST['tomofilename']) ? $_POST['tomofilename'] : '';
	$xffilename = ($_POST['xffilename']) ? $_POST['xffilename'] : '';
	$orientation = ($_POST['orientation']) ? $_POST['orientation'] : '';
	$snapshot = ($_POST['snapshot']) ? $_POST['snapshot'] : '';
	$description = $_POST['description'];
	$outdir .= $tomofilename.'mrc';
	$alltiltseries = $particle->getTiltSeries($expId);
	$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId); 
	$tiltSeriesSelector = $seriesselector_array[0];
	// Need these to notify that the values has changed in the next reload
	echo "<input type='hidden' name='lasttiltseries' value='$tiltseriesId'>\n";
	echo "<input type='hidden' name='lastrunname' value='$runname'>\n";
  
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	
  echo"
	<B>Original Tomogram file name with path:</B><br>
      <INPUT TYPE='text' NAME='tomofilename' VALUE='$tomofilename' SIZE='50'><br />\n
	<br/>
	<B>(Optional) Original Full Tomogram Transform file name (.xf) with path:</B><br>
      <INPUT TYPE='text' NAME='xffilename' VALUE='$xffilename' SIZE='50'><br />\n
	<B>(Optional) Original Snapshot file name with path:</B><br>
      <INPUT TYPE='text' NAME='snapshot' VALUE='$snapshot' SIZE='50'><br />\n";

	$choices = array('XYZ:right-handed','XYZ:left-handed','XZY:right-handed','XZY:left-handed');	
	$selector = '<select name="orientation" '
				.'size=5 '
				.'onchange=submit()>';
	foreach ($choices as $choice) {
		$selector .= '<option class="fixed" value='.$choice;
		if ($choice == $orientation) {
			$selector .= ' selected ';
			$selected_number = $number;
		}
		$selector .= '>'.$choice.'</option>';
	}
	$selector .= '</select>';
	echo $selector;
	echo docpop('tomoorientation', 'Tomogram Orientation');
	echo"<P>
      <B>Tomogram Description:</B><br>
      <TEXTAREA NAME='description' ROWS='2' COLS='40'>$description</TEXTAREA>
      </TD>
    </tr>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>";       


	echo "
	
		<B> <CENTER>Tomogram Params: </CENTER></B>

      <P>
      <INPUT TYPE='text' NAME='extrabin' SIZE='5' VALUE='$extrabin'>\n";
		echo docpop('extrabin','Binning');
		echo "<FONT>(additional binning in tomogram)</FONT>
		<p><br />";
		echo $seriesselector_array[0];
  #    <INPUT TYPE='text' NAME='tiltseries' VALUE='$tiltseries' SIZE='5'>\n";
		echo docpop('tiltseries_upload', 'Tilt Series');
		#echo "<FONT>(tilt series)</FONT>";
   
	if (!$sessionname) {
		echo "
		<br>
      <INPUT TYPE='text' NAME='sessionname' VALUE='$sessionname' SIZE='5'>\n";
		echo docpop('session', 'Session Name');
		echo "<FONT> (leginon session name)</FONT>";
	}
		echo "	  		
		<p><br />
      <INPUT TYPE='text' NAME='runname' VALUE='$runname' SIZE='10'>\n";
		echo docpop('tomorunname', 'Runname');
   	echo "<FONT>(full tomogram reconstruction run name)</FONT>";     
		echo "	  		
		<p><br />
      <INPUT TYPE='text' NAME='volume' VALUE='$volume' SIZE='10'>\n";
		echo docpop('volume', 'Volume');
   	echo "<FONT>(subvolume name)</FONT>     

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
	echo getSubmitForm("Upload Tomogram");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runUploadTomogram() {
	/* *******************
	PART 1: Get variables
	******************** */

	$tomofilename=$_POST['tomofilename'];
	$xffilename=$_POST['xffilename'];
	$tiltseriesId=$_POST['tiltseriesId'];
	$runname=$_POST['runname'];
	$volume=$_POST['volume'];
	$sessionname=$_POST['sessionname'];
	$extrabin=$_POST['extrabin'];
	$snapshot=$_POST['snapshot'];
	$orientation=$_POST['orientation'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a tilt series was provided
	if (!$tiltseriesId) createUploadTomogramForm("<B>ERROR:</B> Select the tilt series");
//make sure a tomogram was entered
	if (!$tomofilename) createUploadTomogramForm("<B>ERROR:</B> Enter a tomogram to be uploaded");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createUploadTomogramForm("<B>ERROR:</B> Enter a brief description of the tomogram");

	$transform = '';
	if ($orientation) {
		$splitorientation = explode(':',$orientation);
		$order = $splitorientation[0];
		$handness = $splitorientation[1];
		if ($volume) {
			if ($order =='XYZ') {
				$transform = ($handness == 'right-handed') ? '' : 'flipz';
			} else {
				if ($order == 'XZY') {
					$transform = ($handness == 'right-handed') ? 'rotx' : 'flipyz';
				}
			}
		} else {
			if ($order =='XZY') {
				$transform = ($handness == 'right-handed') ? '' : 'flipx';
			} else {
				if ($order == 'XYZ') {
					$transform = ($handness == 'right-handed') ? 'rotx' : 'flipyz';
				}
			}
		}
	} 
	$particle = new particledata();
	$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
	$apix = $tiltseriesinfos[0]['ccdpixelsize'] * $tiltseriesinfos[0]['imgbin'] * $extrabin * 1e10;
	$tiltseriesnumber = $tiltseriesinfos[0]['number'];

	/* *******************
	PART 3: Create program command
	******************** */

	$command = "uploadTomo.py ";
	$command.="--file=$tomofilename ";
	$command.="--session=$sessionname ";
	$command.="--bin=$extrabin ";
	$command.="--tiltseries=$tiltseriesnumber ";
	if ($transform) $command.="--transform=\"$transform\" ";
	if ($order) $command.="--order=$order ";
	if ($volume) $command.="--volume=$volume ";
	if ($xffilename) $command.="--xffile=$xffilename ";
	$command.="--description=\"$description\" ";
	if ($snapshot) 
		$command.="--image=$snapshot ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= appionRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);

	// if error display them
	if ($errors)
		createUploadTomogramForm($errors);
	exit;
	
}


?> 

