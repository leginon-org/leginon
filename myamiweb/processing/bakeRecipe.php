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
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['bake']){
	bakeRecipe();
} elseif ($_GET['remove']){
	removeRecipe();
} else {
	checkSelectedRecipe();
}

function bakeRecipe($extra=false, $title='Bake Processing Recipe', $heading='Bake Processing Recipe') {
	$expId = $_GET['expId'];
	$stackid = $_GET['stackid'];
	$alignstackid = $_GET['alignstackid'];
	$name = $_POST['name'];
	$description = $_POST['description'];
	$ctfids = ($_POST['ctfrunids']) ? implode(',',$_POST['ctfrunids']) : '';
	# turn ctfids into list if exist

	$particle = new particledata();
	processing_header($title, $heading, $javascript, False);
	$resultdb = $particle->bakeRecipe($name, $description, $stackid, $alignstackid, $ctfids);
	if ($resultdb == 'exists') echo "<h3>This recipe is already stored in the database</h3>\n";
	elseif ($resultdb == 'ok')  echo "<h3>The recipe was added to the database</h3>\n";
	else echo "<h3>There was an error storing this recipe. Seek the aid of a professional chef</h3>\n";
	processing_footer();
	exit();
}

function checkSelectedRecipe($extra=false, $title='Bake Processing Recipe', $heading='Bake Processing Recipe') {
	$expId = $_GET['expId'];
	$stackid = $_GET['stackid'];
	$alignstackid = $_GET['alignstackid'];
	$formAction = $_SERVER['PHP_SELF']."?expId=$expId&";
	if ($stackid) $formAction .="stackid=$stackid";
	elseif ($alignstackid) $formAction .="alignstackid=$alignstackid";

	// --- Get Session Name --- //
	$sessiondata = getSessionList($projectId,$expId);
	$sessioninfo = $sessiondata['info'];
	$sessionname = $sessioninfo['Name'];

	$particle = new particledata();

	## Get all the existing recipe names (can't have duplicates)
	$recipenames = $particle->getRecipeNames();
	if ($recipenames) $recipenames=implode("','",$recipenames);

	## store jobtype and command in an array
	$storedCommands=array();

	$errors = '';
	# for aligned stack
	if ($alignstackid) {		
		# get jobId for aligned stack
		$astackdata = $particle->getAlignStackParams($alignstackid);
		$job = $particle->getJobFileFromPath($astackdata['path']);
		$jobId = $job[0]['DEF_id'];

		## print aligned stack command, return stackid
		$returnarray = printJobCommand($jobId,array('stackid'));
		$stackid=$returnarray['stackid'];
		$storedCommands['align']=array(
			'name'=>$astackdata['runname'],
			'cmd'=>$returnarray['commandstring']
		);

		## make sure have stack id for aligned stack
		if (!$stackid)
			$errors.= "ERROR: no stack ID associated with aligned stack";
	}

	# must have a stack
	## get jobId for stack
	$stackdata = $particle->getStackParams($stackid);
	$job = $particle->getJobFileFromPath($stackdata['path']);
	$jobId = $job[0]['DEF_id'];

	## print makestack command, return selectionid
	$returnarray = printJobCommand($jobId,array('selectionid'));
	$selectionid = $returnarray['selectionid'];
	$storedCommands['stack']=array(
		'name'=>$stackdata['stackRunName'],
		'cmd'=>$returnarray['commandstring']
	);
	## make sure have selection id for stack
	if (!$selectionid) 
		$errors.= "ERROR: no selection ID associated with aligned stack";
		
	# get jobId for selection run informationa
	$selectrundata = $particle->getSelectionRunData($selectionid);
	$job = $particle->getJobFileFromPath($particle->getPathFromId($selectrundata['REF|ApPathData|path']));
	$jobId = $job[0]['DEF_id'];
	$returnarray = printJobCommand($jobId);
	
	# can't bake a manual picking session
#	if ($returnarray['jobtype']=='manualpicker')
#		$errors.= "ERROR: Cannot bake a recipe with manually picked particles";

	$storedCommands['selection']=array(
		'name'=>$selectrundata['name'],
		'cmd'=>$returnarray['commandstring']
	);

	# for CTF runs (can have multiple)
	$ctfruns = $particle->getCtfRunIds($expId);
	if ($ctfruns) {
		$storedCommands['ctf']=array();
		foreach ($ctfruns as $ctfrun) {
			$job = $particle->getJobFileFromPath($particle->getPathFromId($ctfrun['REF|ApPathData|path']));
			$jobId = $job[0]['DEF_id'];
			$returnarray = printJobCommand($jobId);
			$storedCommands['ctf'][$ctfrun['DEF_id']] = array(
				'name'=>$ctfrun['name'],
				'cmd'=>$returnarray['commandstring']
			);
		}	
	}

	# Javascript to handle errors
	$javascript = "<script LANGUAGE='JavaScript'>\n";
	$javascript.= "function checkForm() {\n";
	$javascript.= "  var rname = document.forms['bakeRecipeForm']['name'].value;\n";
	$javascript.= "  if (rname == null || rname == '') {\n";
	$javascript.= "    alert('Enter a recipe name');\n";
	$javascript.= "    return false\n";
	$javascript.= "  }\n";
	$javascript.= "  namelist = ['$recipenames'];\n";
	$javascript.= "  if (namelist.indexOf(rname) > -1) {\n";
	$javascript.= "    alert('This recipe name is already in use');\n";
	$javascript.= "    return false\n";
	$javascript.= "  }\n";
	$javascript.= "  var desc = document.forms['bakeRecipeForm']['description'].value;\n";
	$javascript.= "  if (desc == null || desc == '') {\n";
	$javascript.= "    alert('Enter a recipe description');\n";
	$javascript.= "    return false\n";
	$javascript.= "  }\n";
	if ($ctfruns) if (count($ctfruns)>1) {
		$javascript.= "  anyChecked = false;\n";
		$javascript.= "  var ctf = document.forms['bakeRecipeForm']['ctfrunids[]'];\n";
		$javascript.= "  for (var i=0; i < ctf.length; i++) {\n";
		$javascript.= "    if (ctf[i].checked) {\n";
		$javascript.= "      anyChecked = true;\n";
		$javascript.= "      break;\n";
		$javascript.= "    }\n";
		$javascript.= "  }\n";
		$javascript.= "  if (!anyChecked) {\n";
		$javascript.= "    alert('Select at least one CTF estimation run');\n";
		$javascript.= "    return false\n";
		$javascript.= "  }\n";
	}
	$javascript.= "}\n";
	$javascript.= "</script>\n";

	processing_header($title, $heading, $javascript, False);
	echo "<form name='bakeRecipeForm' method='POST' action='$formAction' onsubmit='return checkForm()'>\n";

	if ($errors) {
		echo "<h3>$errors</h3>";
		echo "</form>\n";
		processing_footer();
		exit();
	}

	$twidth=600;
	echo "<h2>Commands included in this recipe:</h2>";
	if (array_key_exists('ctf',$storedCommands)) {
		$cmds = $storedCommands['ctf'];
		echo "<table class='tablebubble' width='$twidth'><tr><td>\n";
		echo "<h4>CTF estimation:";
		if (count($cmds) > 1) echo " (select to include in the recipe)";
		echo "</h4>\n";
		$ctftext=array();
		foreach ($cmds as $ctfid => $cmd) {
			if (count($cmds)>1) {
				echo "<input type='checkbox' name='ctfrunids[]' value='$ctfid' checked>";
				echo "<span class='aptitle'>".$cmd['name']."</span><br>\n";
				echo $cmd['cmd'];
				# put <hr> under each ctfrun, except last
				if ($ctfid != key(array_slice($cmds, -1, 1, TRUE)))
					echo "<hr/>\n";
			}
			else {
				echo "<input type='hidden' name='ctfrunids[]' value='$ctfid'>";
				echo "<span class='aptitle'>".$cmd['name']."</span><br>\n";
				echo $cmd['cmd'];
			}
		}
		echo "</td></tr></table>\n";
		echo "<br>\n";
	}
	echo "<table class='tablebubble' width='$twidth'><tr><td>\n";
	echo "<h4>Particle Selection</h4>\n";
	echo "<span class='aptitle'>".$storedCommands['selection']['name']."</span><br>\n";
	echo $storedCommands['selection']['cmd'];
	echo "</td></tr></table>\n";
	echo "<br>\n";

	echo "<table class='tablebubble' width='$twidth'><tr><td>\n";
	echo "<h4>Stack Creation</h4>\n";
	echo "<span class='aptitle'>".$storedCommands['stack']['name']."</span><br>\n";
	echo $storedCommands['stack']['cmd'];
	echo "</td></tr></table>\n";
	echo "<br>\n";
	
	if (array_key_exists('align',$storedCommands)) {
		echo "<table class='tablebubble' width='$twidth'><tr><td>\n";
		echo "<h4>Particle Alignment</h4>\n";
		echo "<span class='aptitle'>".$storedCommands['align']['name']."</span><br>\n";
		echo $storedCommands['align']['cmd'];
		echo "</td></tr></table>\n";
	}

	echo "<hr/>\n";
	echo "<p>\n";
	echo "Recipe Name: <input type='text' name='name' size='15'><br><br>\n";
	echo "Recipe Description: <input type='text' name='description' size='65'>\n";
	echo "<hr/>\n";
	echo "<p><input type='submit' name='bake' value='Bake this recipe'>\n";
	echo "</form>\n";
	processing_footer();
	exit();
}

function removeRecipe() {
	$recipeid = $_GET['remove'];

	$particle = new particledata();

	$title = "Remove Recipe";
	$heading = "Remove Recipe";
	processing_header($title, $heading, $javascript, False);

	$recipeinfo = $particle->getRecipeDataFromId($recipeid, $remove=True);
	echo "Recipe deleted";

	processing_footer();
	exit();
}

function printJobCommand($jobId,$returnParams=False) {
	$particle = new particledata();
	$returnArray = array();
	$returnArray['commandstring'] = "";

	# Get job type from ID
	$jobinfo = $particle->getJobInfoFromId($jobId);
	$returnArray['jobtype'] = $jobinfo['jobtype'];

	## print the job command from the job id, and return specific parameters if needed 
	list($jobname,$params) = getJobCommand($jobId);
	$returnArray['commandstring'] .= $jobname." ";
	foreach ($params as $param) {
		if ($returnParams) {
			foreach ($returnParams as $rpar) {
				if (strtolower($param['name'])=="$rpar") $returnArray[$rpar]=$param['value'];
			}
		}
		$returnArray['commandstring'] .= $param['usage']." ";
	}
	return $returnArray;
}

function getJobCommand($jobId){
	$particle = new particledata();

	$progrunArray = $particle->getProgramRunFromJob($jobId);
	$progrunId = $progrunArray['id'];
	$progparams = $particle->getProgramRunParams($progrunId);
	$params = $particle->getProgramCommands($progrunId);

	$listofparams = array();
	
	return array($progparams['progname'].".py",$params);
}
?>
