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
	runAverageTomogram();
}

// Create the form page
else {
	createAverageTomogramForm();
}

function createAverageTomogramForm($extra=false, $title='tomoaverage.py Launcher', $heading='Average Sub-Tomogram according to Stack Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];

	$particle = new particledata();

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	
	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// set max last ring radius
	$javascript .= "	var box = Math.floor(stackArray[2]);\n";
	$javascript .= "	document.viewerform.sizex.value = box;\n";
	$javascript .= "	document.viewerform.sizey.value = box;\n";
	$javascript .= "}\n";
	$javascript .= "</script>\n";
	$javascript .= writeJavaPopupFunctions('appion');  
	
	processing_header($title,$heading,$javascript);
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
		$outdir=ereg_replace("rawdata","tomo/average",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$stackval = ($_POST['stackval']) ? $_POST['stackval'] : NULL;
	$avgruns = $particle->getAveragedTomogramsFromSession($expId);
	$lastavgrunid = $avgruns[count($avgruns)-1]['avgid'];
	$nextavgrun = $lastavgrunid+1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'average'.$nextavgrun;
	$description = $_POST['description'];

	// find each stack entry in database
	$primarystackinfo = $particle->getSubTomogramStackIds($expId);
	$stackIds = array();
	$subtomoruns = array();
	$substacknames = array(0=>"align",1=>"cluster");
	foreach ($primarystackinfo as $pstackinfo) {
		$subtomorunid = $pstackinfo['subtomorunid'];
		$substackname = $pstackinfo['substackname'];
		foreach ($substacknames as $name) {
			if (substr_count($substackname,$name)) {
				$stackIds[] = $pstackinfo;
			} else {
				$namedstacks = $particle->getNamedSubStackIds($expId,$pstackinfo['stackid'],$name);
				$stackIds = array_merge($stackIds,$namedstacks);
			}
		}
	}
	// only allow most recent subtomogram stack in the selection for now
	$unique_stacks = array();
	foreach ($stackIds as $info) {
		if (!array_key_exists($info['stackid'],$unique_stacks)) $unique_stacks[$info['stackid']]=$info;
	}
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
  
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	echo docpop('tomostack','Stack:');
	$particle->getStackSelector($unique_stacks,$stackidval,'switchDefaults(this.value)');
	echo "<br/>\n";
  echo "<P>";
	echo docpop('avgtomorunname','Runname');
  echo "<INPUT TYPE='text' NAME='runname' SIZE='15' VALUE='$runname'>\n";
	echo "<FONT>(avgtomogram creating run name)</FONT>
		<br/>";
	echo"<P>
			<B> Tomogram Average Description:</B><br>
			<TEXTAREA NAME='description' ROWS='2' COLS='40'>$description</TEXTAREA>
		  </TD>
    </tr>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>";       
	echo "	  		
		<p><br />
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
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	echo getSubmitForm("Average Tomograms");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}
	processing_footer();
	exit;
}

function runAverageTomogram() {
	$projectId=getProjectId();
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "tomoaverage.py ";

	$runname=$_POST['runname'];
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$sessionname=$_POST['sessionname'];

	$particle = new particledata();
	$selectionruns = $particle->getParticleRunsFromStack($stackidval);
//make sure a tomogram was entered
	if (!$runname) createAverageTomogramForm("<B>ERROR:</B> Select a full tomogram to be boxed");
	//make sure a particle run or stack is chosen
	if (!$stackidval) createAverageTomogramForm("<B>ERROR:</B> Select a stack that is used in making subtomograms");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createAverageTomogramForm("<B>ERROR:</B> Enter a brief description of the tomogram");

	$subtomorunid = $particle->getSubTomoRunFromStack($stackidval);
	$command.="--projectid=$projectId ";
	$command.="--subtomorunId=$subtomorunid ";
	$command.="--runname=$runname ";
	$command.="--stackId=$stackidval ";
	$command.="--description=\"$description\" ";
	$command.="--commit ";

	// submit job to cluster
	if ($_POST['process']=="Average Tomograms") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createAverageTomogramForm("<B>ERROR:</B> You must be logged in to submit");
		$rundir = $outdir.'/'.$runname;
		echo $rundir;
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'tomoaverage',False,False,False);
		// if errors:
		if ($sub) createAverageTomogramForm("<b>ERROR:</b> $sub");

		// check that process finished properly
		$jobf = $rundir.'/'.$runname.'.appionsub.log';
		$status = "Averaged Tomogram was created";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while processing, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Tomogram Averaging", "Tomogram Averaging");
		echo "$status\n";
	}

	else processing_header("Tomogram Average Command","Tomogram Average Command");
	
	// rest of the page
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>Tomogram Average Command:</B><br>
	$command
	</TD></tr>
	<TR><td>average runname</TD><td>$runname</TD></tr>
	";
	echo"
	<TR><td>stack id</TD><td>$stackidval</TD></tr>
	<TR><td>subtomogram run id</TD><td>$subtomorunid</TD></tr>
	<TR><td>description</TD><td>$description</TD></tr>
	</table>\n";
	processing_footer();
}

?> 

