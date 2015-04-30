<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Prepare a Frealign Job for submission to a cluster
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['cluster']) {
	$selectedcluster=$_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

if ($_POST['process'])
	prepareFrealign(); // generate command
elseif ($_POST['stackval'] && $_POST['model'])
	jobForm(); // set parameters
else
	stackModelForm(); // select stack and model

/* ******************************************
*********************************************
SELECT STACK AND INITIAL MODEL
*********************************************
****************************************** */

function stackModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	processing_header("FREALIGN Job Generator","FREALIGN Job Generator",$javafunc);

	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}

	$particle = new particledata();

	// get initial models associated with project
	$models = $particle->getModelsFromProject($projectId);

	// find each stack entry in database
	$stackIds = $particle->getStackIds($expId, false, false, true);

	$stackinfo = explode('|--|', $_POST['stackval']);
	$stackid = $stackinfo[0];
	$reconstackinfo = explode('|--|', $_POST['reconstackval']);
	$reconstackid = $reconstackinfo[0];

	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";


	// Begin warning code. See redmine issue number 399 and wikipage.
	#echo "<table cellpadding='10' class='tableborder' border='1'>\n";
	#echo "<tr><td>\n";
	#echo "<h3><font color='#cc3333'> Warning: Handedness of output volume will be flipped! </font></h3>";
	#echo "<p align='center'><a target='_blank' href='http://emg.nysbc.org/redmine/issues/399'>[see more info and workaround here]</a>";
	#echo "</td></tr>\n";
	#echo "</table>\n\n";
	#echo "<br />";

	echo "<table cellpadding='10' class='tableborder' border='1'>\n";
	echo "<tr><td>\n";
	echo "<h3><font color='#cc3333'> Note: Frealign requires a non-ctf corrected stack with black density on white background and the stack must contain the same particles as the stack used for the EMAN reconstruction that initial orientations will be imported from. </font></h3>";
	echo "<p align='center'><a target='_blank' href='http://emg.nysbc.org/redmine/projects/appion/wiki/Frealign_Refinement'>[Refer to the wikipages for more info and workflow]</a>";
	echo "</td></tr>\n";
	echo "</table>\n\n";
	echo "<br />";
	// End warning code
		
	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	echo "<table class='tableborder' border='1'>\n";
	echo "<tr><td>\n";
	echo"<h3>Select stacks:</h3>";
	echo"<h4>Refinement Non CTF-corrected Stacks:</h4>";
	$particle->getStackSelector($stackIds, $stackid, '');

	if (count($stackIds) > 0) {
		echo"<h4>Reconstruction Non CTF-corrected Stacks:</h4>";
		specialStackSelector($stackIds, $reconstackid);
	}
	echo "</td></tr>\n";
	echo "</table>\n\n";

	// show initial models
	echo "<P><B>Initial models:</B><br>"
		."<A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><br>\n";
	echo "<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'><br>\n";

	$minf = explode('|--|',$_POST['model']);
	if (is_array($models) && count($models)>0) {
		echo "<table class='tableborder' border='1'>\n";
		foreach ($models as $model) {
			echo "<tr><td>\n";
			$modelid = $model['DEF_id'];
			$symdata = $particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
			$modelvals = "$model[DEF_id]|--|$model[path]|--|$model[name]|--|$model[boxsize]|--|$symdata[symmetry]";
			echo "<input type='radio' NAME='model' value='$modelvals' ";
			// check if model was selected
			if ($modelid == $minf[0]) echo " CHECKED";
			echo ">\n";
			echo"Use<br/>Model\n";

			echo "</td><td>\n";

			echo modelsummarytable($modelid, true);

			echo "</td></tr>\n";
		}
		echo "</table>\n\n";
		echo "<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'></FORM>\n";
	}
	else echo "No initial models in database";

	echo frealignRef();

	processing_footer();
	exit;
}

/* ******************************************
*********************************************
MAIN FORM TO SET PARAMETERS
*********************************************
****************************************** */

function jobForm($extra=false) {
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	if (!$_POST['model'])
		stackModelForm("ERROR: no initial model selected");
	if (!$_POST['stackval'])
		stackModelForm("ERROR: no stack selected");


	## get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath=getBaseAppionPath($sessiondata).'/recon/';

	if ($leginondata->getCsValueFromSession($expId) === false) {
		stackModelForm("Cs value of the images in this session is not unique or known, can't process");
		exit;
	}
	$particle = new particledata();
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$reconruns = count($particle->getReconIdsFromSession($expId));
	while (glob($outdir.'*recon'.($reconruns+1))) {
		$reconruns += 1;
	}
	$defrunid = 'frealign_recon'.($reconruns+1);

	## find if there are ctffind runs
	$ctffindruns = $particle->getCtfRunIds($expId, $showHidden=False, $ctffind=True);

	## get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$stackid=$stackinfo[0];
	$nump=$particle->getNumStackParticles($stackid);
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
  
	if ($_POST['reconstackval']) {
		$reconstackinfo = explode('|--|',$_POST['reconstackval']);
		$reconstackid=$reconstackinfo[0];
		$reconapix=$reconstackinfo[1];
		$reconbox=$reconstackinfo[2];
		$reconnumpart=$particle->getNumStackParticles($reconstackid);
		if ($reconbox != $box)
			stackModelForm("ERROR: refine stack boxsize ($box) is different from recon stack boxsize ($reconbox)");
		if ($reconapix != $apix)
			stackModelForm("ERROR: refine stack apix ($apix) is different from recon stack apix ($reconapix)");
		if ($reconnumpart != $nump)
			stackModelForm("ERROR: refine stack particle count ($nump) is different from recon stack particle count ($reconnumpart)");
	}
	
	## get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$modelid = $modelinfo[0];
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];

	$syminfo = explode(' ',$modelinfo[4]);
	$modsym = $syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : C_NODES_DEF;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : C_PPN_DEF;
	$rpn = ($_POST['rpn']) ? $_POST['rpn'] : C_RPROCS_DEF;

	// preset information from stackid
	$presetinfo = $particle->getPresetFromStackId($stackid);
	$kv = $presetinfo['hightension']/1e3;

	$javafunc .= writeJavaPopupFunctions('frealign');
	processing_header("Frealign Job Generator","Frealign Job Generator",$javafunc);
	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='frealignjob' method='post' action='$formaction'><br/>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";
	if ($_POST['reconstackval'] && $stackid != $reconstackid)
		echo "<input type='hidden' name='reconstackval' value='".$_POST['reconstackval']."'>\n";

	$sym = ($_POST['sym']) ? $_POST['sym'] : $modsym;

	// if importing reconstruction eulers
	if ($_POST['importrecon'] && $_POST['importrecon']!='None'){
		$_POST['initmethod']='importrecon';
		$_POST['write']='True';
		$importcheck='checked';
	}
	$angcheck = ($_POST['initmethod']=='projmatch' || !$_POST['write']) ? 'checked' : '';
	$inparfilecheck = ($_POST['initmethod']=='inparfile') ? 'checked' : '';

	/* ******************************************
	SCRIPT PARAMETERS
	****************************************** */
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunid;
	$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '10';

	echo "<table class='tableborder' border='1' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td colspan='2' align='center'>\n";
		echo "<h4>Script parameters</h4>\n";
	echo "</td></tr><tr><td>\n";

	echo "</td></tr><tr><td>\n";

		echo docpop('runname','Run Name')." <br/>\n";
		echo " <input type='text' name='runname' value='$runname' size='20'>\n";
		echo "<br/>\n";
		echo docpop('outdir','Output directory')." <br/>\n";
		echo " <input type='text' name='outdir' value='$outdir' size='50'>\n";
		echo "<br/><br/>\n";

	echo "</td></tr>\n";
	echo "</table>\n";

	/* ******************************************
	INITIAL ORIENTATIONS BOX
	****************************************** */

	### Frealign initial search only
	$dang   = $_POST['dang'] ? $_POST['dang'] : '5';
	$initlp = $_POST['initlp'] ? $_POST['initlp'] : '25';

	echo "<br/>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td>\n";
	echo "<h4>Initial Orientations</h4>\n";

	echo "</td></tr><tr><td>\n";

	echo "<input type='radio' name='initmethod' value='importrecon' $importcheck>\n";
	// Neil:: Switching code ; why do want recons from other sessions, we don't have a mathcing stack
	//$recons = $particle->getReconIdsFromSession($expId);
	$recons = $particle->getReconIterIdRelatedToStackid($stackid);
	if (is_array($recons)) {
		echo "<b>Import from EMAN reconstruction:</b>";
		echo "<br/>&nbsp;&nbsp;&nbsp; Reconstr.:\n";
		echo "<select name='importrecon' onchange='frealignjob.submit()'>\n";
		echo "   <option value='None'>Select Reconstruction</option>\n";
	  	foreach ($recons as $r) {
			$ropt = "<option value='".$r['DEF_id']."' ";
			$ropt.= ($_POST['importrecon']==$r['DEF_id']) ? 'selected':'';
			$ropt.= ">";
			$ropt.= $r['name']." (id: ".$r['DEF_id'].") -- ".substr($r['description'],0,60);
			$ropt.= "</option>\n";
			echo $ropt;
		}
	} else {
		echo "<i>no EMAN recons to import Euler angles</i>\n";
	}
	echo "</select>\n";
	echo "<br/>\n";

	// if a reconstruction has been selected, show iterations & resolutions
	if ($_POST['importrecon'] && $_POST['importrecon']!='None') {
		echo "&nbsp;&nbsp;&nbsp; Iteration:\n";
		$iterinfo = $particle->getRefinementData($_POST['importrecon']);
		echo "<select name='importiter'>\n";
		if (is_array($iterinfo)) {
			foreach ($iterinfo as $iter){
			  	$iterstuff = $particle->getIterationInfo($_POST['importrecon'],$iter['iteration']);
				$rmeas = $particle->getRMeasureInfo($iter['REF|ApRMeasureData|rMeasure']);
				$fsc = $particle->getResolutionInfo($iter['REF|ApResolutionData|resolution']);
				$iopt.="<option value='".$iter['DEF_id']."' ";
				$iopt.= ($_POST['importiter']==$iter['DEF_id']) ? 'selected':'';
				$iopt.= ">Iter ".$iter['iteration'];
				$iopt.= ": Ang=".$iterstuff['ang'];
				$iopt.= ", FSC=".sprintf('%.1f',$fsc['half']);
				$iopt.= ", Rmeas=".sprintf('%.1f',$rmeas['rMeasure']);
				$iopt.= "</option>\n";
			}
		}
		echo $iopt;
		echo "</select>\n";
		echo "<br/>\n";
	}
	echo "</td></tr><tr><td>\n";

	echo "<input type='radio' name='initmethod' value='projmatch' $angcheck>\n";
	echo "<b>Determine with Frealign</b>";
	echo "<br/>\n";
	echo docpop('dang',"&nbsp;&nbsp;&nbsp; Angular increment: ");
	echo " <input type='text' name='dang' value='$dang' size='4'>\n";
	echo "&nbsp;&nbsp;&nbsp; Initial LP filter: ";
	echo " <input type='text' name='initlp' value='$initlp' size='4'>\n";

	//echo "</td></tr><tr><td>\n";

	//echo "<input type='radio' name='initmethod' value='inparfile' $inparfilecheck>\n";
	//echo docpop('inpar',"Use input Frealign parameter file:");
	//echo " <input type='text' name='inparfile' value='$inparfile' size='50'>\n";

	echo "</td></tr><tr><td>\n";

	echo " <input type='text' name='numiter' value='$numiter' size='4'>\n";
	echo docpop('numiter','Number of refinement iterations')." <font size='-2'><i></i></font>\n";
	echo "<br/>\n";

	echo "</td></tr>\n";
	echo "</table>\n";
	echo closeRoundBorder();

	echo "<br/>\n";
	echo "<br/>\n";

	/* ******************************************
	CLUSTER PARAMETERS
	****************************************** */
	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : C_NODES_DEF;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : C_PPN_DEF;
	$rpn = ($_POST['rpn']) ? $_POST['rpn'] : C_RPROCS_DEF;

	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>\n";
	echo "<td colspan='4' align='center'>\n";
	echo "<h4>PBS Cluster Parameters</h4>\n";
	echo "</td>\n";
	echo "</tr>\n";
	echo "<tr><td>\n";
		echo docpop('nodes',"Nodes: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='nodes' VALUE='$nodes' SIZE='4' MAXCHAR='4'>";
	echo "</td><td>\n";
		echo docpop('ppn',"Proc/Node: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='ppn' VALUE='$ppn' SIZE='3'>";
	echo "</td><td>\n";
		echo docpop('rpn',"Refines/Node: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='rpn' VALUE='$rpn' SIZE='3'>";
	echo "</td></tr>\n";
	echo "</table>\n";
	echo closeRoundBorder();
	echo "<br/>\n";
	echo "<br/>\n";

	/* ******************************************
	FREALIGN PARAMETERS
	****************************************** */

	//$magrefine=($_POST[$magrefinen]=='on') ? 'CHECKED' : '';
	//$defocusrefine=($_POST[$defocusrefinen]=='on') ? 'CHECKED' : '';
	//$astigrefine=($_POST[$astigrefinen]=='on') ? 'CHECKED' : '';

	###set default values that iterate
	$mask  = $_POST["mask"] ? $_POST["mask"] : round($apix*$box/3.0);
	$imask = $_POST["imask"] ? $_POST["imask"] : 0;
	$wgh   = $_POST["wgh"] ? $_POST["wgh"] : 0.07;
	$xstd  = $_POST["xstd"] ? $_POST["xstd"] : 0;
	$pbc   = $_POST["pbc"] ? $_POST["pbc"] : 100;
	$boff  = $_POST["boff"] ? $_POST["boff"] : 70;
	$itmax = $_POST["itmax"] ? $_POST["itmax"] : 10;
	$ipmax = $_POST["ipmax"] ? $_POST["ipmax"] : 0;

	$target = $_POST["target"] ? $_POST["target"] : 15;
	$thresh = $_POST["thresh"] ? $_POST["thresh"] : 85;

	$rrec = $_POST["rrec"] ? $_POST["rrec"] : (ceil($apix*20))/10;
	$hp = $_POST["hp"] ? $_POST["hp"] : 50;
	$lp = $_POST["lp"] ? $_POST["lp"] : (ceil($apix*40))/10;
	$rbfact = $_POST["rbfact"] ? $_POST["rbfact"] : 0;
	$ctffindcheck = ($_POST['ctffindonly']=='on') ? 'checked':'';

	echo "<table class='tableborder' border='1' cellpadding='4' cellspacing='4'>\n";
	echo "<tr><td colspan='2' align='center'>\n";
		echo "<h4>Frealign parameters</h4>\n";
	echo "</td></tr>";

	echo "<tr><td>\n";
		echo "<h4>Card #2</h4>\n";
	echo "</td><td>\n";
		echo "<h4>Card #5</h4>\n";
	echo "</td></tr>";

	echo "<tr><td rowspan='5'>\n";
		echo " <input type='text' name='mask' value='$mask' size='4'>\n";
		echo docpop('mask','Particle outer mask radius (RO)')
			." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='imask' value='$imask' size='4'>\n";
		echo docpop('imask','Particle inner mask radius (RI)')
			." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";

		echo "<br/><br/>\n";

		echo " <input type='text' name='wgh' value='$wgh' size='4'>\n";
		echo docpop('wgh','Amplitude contrast (WGH)')." \n";
		echo "<br/>\n";
		echo " <input type='text' name='xstd' value='$xstd' size='4'>\n";
		echo docpop('xstd','Standard deviation filtering (XSTD)')
			." <font size='-2'><i>(0 = no filtering)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='pbc' value='$pbc' size='4'>\n";
		echo docpop('pbc','Phase B-factor weighting constant (PBC)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='boff' value='$boff' size='4'>\n";
		echo docpop('boff','B-factor offset (BOFF)')." <font size='-2'></font>\n";

		echo "<br/><br/>\n";

		echo " <input type='text' name='itmax' value='$itmax' size='4'>\n";
		echo docpop('itmax','Number of randomized search trials (ITMAX)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='ipmax' value='$ipmax' size='4'>\n";
		echo docpop('ipmax','Number of potential matches to refine (IPMAX)')." <font size='-2'></font>\n";

	echo "</td><td>\n";

		echo " <input type='text' name='sym' value='$sym' size='4'>\n";
		echo docpop('sym','Symmetry (ASYM)')." <font size='-2'></font>\n";

	echo "</td></tr><tr><td>\n";
		echo "<h4>Card #6</h4>\n";
	echo "</td></tr><tr><td>\n";

		echo " <input type='text' name='target' value='$target' size='4'>\n";
		echo docpop('target','Target phase residual (TARGET)')." <font size='-2'></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='thresh' value='$thresh' size='4'>\n";
		echo docpop('thresh','Worst phase residual for inclusion (THRESH)')." <font size='-2'></font>\n";

	echo "</td></tr><tr><td>\n";
		echo "<h4>Card #7</h4>\n";
	echo "</td></tr><tr><td>\n";

		echo " <input type='text' name='rrec' value='$rrec' size='4'>\n";
		echo docpop('rrec','Resolution limit of reconstruction (RREC)')
			." <font size='-2'><i>(in &Aring;ngstroms; default Nyquist)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='hp' value='$hp' size='4'>\n";
		echo docpop('hp','Lower resolution limit or high-pass filter (RMAX1)')
			." <font size='-2'><i>(in &Aring;ngstroms)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='lp' value='$lp' size='4'>\n";
		echo docpop('lp','Higher resolution limit or low-pass filter (RMAX2)')
			." <font size='-2'><i>(in &Aring;ngstroms; default 2*Nyquist)</i></font>\n";
		echo "<br/>\n";
		echo " <input type='text' name='rbfact' value='$rbfact' size='4'>\n";
		echo docpop('rbfact','B-factor correction (RBFACT)')." <font size='-2'><i>(0 = off)</i></font>\n";

		echo "</td></tr><tr><td colspan='3' align='center'>\n";

		// give option of only using ctffind runs
		if ($ctffindruns) {
			echo "<input type='checkbox' name='ctffindonly' $ctffindcheck>";
			echo docpop('ctffindonly','Only use CTFFIND values');
			echo "&nbsp;&nbsp;&nbsp;&nbsp;\n";
		}
		echo " <input type='text' name='last' value='$last' size='4'>\n";
		echo docpop('last','Last particle to use')." \n";

	// SUBMIT BUTTON
	echo "</td></tr><tr><td colspan='3' align='center'>\n";
		echo "<br/>\n";
		echo getSubmitForm("Prepare Frealign");
	echo "</td></tr>\n";
	echo "</table>\n";

	echo "<input type='hidden' NAME='kv' value='$kv'>";
	echo "<input type='hidden' NAME='apix' value='$apix'>";

	echo "</form>\n";
	echo "<br/><br/><hr/>\n";
	//echo "StackID: $stackid -- ModelID: $modelid<br/>\n";
	echo "<table class='tablebubble'><tr><td>\n";
	echo stacksummarytable($stackid, true);
	if ($_POST['reconstackval'] && $stackid != $reconstackid) {
		echo "</td></tr><tr><td>\n";
		echo stacksummarytable($reconstackid, true);
	}
	echo "</td></tr><tr><td>\n";
	echo modelsummarytable($modelid, true);
	echo "</td></tr></table>\n";

	echo frealignRef();

	processing_footer();
	exit;
}

/* ******************************************
*********************************************
GENERATE COMMAND
*********************************************
****************************************** */

function prepareFrealign ($extra=False) {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$nodes = $_POST['nodes'];
	$ppn = $_POST['ppn'];
	$rpn = $_POST['rpn'];

	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackid=$stackinfo[0];

	if ($_POST['reconstackval']) {
		$reconstackinfo=explode('|--|',$_POST['reconstackval']);
		$reconstackid=$reconstackinfo[0];
	}

	// get the model id
	$modelinfo=explode('|--|',$_POST['model']);
	$modelid=$modelinfo[0];
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];

	$last=$_POST['last'];
	$kv=$_POST['kv'];
	$mask=$_POST["mask"];
	$imask=$_POST["imask"];
	$wgh=$_POST["wgh"];
	$xstd=$_POST["xstd"];
	$pbc=$_POST["pbc"];
	$boff=$_POST["boff"];
	$dang = ($_POST['initmethod']=='projmatch') ? $_POST["ang"] : '';
	$itmax=$_POST["itmax"];
	$ipmax=$_POST["ipmax"];
	$sym=$_POST["sym"];
	$target=$_POST["target"];
	$thresh=$_POST["thresh"];
	$rrec=$_POST['rrec'];
	$hp=$_POST["hp"];
	$lp=$_POST["lp"];
	$rbfact=$_POST["rbfact"];
	$numiter=$_POST['numiter'];
	$inpar=$_POST['inparfile'];
	$importiter=$_POST['importiter'];
	$ctffindonly=($_POST['ctffindonly']=='on') ? True:'';

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if ($_POST['ppn'] > C_PPN_MAX )
		jobForm("ERROR: Max processors per node is ".C_PPN_MAX);
	if ($_POST['nodes'] > C_NODES_MAX )
		jobForm("ERROR: Max nodes on ".C_NAME." is ".C_NODES_MAX);

	if ($_POST['initmethod']=='projmatch' && !$_POST['dang'])
		jobForm("<b>ERROR:</b> Enter an angular increment");
	if (!$_POST['mask'])
		jobForm("<b>ERROR:</b> Enter an outer mask radius");

	/* *******************
	PART 3: Create program command
	******************** */
	$command = "prepFrealign.py ";
	$command.= "--stackid=$stackid ";
	if ($reconstackid)
		$command.= "--reconstackid=$reconstackid ";
	$command.= "--modelid=$modelid ";
	if ($importiter) $command.= "--reconiterid=$importiter ";
	if ($dang) $command.= "--dang=$dang ";

	$command.= "--mask=$mask ";
	$command.= "--imask=$imask ";
	$command.= "--wgh=$wgh ";
	$command.= "--xstd=$xstd ";
	$command.= "--pbc=$pbc ";
	$command.= "--boff=$boff ";
	$command.= "--itmax=$itmax ";
	$command.= "--ipmax=$ipmax ";
	$command.= "--sym=$sym ";
	$command.= "--target=$target ";
	$command.= "--thresh=$thresh ";
	$command.= "--rrec=$rrec --hp=$hp --lp=$lp --rbfact=$rbfact ";
	$command.= "--numiter=$numiter ";
	#enforce cluster mode, for now
	$command.= "--cluster ";
	$command.= "--ppn=$ppn ";
	$command.= "--rpn=$rpn ";
	$command.= "--nodes=$nodes ";
	if ($ctffindonly) $command.= "--ctfmethod=ctffind ";
	if ($last) $command.= "--last=$last ";


	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= frealignRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'prepfrealign', $nproc);
	// if error display them
	if ($errors)
		jobForm($errors);
	exit;
};

function specialStackSelector($stackIds, $stackidval) {
	# $stackinfo[0] = stackid
	# $stackinfo[1] = pixel size in angstrums / pixels
	# $stackinfo[2] = stack boxsize (length in either direction) in pixels
	# $stackinfo[3] = number of particles in the stack
	# $stackinfo[4] = appion stackfile path
	# $stackinfo[5] = Imagic stack header file name, including extension but not path
	# $stackinfo[6] = Imagic stack data file name, including extension but not path
	# examples: 
	# $stackinfo[4] = '/your_disk/appion/09aug267/stacks/stack1'
	# $stackinfo[5] = 'start.hed'
	# $stackinfo[6] = 'start.img'
	echo "<SELECT NAME='reconstackval' >\n";
	echo "<OPTION VALUE='' style='color:green;' >Same as refinement</option>\n";
	$particle = new particledata();
	foreach ($stackIds as $stackid){
		// get stack parameters from database
		$s=$particle->getStackParams($stackid['stackid']);
		// get number of particles in each stack
		$totalp=$particle->getNumStackParticles($stackid['stackid']);
		$nump=commafy($totalp);
		// get pixel size of stack
		$apix=($particle->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
		// truncated pixel size
		$showapix=sprintf("%.2f",$apix);
		// get box size
		$box = $s['boxsize'];
		// get stack path with name
		$opvals = "$stackid[stackid]|--|$apix|--|$box|--|$totalp|--|$s[path]|--|$s[name]";
		// if imagic stack, send both hed & img files for dmf
		if (preg_match('%\.hed%', $s['name'])) $opvals.='|--|'.preg_replace('%hed%','img',$s['name']);
		if (preg_match('%\.img%', $s['name'])) $opvals.='|--|'.preg_replace('%img%','hed',$s['name']);
	
		echo "<OPTION VALUE='$opvals'";
		// select previously set stack on resubmita
		if ($stackid['stackid']==$stackidval) echo " SELECTED";
		echo">$s[shownstackname] ID: $stackid[stackid] ($nump particles, $showapix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
	}
	echo "</SELECT>\n";
	return $apix;
};
?>


