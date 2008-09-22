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
	runSubStack();
}

// Create the form page
else {
	createSubStackForm();
}

function createSubStackForm($extra=false, $title='subStack.py Launcher', $heading='Make a partial Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$stackId = $_GET['sId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// save other params to url formaction
	$formAction.=($stackId) ? "&sId=$stackId" : "";

	// Set any existing parameters in form
	if (!$description) $description = $_POST['description'];
	$runid = ($_POST['runid']) ? $_POST['runid'] : 'sub'.$stackId;

	$subcheck = ($_POST['subsplit']=='sub' || !$_POST['process']) ? 'checked' : '';		
	$firstpdisable = ($subcheck) ? '' : 'disabled';		
	$lastpdisable = ($subcheck) ? '' : 'disabled';		
	$splitcheck = ($_POST['subsplit']=='split') ? 'checked' : '';		
	$splitdisable = ($splitcheck) ? '' : 'disabled';		
	$split = ($_POST['split']) ? $_POST['split'] : '2';		
	$firstp = ($_POST['firstp']) ? $_POST['firstp'] : '';		
	$lastp = ($_POST['lastp']) ? $_POST['lastp'] : '';		
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		

	// get outdir path
	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=$sessioninfo['Image path'];
	$outdir=ereg_replace("leginon","appion",$outdir);
	$outdir=ereg_replace("rawdata","stacks",$outdir);

	$javafunctions .= writeJavaPopupFunctions('appion');
	$javafunctions .="<script language='JavaScript'>\n";
	$javafunctions .="function subORsplit(check){\n";
	$javafunctions .="  if (check=='split'){\n";
	$javafunctions .="    document.viewerform.split.disabled=false;\n";
	$javafunctions .="    document.viewerform.firstp.disabled=true;\n";
	$javafunctions .="    document.viewerform.lastp.disabled=true;\n";
	$javafunctions .="    document.viewerform.split.value='2';\n";
	$javafunctions .="  }\n";
	$javafunctions .="  else {\n";
	$javafunctions .="    document.viewerform.split.disabled=true;\n";
	$javafunctions .="    document.viewerform.firstp.disabled=false;\n";
	$javafunctions .="    document.viewerform.lastp.disabled=false;\n";
	$javafunctions .="    document.viewerform.split.value='2';\n";
	$javafunctions .="    document.viewerform.firstp.value='';\n";
	$javafunctions .="    document.viewerform.lastp.value='';\n";
	$javafunctions .="  }\n";
	$javafunctions .="}";
	$javafunctions .="</script>\n";
	
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='red'>$extra</font>\n<hr />\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	
	//query the database for parameters
	$particle = new particledata();
	

	# get stack name
	$stackp = $particle->getStackParams($stackId);
	$nump=$particle->getNumStackParticles($stackId);
	$filename = $stackp['path'].'/'.$stackp['name'];

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";
	echo"
					<b>Original Stack Information:</b> <br />
					Name & Path: $filename <br />	
					Stack ID: $stackId<br />
					# Particles: $nump<br />
                     <input type='hidden' name='stackId' value='$stackId'>
					<br />\n";

	echo docpop('runid','<b>Run Name:</b> ');
	echo "<input type='text' name='runid' value='$runid'><br />\n";
	echo "<b>Description:</b><br />\n";
	echo "<textarea name='description' rows='3'cols='70'>$description</textarea>\n";
	echo "<br />\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='5' cellspacing='0' width='100%'><tr><td width='50%' valign='top'>\n";
	echo "<input type='radio' name='subsplit' onclick='subORsplit(\"sub\")' value='sub' $subcheck>\n";
	echo "<b>Select Subset of Particles (1-$nump)</b><br />\n";
	echo docpop('firstp', '<b>First:</b> ');
     	echo "<input type='text' name='firstp' value='$firstp' size='7' $firstpdisable><br />\n";
	echo docpop('lastp', '<b>Last:</b> ');
	echo "<input type='text' name='lastp' value='$lastp' size='7' $lastpdisable> (included)<br />\n";
	echo "</td><td width='50%' valign='top'>\n";
	echo "<input type='radio' name='subsplit' onclick='subORsplit(\"split\")' value='split' $splitcheck>\n";
	echo "<b>Split Stack</b><br />\n";
	echo docpop('split','<b>Split into:</b> ');
	echo "<input type='text' name='split' value='$split' size='3' $splitdisable> sets\n";
	echo "</td></tr></table>\n";
	echo closeRoundBorder();
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br />\n";
	echo "<input type='hidden' name='outdir' value='$outdir' size='38'>\n";
	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo getSubmitForm("Create SubStack");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runSubStack() {
	$expId = $_GET['expId'];

	$runid=$_POST['runid'];
	$stackId=$_POST['stackId'];
	$outdir=$_POST['outdir'];
	$commit=$_POST['commit'];
	$subsplit = $_POST['subsplit'];
	$firstp = $_POST['firstp'];
	$lastp = $_POST['lastp'];
	$split = $_POST['split'];
	
	$command.="subStack.py ";

	//make sure a description is provided
	$description=$_POST['description'];
	if (!$runid) createSubStackForm("<b>ERROR:</b> Specify a runid");
	if (!$description) createSubStackForm("<B>ERROR:</B> Enter a brief description");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$procdir = $outdir.$runid;

	// check sub stack particle numbers
	if ($subsplit == 'sub') {
		if (!$firstp) createSubStackForm("<b>ERROR:</b> Enter a starting particle");
		if (!$lastp) createSubStackForm("<b>ERROR:</b> Enter an end particle");
	}
	elseif (!$split) {
		if (!$firstp) createSubStackForm("<b>ERROR:</b> Enter # of stacks");
	}

	//putting together command
	$command.="-s $stackId ";
	$command.="-n $runid ";
	$command.="-d \"$description\" ";
	if ($firstp!='' && $lastp) $command.="--first=".($firstp-1)." --last=".($lastp-1)." ";
	elseif ($split) $command.="--split=$split ";
	$command.= ($commit=='on') ? "-C " : "--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Create SubStack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createSubStackForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'makestack');
		// if errors:
		if ($sub) createSubStackForm("<b>ERROR:</b> $sub");
		exit();
	}

	processing_header("Creating a SubStack", "Creating a SubStack");

	//rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>centerParticleStack.py command:</b><br />
	$command
	</td></tr>\n";
	echo "<tr><td>run id</td><td>$runid</td></tr>\n";
	echo "<tr><td>stack id</td><td>$stackId</td></tr>\n";
	echo "<tr><td>description</td><td>$description</td></tr>\n";
	echo "<tr><td>outdir</td><td>$procdir</td></tr>\n";
	echo"</table>\n";
	processing_footer();
}

?>
