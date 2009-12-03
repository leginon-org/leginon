<?php

/* 


script for setting up a batch refinement in IMAGIC using an initial model and a stack as input


*/

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/summarytables.inc";



$numiters = ($_POST['numiters']) ? $_POST['numiters'] : 1;
	
// if processing, write job file & process, checking for any errors in user input
if ($_POST['process'])  {
	if (!$_POST['output_directory']) jobform("error: no output directory specified");	
	if (!$_POST['runid']) jobform("error: no run ID specified");

	for ($i=1; $i<=$numiters; $i++) {	
		// check for errors in user input values
		if (!$_POST['symmetry'.$i]) jobform("error: no symmetry specified");
		if (!$_POST['mask_val'.$i]) jobform("error: no particle mask radius specified (pixels)");
		if ($_POST['autofiltstack']) {
			if (!$_POST['auto_lp_filt_base']) jobform("error: please specify a baseline value for lp-filtering stack");
			if (!$_POST['auto_lp_filt_fraction']) jobform("error: please specify a dropoff fraction for low-pass filtering value");
		}
		if (!$_POST['mrarefs_ang_inc'.$i]) jobform("error: angular increment of forward projections for mra references not specified");
		if (!$_POST['max_shift_orig'.$i]) jobform("error: no max shift specified as compared to originals (MRA)");
		if (!$_POST['max_shift_this'.$i]) jobform("error: no max shift specified for this iteration (MRA)");
//		if (!$_POST['samp_param'.$i]) jobform("error: no sampling parameter specified (MRA)");
		if (!$_POST['minrad'.$i] && $_POST['minrad']!=0) jobform("error: no minimum radius specified for rotational alignment in MRA");
		if (!$_POST['maxrad'.$i]) jobform("error: no maximum radius specified for rotational alignment in MRA");
		if (!$_POST['ignore_images'.$i]) jobform("error: Please specify a value for percentage of images to ignore in MSA");	
		if (!$_POST['ignore_members'.$i]) jobform("error: Please specify a value for percentage of members within each class to ignore in MSA");
		if (!$_POST['num_classums'.$i]) jobform("error: need to specify how many classums to use for each iteration");
		if (!$_POST['keep_classes'.$i]) jobform("error: Please specify the percentage of classes to keep after MSA");
		if (!$_POST['forw_ang_inc'.$i]) jobform("error: angular increment of formward projections for anchor set not specified");
		if (!$_POST['euler_ang_inc'.$i]) jobform("error: no increment specified for euler angle search (Angular Reconstitution)");
		if (!$_POST['keep_ordered'.$i]) jobform("error: Please specify the percentage of ordered classes to keep after Angular Reconstitution");
//		if (!$_POST['hamming_window'.$i]) jobform("error: no hamming window specified");
		if (!$_POST['obj_size'.$i]) jobform("error: object size as fraction of image size not specified");
		imagic3dRefine();
	}
}

// if a model chosen for refinement, go to regular refinement
elseif ($_POST['submitstackmodel'])  {
	if (!$_POST['model']) initModelForm("Error: No model selected");
	if (!$_POST['stackval']) initModelForm("Error: No stack selected");
	jobform();
}	
	
elseif ($_POST['duplicate'])  {
	$postdata = explode('|~~|', $_POST['duplicate']);
	jobform();
}

elseif ($_POST['import']) {
	$postdata = explode('|~~|', $_POST['import']);
	jobform();
}

else initModelForm();

############################################################
##
##		Normal Initial Model Form
##
############################################################
	
function initModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectFromExpId($expId);
	
	$javafunc="<script src='../js/viewer.js'></script>\n";
	processing_header("IMAGIC 3d Refinement Job Form","IMAGIC 3d Refinement Job Form",$javafunc);
	
	if ($expId) $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	else exit;
	
	$particle = new particledata();
	
	// get initial models associated with project
	$models = $particle->getModelsFromProject($projectId);
	
	// find each stack entry in database
	$stackIds = $particle->getStackIds($expId);
	$stackinfo = explode('|--|', $_POST['stackval']);
	$stackid = $stackinfo[0];
	$apix = $stackinfo[1];
	$box = $stackinfo[2];
	
	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	
	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";
	
	echo"<b>Stack:</b><br>";
	$particle->getStackSelector($stackIds, $stackid, '');
	
	// show initial models
	echo "<P><B>Model:</B><br><A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><br>\n";
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
	processing_footer();
	exit;
}	
		
############################################################
##
##		Normal Job Form using stack & initial model
##
############################################################

function jobform($extra=false) {

	$particle = new particledata();	
	
	// get experiment & model info
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","recon",$sessionpath);
		$sessionpath=ereg_replace("data..","data00",$sessionpath);
	}
	
	// get selected initial model data
	$modelinfo = explode('|--|',$_POST['model']);
	$modelid = $modelinfo[0];
	$modeldata = $particle->getInitModelInfo($modelid);
	
	## get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$stackid=$stackinfo[0];
	$nump=$particle->getNumStackParticles($stackid);
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
	$stackpath=$stackinfo[4];
	$stackname1=$stackinfo[5];
	$stackname2=$stackinfo[6];
	$fullname=$stackpath."/".$stackname1;
	$stack=$stackname1;

	// javascript help popups
	$javafunc .= writeJavaPopupFunctions('appion');
	
	// header
	processing_header("IMAGIC 3d Refinement Job Form","IMAGIC 3d Refinement Job Form",$javafunc);

	// write out errors if any came up
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='imagic3dRefine' method='post' action='$formaction'><br />\n";

	// set checkboxes on by default when first loading page
//	$autofiltcheck = ($_POST['auto_filt_stack']=='on' || !$_POST['process']) ? 'checked' : '';
//	$auto_lp_filt_base = ($_POST['auto_lp_filt_base']) ? $_POST['auto_lp_filt_base'] : '25';
//	$auto_lp_filt_fraction = ($_POST['auto_lp_filt_fraction']) ? $_POST['auto_lp_filt_fraction'] : '0.8';
	$centcheck = ($_POST['cent_stack']=='on' || !$_POST['process']) ? 'checked' : '';
	$mirrorcheck = ($_POST['mirror']=='on' || !$_POST['process']) ? 'checked' : '';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	
	// define default variables for directory and runid
	$reconruns = (count($particle->getReconIdsFromSession($expId))) ? count($particle->getReconIdsFromSession($expId)) : 0;
	$outdir = ($_POST[output_directory]) ? $_POST[output_directory] : $sessionpath;
	while (file_exists($outdir.'/imagicRefine'.($reconruns+1))) $reconruns += 1;
	$runid = ($_POST[runid]) ? $_POST[runid] : "imagicRefine".($reconruns+1);
	
	$doc_runname = docpop('runid', '<t><b>Run Name:</b>');
	$doc_outdir = docpop('outdir', '<b>Output Directory:</b>');
	$doc_description = docpop('descr', '<b>Description of 3d Refinement:</b>');
	$doc_mass = docpop('mass', '<b>Approximate mass in Kd</b>');
//	$doc_nproc = docpop('proc', '<b> Number of Processors to use </b>');

	// form for output directory & runid
	echo "<TABLE cellspacing='10' cellpadding='10'><tr><td>";
	echo openRoundBorder();
	echo "	<b> $doc_outdir</b> <input type='text' name='output_directory' value='$outdir' size='50'><br /><br />\n
			<b> $doc_runname</b> <input type='text' name='runid' value='$runid' size='20'><br /><br />\n
			<b> $doc_description</b><br><textarea name='description' rows='3' cols='50'>$rundescrval</textarea><br><br>\n";
	echo closeRoundBorder();
	echo "</td></tr></table><br />";	

	// keys and documentation for user input values
	$display_keys = array('copy', 
						  'itn', 
						  'symmetry', 
						  'mask',
						  'filtering',
						  'MRA', 
						  'MSA', 
						  'Angular_Reconstitution', 
						  'Threed_Reconstruction', 
						  'copy');
	
	// javascript documentation popups as display_keys
	$bgcolor="#E8E8E8";
	echo "<br> <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4><tr>\n";
	foreach ($display_keys as $k => $key) {
		$id = "$key";
		echo "	<td align='center' bgcolor='$bgcolor'> 
				<font class='sf'> 
				<a href='#' id=\"$id\" onMouseOver='popLayer(\"$key\", \"$id\")' onMouseOut='hideLayer()'>
				$key </a></font></td>\n";
	}
	echo"  </tr><br>\n";
	$rcol = ($i % 2) ? '#FFFFFF' : '#FFFDCC';

	// define imports and give the option of selecting them
	echo "<select name='import' onChange='imagic3dRefine.submit()'>\n";
	echo "<option>Import parameters</option>\n";
	echo "<option value='default1'>5 Iterations with 10,000+ particles</option>\n";
	echo "<option value='default2'>10 Iterations with 10,000+ particles</option>\n";
	echo "<br></select>\n";
	$syms = $particle->getSymmetries();
	
	// set j to the number of iterations that were posted with the copy / duplicate function
	$numiters = ($_POST['numiters']) ? $_POST['numiters'] : 1;
	if ($_POST['duplicate']) {
		$numiters+=1;
		$j=$_POST['duplicate'];
	}
	else $j=$numiters;

	// set number of iterations if importing
	if ($_POST['import'] == "default1") $numiters = 5;
	if ($_POST['import'] == "default2") $numiters = 10;

	for ($i=1; $i<=$numiters; $i++)	{
		// define names for user-inputted values for each iteration
		$symmetryn = "symmetry".$i;
		$lp_filtn = "lp_filt".$i;
		$hp_filtn = "hp_filt".$i;
		$auto_filt_stackn = "auto_filt_stack".$i;
//		$auto_lp_filt_basen = "auto_lp_filt_base".$i;
//		$auto_lp_filt_fractionn = "auto_lp_filt_fraction".$i;
		$mask_valn = "mask_val".$i;
		$mrarefs_ang_incn = "mrarefs_ang_inc".$i;
		$max_shift_orign = "max_shift_orig".$i;
		$max_shift_thisn = "max_shift_this".$i;
		$minradn = "minrad".$i;
		$maxradn = "maxrad".$i;
		$ignore_imagesn = "ignore_images".$i;
		$num_classumsn = "num_classums".$i;
		$num_eigenimagesn = "num_eigenimages".$i;
		$ignore_membersn = "ignore_members".$i;
		$keep_classesn = "keep_classes".$i;
		$forw_ang_incn = "forw_ang_inc".$i;
		$euler_ang_incn = "euler_ang_inc".$i;
		$keep_orderedn = "keep_ordered".$i;
		$hamming_windown = "hamming_window".$i;
		$obj_sizen = "obj_size".$i;
		$threedfiltn = "threedfilt".$i;

		// if importing values, set them here
		if ($_POST['import']=='default1') {
			// default 1 parameters with 5 iterations
			$nproc = ($_POST[$nproc]) ? $_POST[$nproc] : "8";
			$mass = ($_POST[$mass]) ? $_POST[$mass] : "";
			$symmetry = $modeldata['REF|ApSymmetryData|symmetry'];
			$mask_val = ($_POST[$mask_valn]) ? $_POST[$mask_valn] : ($box/2)-2;
			$lp_filt = "25";
			$hp_filt = "600";
			$auto_filt_stack = "CHECKED";
//			$auto_lp_filt_base = "25";
//			$auto_lp_filt_fraction = "0.8";
			$mrarefs_ang_inc = "25";
			$max_shift_orig = (int)($box/2*0.4);
			$max_shift_this = (int)($box/2*0.1);
			$minrad = "0";
			$maxrad = (int)($mask_val*0.8);
			$ignore_images = (35 - $i*5);
			$ignore_members = "10";
			$num_classums = $i*25 + 75;
			$num_eigenimages = $i*4 + 1;
			$keep_classes = "0.9";
			$forw_ang_inc = (30 - $i*5);
			$euler_ang_inc = (12 - $i*2);
			$keep_ordered = "0.9";
			$obj_size = "0.8";
			$threedfilt = "20";
		}
		elseif ($_POST['import']=='default2') {
			// default 2 parameters with 10 iterations
			$nproc = ($_POST[$nproc]) ? $_POST[$nproc] : "8";
			$mass = ($_POST[$mass]) ? $_POST[$mass] : "";
			$symmetry = $modeldata['REF|ApSymmetryData|symmetry'];
			$mask_val = ($_POST[$mask_valn]) ? $_POST[$mask_valn] : ($box/2)-2;
			$lp_filt = "25";
			$hp_filt = "600";
			$auto_filt_stack = "CHECKED";
//			$auto_lp_filt_base = "25";
//			$auto_lp_filt_fraction = "0.8";
			$mrarefs_ang_inc = "25";
			$max_shift_orig = (int)($box/2*0.4);
			$max_shift_this = (int)($box/2*0.1);
			$minrad = "0";
			$maxrad = (int)($mask_val*0.8);
			$ignore_images = (($i % 2) == 0) ? (35 - ceil(($i-1)/2)*5) : (35 - ceil($i/2)*5);
			$ignore_members = "10";
			$num_classums = (($i % 2) == 0) ? (75 + ceil(($i-1)/2)*25) : (75 + ceil($i/2)*25);
			$num_eigenimages = $i*2 + 3;
			$keep_classes = "0.9";
			$forw_ang_inc = (($i % 2) == 0) ? (30 - ceil(($i-1)/2)*5) : (30 - ceil($i/2)*5);
			$euler_ang_inc = (($i % 2) == 0) ? (12 - ceil(($i-1)/2)*2) : (12 - ceil($i/2)*2);
			$keep_ordered = "0.9";
			$obj_size = "0.8";
			$threedfilt = "20";
		}
		else {
			// define default parameters for 1st iteration
			if ($i==1)	{
				$nproc = ($_POST[$nproc]) ? $_POST[$nproc] : "8";
				$mass = ($_POST[$mass]) ? $_POST[$mass] : "";
				$symmetry = ($_POST[$symmetryn]) ? $_POST[$symmetryn] : $symmetry;
				$lp_filt = ($_POST[$lp_filtn]) ? $_POST[$lp_filtn] : "25";
				$hp_filt = ($_POST[$hp_filtn]) ? $_POST[$hp_filtn] : "600";
//				$auto_lp_filt_base = ($_POST[$auto_lp_filt_basen]) ? $_POST[$auto_lp_filt_basen] : "25";
//				$auto_lp_filt_fraction = ($_POST[$auto_lp_filt_fractionn]) ? $_POST[$auto_lp_filt_fractionn] : "0.8";
				$mask_val = ($_POST[$mask_valn]) ? $_POST[$mask_valn] : ($box/2)-2;
				$mrarefs_ang_inc = ($_POST[$mrarefs_ang_incn]) ? $_POST[$mrarefs_ang_incn] : "25";
				$max_shift_orig = ($_POST[$max_shift_orign]) ? $_POST[$max_shift_orign] : (int)($box/2*0.4);
				$max_shift_this = ($_POST[$max_shift_thisn]) ? $_POST[$max_shift_thisn] : (int)($box/2*0.1);
				$minrad = ($_POST[$minradn]) ? $_POST[$minradn] : "0";
				$maxrad = ($_POST[$maxradn]) ? $_POST[$maxradn] : (int)($mask_val*0.8);
				$ignore_images = ($_POST[$ignore_imagesn]) ? $_POST[$ignore_imagesn] : "10";
				$ignore_members = ($_POST[$ignore_membersn]) ? $_POST[$ignore_membersn] : "10";
				$num_classums = ($_POST[$num_classumsn]) ? $_POST[$num_classumsn] : "";
				$num_eigenimages = ($_POST[$num_eigenimagesn]) ? $_POST[$num_eigenimagesn] : "5";
				$keep_classes = ($_POST[$keep_classesn]) ? $_POST[$keep_classesn] : "0.9";
				$forw_ang_inc = ($_POST[$forw_ang_incn]) ? $_POST[$forw_ang_incn] : "25";
				$euler_ang_inc = ($_POST[$euler_ang_incn]) ? $_POST[$euler_ang_incn] : "10";
				$keep_ordered = ($_POST[$keep_orderedn]) ? $_POST[$keep_orderedn] : "0.9";
				$obj_size = ($_POST[$obj_sizen]) ? $_POST[$obj_sizen] : "0.8";
				$threedfilt = ($_POST[$threedfiltn]) ? $_POST[$threedfiltn] : "20";
			}
			// copy parameters from previous post
			else 	{
				$symmetry = ($i>$j) ? $_POST['symmetry'.($i-1)] : $_POST[$symmetryn];
				$mask_val = ($i>$j) ? $_POST['mask_val'.($i-1)] : $_POST[$mask_valn];
				$lp_filt = ($i>$j) ? $_POST['lp_filt'.($i-1)] : $_POST[$lp_filtn];
				$hp_filt = ($i>$j) ? $_POST['hp_filt'.($i-1)] : $_POST[$hp_filtn];
//				$auto_lp_filt_base = ($i>$j) ? $_POST['auto_lp_filt_base'.($i-1)] : $_POST[$auto_lp_filt_basen];
//				$auto_lp_filt_fraction = ($i>$j) ? $_POST['auto_lp_filt_fraction'.($i-1)] : $_POST[$auto_lp_filt_fractionn];
				$mrarefs_ang_inc = ($i>$j) ? $_POST['mrarefs_ang_inc'.($i-1)] : $_POST[$mrarefs_ang_incn];
				$max_shift_orig = ($i>$j) ? $_POST['max_shift_orig'.($i-1)] : $_POST[$max_shift_orign];
				$max_shift_this = ($i>$j) ? $_POST['max_shift_this'.($i-1)] : $_POST[$max_shift_thisn];
				$samp_param = ($i>$j) ? $_POST['samp_param'.($i-1)] : $_POST[$samp_paramn];
				$minrad = ($i>$j) ? $_POST['minrad'.($i-1)] : $_POST[$minradn];
				$maxrad = ($i>$j) ? $_POST['maxrad'.($i-1)] : $_POST[$maxradn];
				$ignore_images = ($i>$j) ? $_POST['ignore_images'.($i-1)] : $_POST[$ignore_imagesn];
				$ignore_members = ($i>$j) ? $_POST['ignore_members'.($i-1)] : $_POST[$ignore_membersn];
				$num_classums = ($i>$j) ? $_POST['num_classums'.($i-1)] : $_POST[$num_classumsn];
				$num_eigenimages = ($i>$j) ? $_POST['num_eigenimages'.($i-1)] : $_POST[$num_eigenimagesn];
				$keep_classes = ($i>$j) ? $_POST['keep_classes'.($i-1)] : $_POST[$keep_classesn];
				$forw_ang_inc = ($i>$j) ? $_POST['forw_ang_inc'.($i-1)] : $_POST[$forw_ang_incn];
				$euler_ang_inc = ($i>$j) ? $_POST['euler_ang_inc'.($i-1)] : $_POST[$euler_ang_incn];
				$keep_ordered = ($i>$j) ? $_POST['keep_ordered'.($i-1)] : $_POST[$keep_orderedn];
				$obj_size = ($i>$j) ? $_POST['obj_size'.($i-1)] : $_POST[$obj_sizen];
				$threedfilt = ($i>$j) ? $_POST['threedfilt'.($i-1)] : $_POST[$threedfiltn];
			}
			// deal with checkboxes for each iteration
			if ($i>$j) {
				$auto_filt_stack = ($_POST['auto_filt_stack'.($i-1)]=='on') ? 'CHECKED' : '';
			}
			else {
				$auto_filt_stack = ($_POST[$auto_filt_stackn]=='on') ? 'CHECKED' : '';
			}

		}

		// print form with user input for all values
		echo "<tr>
       			<td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i|~~|$modelid' onclick='imagic3dRefine.submit()'></td>
       			<td bgcolor='$rcol'><b>$i</b></td>
					<td bgcolor='$rcol'><SELECT NAME='$symmetryn'><OPTION VALUE='$symmetry'>Select One</OPTION>\n";
	                	foreach ($syms as $sym) {
	                        	echo "<OPTION VALUE='$sym[DEF_id]'";
										if ($_POST['import'] && $sym['DEF_id']==$modeldata['REF|ApSymmetryData|symmetry']) echo " SELECTED";
	                        	if ($sym['DEF_id']==$_POST[$symmetryn]) echo " SELECTED";
										if ($sym['DEF_id']==$_POST["symmetry".($i-1)] && $symmetry == $_POST["symmetry".($i-1)]) echo " SELECTED";
										echo ">$sym[symmetry]";
	                        	if ($sym['symmetry']=='C1') echo " (no symmetry)";
	                        	echo "</OPTION>\n";
	                	}
	                	echo "</td>
					<td bgcolor='$rcol'><input type='text' NAME='$mask_valn' SIZE='3' VALUE='$mask_val'></td>
					<td bgcolor='$rcol'><input type='text' NAME='$lp_filtn' SIZE='3' VALUE='$lp_filt'>
										<input type='text' NAME='$hp_filtn' SIZE='3' VALUE='$hp_filt'></td>
					<td bgcolor='$rcol'><input type='text' NAME='$mrarefs_ang_incn' SIZE='3' VALUE='$mrarefs_ang_inc'>
										<input type='text' NAME='$max_shift_orign' SIZE='3' VALUE='$max_shift_orig'>
										<input type='text' NAME='$max_shift_thisn' SIZE='3' VALUE='$max_shift_this'>
										<input type='text' NAME='$minradn' SIZE='3' VALUE='$minrad'>
										<input type='text' NAME='$maxradn' SIZE='3' VALUE='$maxrad'></td>
					<td bgcolor='$rcol'><input type='text' NAME='$ignore_imagesn' SIZE='3' VALUE='$ignore_images'>
										<input type='text' NAME='$num_classumsn' SIZE='3' VALUE='$num_classums'>
										<input type='text' NAME='$num_eigenimagesn' SIZE='3' VALUE='$num_eigenimages'>
										<input type='text' NAME='$ignore_membersn' SIZE='3' VALUE='$ignore_members'>
										<input type='text' NAME='$keep_classesn' SIZE='3' VALUE='$keep_classes'></td>
					<td bgcolor='$rcol'><input type='text' NAME='$forw_ang_incn' SIZE='3' VALUE='$forw_ang_inc'>
										<input type='text' NAME='$euler_ang_incn' SIZE='3' VALUE='$euler_ang_inc'>
										<input type='text' NAME='$keep_orderedn' SIZE='3' VALUE='$keep_ordered'></td>
	        		<td bgcolor='$rcol'><input type='text' NAME='$obj_sizen' SIZE='3' VALUE='$obj_size'>
										<input type='text' NAME='$threedfiltn' SIZE='3' value='$threedfilt'></td>
	       		<td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i|~~|$modelid' onclick='imagic3dRefine.submit()'></td>
     	   	</tr>\n";
	}
	echo "</table>";

	echo "<br></b><input type='text' name='mass' value='$mass' size='4'> $doc_mass <br>";
//	echo "<br></b><input type='text' name='nproc' value='$nproc' size='4'> $doc_nproc <br>";

//	echo "<br><input type='checkbox' NAME='auto_filt_stack' $autofiltcheck>\t";
//	echo "<input type='text' NAME='auto_lp_filt_base' SIZE='2' VALUE='$auto_lp_filt_base'>\t";
//	echo "<input type='text' NAME='auto_lp_filt_fraction' SIZE='2' VALUE='$auto_lp_filt_fraction'>\t";
//	echo docpop('auto_filter','<B>Auto-filter stack for each iteration</B>');

	// parameters that do not change from iteration to iteration
	echo "<br><INPUT TYPE='checkbox' NAME='cent_stack' $centcheck>\n";
	echo docpop('center','<B>Center stack prior to alignment</B>');
	echo "<br><INPUT TYPE='checkbox' NAME='mirror' $mirrorcheck>\n";
	echo docpop('mirror','<B>Mirror references for alignment</B>');
	echo "<br><INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	
	// hidden variables
	echo "<input type='hidden' NAME='nproc' VALUE='$nproc'><P>";
  	echo "<input type='hidden' NAME='numiters' VALUE='$numiters'><P>";
	echo "<input type='hidden' NAME='modelid' VALUE='$modelid'><P>";
	echo "<input type='hidden' NAME='norefClassId' VALUE='$norefClassId'><P>";
	echo "<input type='hidden' NAME='clusterId' VALUE='$clusterId'><P>";
	echo "<input type='hidden' NAME='stackval' value='".$_POST['stackval']."'>\n";
	echo "<input type='hidden' NAME='model' value='".$_POST['model']."'>\n";
	echo getSubmitForm("run imagic");
	echo "</form><br><br>\n";
	
	// display stack and initial model at the end
	echo "<table class='tablebubble'><tr><td>\n";
	echo stacksummarytable($stackid, true);
	echo "</td></tr><tr><td>\n";
	echo modelsummarytable($modelid, true);
	echo "</td></tr></table>\n";
	
	processing_footer();
	exit;
}

############################################################
##
##		3d Refine - Write Job Form
##
############################################################

function imagic3dRefine() {
	// get variables from $_POST[] array
	$expId = $_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$outdir = $_POST['output_directory'];
	$runid = $_POST['runid'];
	$imagic3d0id = $_POST['imagic3d0id'];
	$modelid = $_POST['modelid'];
	$norefClassId = $_POST['norefClassId'];
	$clusterId = $_POST['clusterId'];
	$numiters = $_POST['numiters'];
	$description = $_POST['description'];
	$mass = $_POST['mass'];
	$nproc = $_POST['nproc'];
	$autofiltcheck = ($_POST['auto_filt_stack']=="on") ? '--auto_filt_stack' : '';
	$auto_lp_filt_base = $_POST['auto_lp_filt_base'];
	$auto_lp_filt_fraction = $_POST['auto_lp_filt_fraction'];
	$mirror = ($_POST['mirror']=="on") ? '--mirror_refs' : '';
	$cent_stack = ($_POST['cent_stack']=="on") ? '--cent_stack' : '';
	$commit = ($_POST['commit']=="on") ? '--commit' : '';
	
	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackid=$stackinfo[0];
	$stackpath=$stackinfo[4];
	$stackname1=$stackinfo[5];
	$stackname2=$stackinfo[6];
	
	// create batch files for each iteration, put them into working directory
	$command_array = array(); 	// separate command per iteration
	for ($i=1; $i<=$numiters; $i++) {

		$symmetry = $_POST['symmetry'.$i];
		$mask_val = $_POST['mask_val'.$i];
		$lp_filt = $_POST['lp_filt'.$i];
		$hp_filt = $_POST['hp_filt'.$i];
		$mrarefs_ang_inc = $_POST['mrarefs_ang_inc'.$i];
		$max_shift_orig = $_POST['max_shift_orig'.$i];
		$max_shift_this = $_POST['max_shift_this'.$i];
		$samp_param = $_POST['samp_param'.$i];
		$minrad = $_POST['minrad'.$i];
		$maxrad = $_POST['maxrad'.$i];
		$ignore_images = $_POST['ignore_images'.$i];
		$ignore_members = $_POST['ignore_members'.$i];
		$num_classums = $_POST['num_classums'.$i];
		$num_eigenimages = $_POST['num_eigenimages'.$i];
		$keep_classes = $_POST['keep_classes'.$i];
		$forw_ang_inc = $_POST['forw_ang_inc'.$i];
		$euler_ang_inc = $_POST['euler_ang_inc'.$i];
		$keep_ordered = $_POST['keep_ordered'.$i];
		$obj_size = $_POST['obj_size'.$i];
		$threedfilt = $_POST['threedfilt'.$i];

		// update actual job file that calls on the execution of each iteration

		$command = "imagic3dRefine.py";
		$command.= " --projectid=".$_SESSION['projectId'];
		$command.= " --stackid=$stackid";
		if ($imagic3d0id) $command.= " --imagic3d0id=$imagic3d0id";
		else $command.= " --modelid=$modelid";
		$command.= " --runname=$runid";
		$command.= " --rundir=$outdir/$runid";
		$command.= " --numiters=$numiters --itn=$i";
		$command.= " --symmetry=$symmetry";
		$command.= " --mask_val=$mask_val";
		if ($autofiltstack) {
			$command.= " --auto_filt_stack";
			$command.= " --auto_lp_filt_base=$auto_lp_filt_base";
			$command.= " --auto_lp_filt_fraction=$auto_lp_filt_fraction";
		}
		elseif ($lp_filt || $hp_filt) {
			$command.= " --filt_stack";
			if ($lp_filt) $command.= " --lp_filt=$lp_filt";
			if ($hp_filt)	$command.= " --hp_filt=$hp_filt";
		}
		$command.= " --mrarefs_ang_inc=$mrarefs_ang_inc";
		$command.= " --max_shift_orig=$max_shift_orig";
		$command.= " --max_shift_this=$max_shift_this";
		$command.= " --minrad=$minrad";
		$command.= " --maxrad=$maxrad";
		$command.= " --ignore_images=$ignore_images";
		$command.= " --ignore_members=$ignore_members";
		$command.= " --num_classes=$num_classums";
		$command.= " --num_eigenimages=$num_eigenimages";
		$command.= " --keep_classes=$keep_classes";
		$command.= " --forw_ang_inc=$forw_ang_inc";
		$command.= " --euler_ang_inc=$euler_ang_inc";
		$command.= " --keep_ordered=$keep_ordered";
		$command.= " --object_size=$obj_size";
		if ($threedfilt) $command.= " --3d_lpfilt=$threedfilt";
		$command.= " --description=\"$description\"";
		if ($mass) $command.= " --mass=$mass";
		$command.= " --nproc=$nproc";
		if ($mirror) $command.= " --mirror_refs";
		if ($cent_stack) $command.= " --cent_stack";
		if ($commit) $command.= " --commit";
		else $command.=" --no-commit";
		$command_array[] = $command;
	}

	// check for errors in submission
	if ($_POST['process']=="run imagic") {
		if (!($user && $pass)) jobform("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command_array,$outdir,$runid,$expId,'imagic3dRefine',False,False,False,$nproc,8,1,$walltime="720:00:00",$cputime="1200:00:00");
		// if errors:
		if ($sub) jobform("<b>ERROR:</b> $sub");
	}

	processing_header("IMAGIC 3d Refinement Job Generator","IMAGIC 3d Refinement Job Generator",$javafunc);

	// display commands for each iteration of refinement
	echo"
        <TABLE WIDTH='600' BORDER='1'>
        <TR><TD COLSPAN='2'>
        <B>Alignment Command:</B><br><br>";
	foreach ($command_array as $c) {
                echo $c."<br><br>";
	}
	echo"
         </TD></tr>
         </table>\n";

	processing_footer();
	exit;
	
}










?>
