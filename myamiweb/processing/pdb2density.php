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

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runDownloadModel();
}

// Create the form page
else {
	createForm();
}

function createForm($extra=false, $title='PDB to EM', $heading='PDB to EM Density') {
	// check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  
	$javafunctions = writeJavaPopupFunctions('appion');
	$particle = new particledata();

	processing_header($title,$heading,$javafunctions,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$outdir=getBaseAppionPath($sessioninfo).'/models';
		$outdir=$outdir."/pdb";
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
  
	// Set any existing parameters in form
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '';
	$symm = ($_POST['symm']) ? $_POST['symm'] : '';
	$runtime = ($_POST['runtime']) ? $_POST['runtime'] : getTimestring();
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$pdbid = ($_POST['pdbid']) ? $_POST['pdbid'] : '';
	$box = ($_POST['box']) ? $_POST['box'] : '';
	$bunitcheck = ($_POST['bunit'] == 'on') ? 'checked' : '';

	echo "<table class=tablebubble cellspacing='8'>";

	echo "<tr><td valign='top'>\n";

	echo docpop('pdbid', '<b>PDB ID:</b>');
	echo "<input type='text' name='pdbid' value='$pdbid' size='5'><br />\n";
	echo "<input type='hidden' name='runtime' value='$runtime'>\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top'>\n";

	echo "<input type='checkbox' name='bunit' $bunitcheck>\n";
	echo "Use the ";
	echo docpop('biolunit', "biological unit");

	echo "</td></tr>\n";
	echo "<tr><td valign='top'>\n";

	echo docpop('outdir', 'Output directory')."<br/>\n";
	echo "<input type='text' name='outdir' value='$outdir' size='40'>\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	echo "<input type='text' name='lowpass' value='$lowpass' size='5'>\n";
	echo "&nbsp;Low pass filter\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	$syms = $particle->getSymmetries();
   echo "<select name='symm'>\n";
   echo "<option value=''>select one...</option>\n";
	foreach ($syms as $sym) {
		echo "<option value='$sym[DEF_id]'";
		if ($sym['DEF_id']==$_POST['symm'])
			echo " selected";
		echo ">$sym[symmetry]";
		if ($sym['symmetry']=='C1')
			echo " (no symmetry)";
		echo "</option>\n";
	}
	echo "</select>\n";
	echo "&nbsp;Symmetry group <i>e.g.</i> c1\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

   echo "<select name='method'>\n";
	   echo "<option value='eman'";
		if ($_POST['method']=='eman')
			echo " selected";
	   echo ">EMAN: pdb2mrc</option>\n";

	   echo "<option value='spider'";
		if ($_POST['method']=='spider')
			echo " selected";
	   echo ">SPIDER: CP FROM PDB</option>\n";
	echo "</select>\n";
	echo "&nbsp;Program to convert PDB\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	echo docpop('apix', 'Pixel size')."<br/>\n";
	echo "<input type='text' name='apix' value='$apix' size='5'>\n";
	echo "&nbsp;<font size='-2'>(in &Aring;ngstroms)</font>\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	echo docpop('boxsize', 'Box size')."<br/>\n";
	echo "<input type='text' name='box' value='$box' size='5'>\n";
	echo "&nbsp;<font size='-2'>(default provided)</font>\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	echo "<input type='checkbox' name='viper2eman' $viper2eman>\n";
	echo docpop('viper2eman', "convert VIPER to EMAN orientation");

	echo "</td></tr>\n";
	echo "<tr><td align='center'>\n";

	echo "<hr>";
	echo getSubmitForm("Create Model");

	echo "</td></tr>\n";
	echo "</table>\n";
	echo "</form>\n";

	echo initModelRef();

	processing_footer();
	exit;
}

function runDownloadModel() {
	/* *******************
	PART 1: Get variables
	******************** */
	$session=$_POST['sessionname'];
	$box=$_POST['box'];
	$method=$_POST['method'];
	$pdbid=$_POST['pdbid'];
	$apix=$_POST['apix'];
	$symm=$_POST['symm'];
	$lowpass=$_POST['lowpass'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a pdb id was entered
  	if (!$pdbid)
		createForm("<B>ERROR:</B> Enter a PDB ID");
	//make sure a apix was provided
	if (!$apix)
		createForm("<B>ERROR:</B> Enter the pixel size");
	//make sure a symmetry group was provided
	if (!$symm)
		createForm("<B>ERROR:</B> Enter a symmetry group");
	//make sure a resolution was provided
	if (!$lowpass)
		createForm("<B>ERROR:</B> Enter the low pass filter radius");
	// check if downloading the biological unit
	if (!is_float($lowpass))
		$lowpass = $lowpass.".0";

	// pdb id will be the runname
	$runtime = $_POST['runtime'];
	$filename = "pdb".$pdbid."-".$runtime;
	$_POST['runname'] = $filename;

	/* *******************
	PART 3: Create program command
	******************** */
	$command = "modelFromPDB.py ";
	$command.="--pdbid=$pdbid ";
	$command.="--session=$session ";
	$command.="--apix=$apix ";
	$command.="--res=$lowpass ";
	$command.="--symm=$symm ";
	if ($box)
		$command.="--box=$box ";
	if ($_POST['bunit']=='on')
		$command.="--biolunit " ;
	if ($_POST['viper2eman']=='on')
		$command.="--viper2eman " ;
	$command.="--method=$method " ;

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= initModelRef(); // main init model ref

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadmodel', $nproc);
	// if error display them
	if ($errors)
		createForm($errors);
	exit;
}
?>
