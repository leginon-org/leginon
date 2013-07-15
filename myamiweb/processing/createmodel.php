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
	runCreateModel();
}

// IF METHOD IS SELECTED
elseif ($_POST['selectmethod']) {
	createSelectParameterForm();
}

// Create the form page
else {
	createEMANInitialModelForm();
}


#######################################################################################
#######################################################################################
#######################################################################################


function createEMANInitialModelForm($extra=false, $title='createModel.py Launcher', $heading='EMAN Common Lines') {
   // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$clusterid=$_GET['clusterid'];
	$exclude=$_GET['exclude'];
	$include=$_GET['include'];

	// Set any existing parameters in form
	if (!$description) $description = $_POST['description'];
	if (!$clusterid) $clusterid = $_POST['clusterid'];
	if (!strlen($exclude)) $exclude = $_POST['exclude'];
	if (!strlen($include)) $include = $_POST['include'];
	$commit = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	$methodcheck = ($_POST['method']) ? $_POST['method']: 'any';

	$javafunctions = writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"<form name='viewerform' method='post' action='$formAction'>\n";

	//query the database for parameters
	$particle = new particledata();

	echo "<table class='tablebubble'>";
	echo "<tr><td>\n";
	if ($clusterid!="") {
		echo "<b>Clustering Information:</b> <br />";
		echo "Cluster ID: $clusterid<br />";
		echo "<input type='hidden' name='clusterid' value='$clusterid'>";
		echo "<br />\n";
	} else {
		//Case 2: Drop Down Menus

		$clusterids = $particle->getClusteringStacks($expId, $projectId);
		if ($clusterids) {
			echo "<SELECT name='clusterid'>\n";
			foreach ($clusterids as $clusteriddata){
				$clusterid = $clusteriddata['clusterid'];
				$clusterdata = $particle->getClusteringStackParams($clusterid);
				$runname  = $clusterdata['name'];
				$numclass = $clusterdata['num_classes'];
				$descript = substr($clusterdata['description'],0,40);
				echo "<OPTION value='$clusterid'";
				if ($clusterid == $_POST['clusterid']) echo " SELECTED";
				echo">Cluster $clusterid: $runname ($numclass classes) $descript...</OPTION>\n";
			}
			echo "</SELECT>\n<br/>\n<br/>\n";
		} else {
			echo "<font color='red' size='+2'>No Clustering Stacks Found</font>\n<hr />\n";
		}
	}

	echo "<table border='0'><tr><td>\n";
	echo docpop('commonlineemanprog','<b>Symmetry group:</b> ');
	echo "</td><td>\n";
	echo "<input type='radio' name='method' value='any'";
	if ($methodcheck == 'any')  echo " CHECKED";
	echo "> Asymmetric\n";

	echo "</td><td>\n";
	echo "<input type='radio' name='method' value='csym'";
	if ($methodcheck == 'csym') echo " CHECKED";
	echo "> C symmetry\n";

	echo "</td><td>\n";
	echo "<input type='radio' name='method' value='icos'";
	if ($methodcheck == 'icos') echo " CHECKED";
	echo "> Icosahedral\n";

	echo "</td><td>\n";
	echo "<input type='radio' name='method' value='oct'";
	if ($methodcheck == 'oct')  echo " CHECKED";
	echo "> Octahedral\n";

	echo "</td></tr>\n";

	echo "<tr><td>\n";
	echo "EMAN manuals: \n";
	echo "</td><td align='center'>\n";
	echo "<a href='http://blake.bcm.tmc.edu/emanwiki/StartAny'>"
		."startAny</a>&nbsp;<img src='img/external.png'>\n";
	echo "</td><td align='center'>\n";
	echo "<a href='http://blake.bcm.tmc.edu/emanwiki/StartCSym'>"
		."startcsym</a>&nbsp;<img src='img/external.png'>\n";
	echo "</td><td align='center'>\n";
	echo "<a href='http://blake.bcm.tmc.edu/emanwiki/StartIcos'>"
		."starticos</a>&nbsp;<img src='img/external.png'>\n";
	echo "</td><td align='center'>\n";
	echo "<a href='http://blake.bcm.tmc.edu/emanwiki/StartOct'>"
		."startoct</a>&nbsp;<img src='img/external.png'>\n";
	echo "</td></tr></table>\n";

	echo "<br/><br/>\n";

	// Include / Exclude
	if ($exclude!="") {
		echo docpop('excludeClass','<b>Excluded Classes:</b> ');
		echo "<font size='+1'><i>$exclude</i></font>\n";
		echo "<input type='hidden' name='exclude' value='$exclude'>\n";
	} elseif ($include!="") {
		echo docpop('includeClass','<b>Included Classes:</b> ');
		echo "<font size='+1'><i>$include</i></font>\n";
		echo "<input type='hidden' name='include' value='$include'>\n";
	} else {
		echo docpop('includeClass','<b>Included Classes:</b> ');
		echo "<input type='text' name='include' value='$include' size='30'>\n";
		echo "<br/>\n";
		echo docpop('excludeClass','<b>Excluded Classes:</b> ');
		echo "<input type='text' name='exclude' value='$exclude' size='30'>\n";
	}
	echo "<br/><br/>\n";



	echo "</td></tr><tr><td align='center'>\n";
	echo "<hr/>\n";
	echo"<p><input type='submit' name='selectmethod' value='Continue to next step >>>'>";

	echo "</td></tr></table></form>\n";

	echo emanRef();

	processing_footer();
	exit;
}

#######################################################################################
#######################################################################################
#######################################################################################


function createSelectParameterForm($extra=false, $title='createModel.py Launcher', $heading='EMAN Common Lines'){

	// get from previous from
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	// from previous form
	$clusterid = $_POST['clusterid'];
	$exclude   = $_POST['exclude'];
	$include   = $_POST['include'];
	$method    = $_POST['method'];

	// new to this form
	$rounds = $_POST['rounds'] ? $_POST['rounds'] : 3;
	$commit = $_POST['commit']=='off' ? '' : ' CHECKED';
	$descript = $_POST['descript'] ? $_POST['descript'] : '';
	$mask = $_POST['mask'] ? $_POST['mask'] : '';
	$imask = $_POST['imask'] ? $_POST['imask'] : '';

	if (!$clusterid)
		createEMANInitialModelForm("<B>ERROR:</B> No Cluster ID was selected");

	$javafunctions = writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);

	$particle = new particledata();
	$syms = $particle->getSymmetries();
	$clusterdata = $particle->getClusteringStackParams($clusterid);

	// set defaults
	$defoutdir = dirname(dirname($clusterdata['path']))."/models";
	$outdir = $_POST['outdir'] ? $_POST['outdir'] : $defoutdir;
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$models = $particle->getModelsFromProject($projectId, True);
	if ($models)
		$nummodels = count($models);
	else
		$nummodels = 0;
	while (file_exists($outdir.'/emanmodel'.($nummodels+1)))
		$nummodels += 1;
	$defrunname = 'emanmodel'.($nummodels+1);
	$runname = $_POST['runname'] ? $_POST['runname'] : $defrunname;

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo"<form name='viewerform' method='post' action='$formAction'>\n";

	echo"<table class='tablebubble'><tr><td>\n";

	echo "<input type='hidden' name='method' value='$method'>";
	if( $_POST['method'] == 'csym') {
		echo " <B>EMAN Program: StartCSym for Volumes with Rotational Symmetry</B><br><br>";
	} elseif ( $_POST['method'] == 'icos') {
		echo " <B>EMAN Program: StartIcos for Volumes with Icosahedral Symmetry</B><br><br>";
	} elseif ( $_POST['method'] == 'oct') {
		echo " <B>EMAN Program: StartOct for Volumes with Octahedral Symmetry</B><br><br>";
	} elseif ( $_POST['method'] == 'any') {
		echo " <B>EMAN Program: StartAny for Asymmetric Volumes</B><br><br>";
	}

	echo "<b>Cluster ID:</b> <font size='+1'><i>$clusterid</i></font>\n";
	echo "<input type='hidden' name='clusterid' value='$clusterid'>";
	echo "<br/><br/>\n";

	// Include / Exclude
	if ($exclude!="") {
		echo docpop('excludeClass','<b>Excluded Classes:</b> ');
		echo "<font size='+1'><i>$exclude</i></font>\n";
		echo "<input type='hidden' name='exclude' value='$exclude'>\n";
	} elseif ($include!="") {
		echo docpop('includeClass','<b>Included Classes:</b> ');
		echo "<font size='+1'><i>$include</i></font>\n";
		echo "<input type='hidden' name='include' value='$include'>\n";
	}
	echo "<br/><br/>\n";

	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' value='$runname' size='10'>\n";
	echo "<br/><br/>\n";

	echo docpop('outdir','<b>Output Directory:</b> ');
	echo "<input type='text' name='outdir' value='$outdir' size='34'>\n";
	echo "<br/><br/>\n";

	echo "<b>Description:</b><br />\n";
	echo "<textarea name='descript' rows='3'cols='70'>$descript</textarea>\n";
	echo "<br/><br/>\n";

	echo "<input type='checkbox' name='commit' $commit>\n";
	echo docpop('commit','<b>Commit model to database');
	echo "<br/><br/>\n";

	echo "<tr><td valign='top' class='tablebg'>\n";
	echo "<table width='450' border='0'>\n";
	#Options to display for each EMAN method
	if($_POST['method'] == 'csym') {
		/* **************************
			C Symmetry
		************************** */
		// Select symmetry
		echo "<tr><td>";
		echo docpop('csym','<b>Model symmetry:</b>');
		echo "</td>\n";
		echo "<td><select name='symmetryid'>\n";
		foreach ($syms as $sym) {
			$symid = $sym['DEF_id'];
			if (strtoupper($sym['eman_name'][0]) == 'C') {
				if ($sym['symmetry']!='C1') {
					echo "<option value='$symid'";
					if ($symid == $_POST['symmetryid'])
						echo " SELECTED";
					echo ">".$sym['symmetry'];
					echo "</option>\n";
				}
			}
		}
    	echo" </select>";
		echo "</td></tr>";

		// Select part number
		echo "<tr><td>";
		echo docpop('partnum','<b>Num clusters per view:</b> ');
		echo "</td><td>\n";
		echo "<input type='text' name='partnum' value='$partnum' size='5'>";
		echo "</td></tr>";

		// Select internal mask
		echo "<tr><td>";
		echo docpop('imask','<b>Internal mask:</b>');
		echo "<font size='-2'><i>(optional)</i></font>\n";
		echo "</td><td>\n";
		echo "<input type='text' name='imask' value='$imask' size='5'>\n";
		echo "<font size='-2'><i>&nbsp;(in pixels)</i></font>\n";
		echo "</td></tr>";

	} elseif ( $_POST['method'] == 'icos') {
		/* **************************
			Icosahedral
		************************** */
		// Select symmetry
		echo "<tr><td>Model symmetry:</td>\n";
		echo "<td>\n";
		foreach ($syms as $sym) {
			$symid = $sym['DEF_id'];
			if (strtoupper(substr($sym['eman_name'],0,4)) == 'ICOS') {
				echo "<input type='hidden' name='symmetryid' value='$symid'>";
				echo $sym['symmetry'].":&nbsp;<i>".$sym['description']."</i>\n";
				break;
			}
		}
		echo "</td></tr>";

		// Select part number
		echo "<tr><td>";
		echo docpop('partnum','<b>Num clusters per view:</b> ');
		echo "</td><td>\n";
		echo "<input type='text' name='partnum' value='$partnum' size='5'>";
		echo "</td></tr>";

		// Select internal mask
		echo "<tr><td>";
		echo docpop('imask','<b>Internal mask:</b>');
		echo "<font size='-2'><i>(optional)</i></font>\n";
		echo "</td><td>\n";
		echo "<input type='text' name='imask' value='$imask' size='5'>\n";
		echo "<font size='-2'><i>&nbsp;(in pixels)</i></font>\n";
		echo "</td></tr>";

	} elseif ( $_POST['method'] == 'oct') {
		/* **************************
			Octahedral
		************************** */
		// Select symmetry
		echo "<tr><td>Model symmetry:</td>\n";
		echo "<td>\n";
		foreach ($syms as $sym) {
			$symid = $sym['DEF_id'];
			if (strtoupper(substr($sym['eman_name'],0,3)) == 'OCT') {
				echo "<input type='hidden' name='symmetryid' value='$symid'>";
				echo $sym['symmetry'].":&nbsp;<i>".$sym['description']."</i>\n";
				break;
			}
		}
		echo "</td></tr>";

		// Select part number
		echo "<tr><td>";
		echo docpop('partnum','<b>Num clusters per view:</b> ');
		echo "</td><td>\n";
		echo "<input type='text' name='partnum' value='$partnum' size='5'>";
		echo "</td></tr>";

	} elseif ( $_POST['method'] == 'any') {
		/* **************************
			No Symmetry
		************************** */
		// Select symmetry
		echo "<tr><td>Model symmetry:</td>\n";
		echo "<td>\n";
		foreach ($syms as $sym) {
			$symid = $sym['DEF_id'];
			if (strtoupper(substr($sym['eman_name'],0,2)) == 'C1') {
				echo "<input type='hidden' name='symmetryid' value='$symid'>";
				echo $sym['symmetry'].":&nbsp;<i>".$sym['description']."</i>\n";
				break;
			}
		}
		echo "</td></tr>";

		// Select external mask
		echo "<tr><td>";
		echo docpop('mask','<b>Mask:</b>');
		echo "<font size='-2'><i>(optional)</i></font>\n";
		echo "</td><td>\n";
		echo "<input type='text' name='mask' value='$mask' size='5'>\n";
		echo "<font size='-2'><i>&nbsp;(in pixels)</i></font>\n";
		echo "</td></tr>";

		echo "<tr><td>";
		echo docpop('rounds','<b>Rounds:</b> ');
		echo "</td><td>\n";
		echo "<input type='text' name='rounds' value='$rounds' size='5'>";
		echo "<font size='-2'><i>(between 2 and 5)</i></font><br/>";
		echo "</td></tr>";
	}
	echo "</table>\n";
	echo "</td></tr>\n";
	echo "<tr><td align='center'>";
	echo "<hr/><br/>\n";
	echo getSubmitForm("Create Model");
	echo "</td></tr></table></form>\n";

	echo emanRef();

}


#######################################################################################
#######################################################################################
#######################################################################################

function runCreateModel() {
	/* *******************
	PART 1: Get variables
	******************** */
	$clusterid  = $_POST['clusterid'];
	$commit     = $_POST['commit'];
	$exclude    = $_POST['exclude'];
	$include    = $_POST['include'];
	$method     = $_POST['method'];
	$symmetryid = $_POST['symmetryid'];
	$descript   = $_POST['descript'];
	if ($method == 'csym') {
		$partnum=$_POST['partnum'];
		$imask=$_POST['imask'];
	} elseif ($method == 'icos') {
		$partnum=$_POST['partnum'];
		$imask=$_POST['imask'];
	} elseif ($method == 'oct') {
		$partnum=$_POST['partnum'];
	} elseif ($method == 'any') {
		$mask=$_POST['mask'];
		$rounds=$_POST['rounds'];
	}
//	$_POST['runname'] = getTimestring();

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a description is provided
	if (!$descript)
		createSelectParameterForm("<B>ERROR:</B> Enter a brief description");
	if (!$symmetryid)
		createSelectParameterForm("<B>ERROR:</B> Symmetry ID was not selected");


	/* *******************
	PART 3: Create program command
	******************** */
	$command ="createModel.py ";
	$command.="--method=$method ";
	$command.="--cluster-id=$clusterid ";
	$command.="--symm=$symmetryid ";
	if ($exclude != "") {
		$exclude=preg_replace("% %","",$exclude);
		$command.="--exclude=$exclude ";
	} elseif ($include != "") {
		$include=preg_replace("% %","",$include);
		$command.="--include=$include ";
	}
	if ($partnum) $command.="--numkeep=$partnum ";
	if ($mask) $command.="--mask=$mask ";
	if ($imask) $command.="--imask=$imask ";
	if ($rounds) $command.="--rounds=$rounds ";
	$command.="--description=\"$descript\" ";
	$command.= ($commit=='on') ? "--commit " : "--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= emanRef(); // main eman ref

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'createModel', $nproc);
	// if error display them
	if ($errors)
		createSelectParameterForm($errors);
	exit;
}

?>
