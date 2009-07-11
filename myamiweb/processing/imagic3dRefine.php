<?php

/* 


NEED TO GET BOX SIZE FOR FSC



*/

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";


$numiters = ($_POST['numiters']) ? $_POST['numiters'] : 1;
if ($_POST['process'])  {
	if (!$_POST['output_directory']) jobform($modelid, "error: no output directory specified");	
	if (!$_POST['runid']) jobform($modelid, "error: no run ID specified");

	for ($i=1; $i<=$numiters; $i++) {	
		// check for errors in user input values
		if (!$_POST['symmetry'.$i]) jobform($modelid, "error: no symmetry specified");
		if (!$_POST['radius'.$i]) jobform($modelid, "error: no particle radius specified");
		if (!$_POST['mrarefs_ang_inc'.$i]) jobform($modelid, "error: angular increment of forward projections for mra references not specified");
		if (!$_POST['max_shift_orig'.$i]) jobform($modelid, "error: no max shift specified as compared to originals (MRA)");
		if (!$_POST['max_shift_this'.$i]) jobform($modelid, "error: no max shift specified for this iteration (MRA)");
		if (!$_POST['samp_param'.$i]) jobform($modelid, "error: no sampling parameter specified (MRA)");
//		if (!$_POST['ignore_images'.$i]) jobform($modelid, "error: Please specify a value for percentage of images to ignore in MSA");	
//		if (!$_POST['ignore_members'.$i]) jobform($modelid, "error: Please specify a value for percentage of members within each class to ignore in MSA");
		if (!$_POST['num_classums'.$i]) jobform($modelid, "error: you need to specify how many classums you're using for each iteration");
//		if (!$_POST['keep_classes'.$i]) jobform($modelid, "error: Please specify the percentage of classes to keep after MSA");
		if (!$_POST['forw_ang_inc'.$i]) jobform($modelid, "error: angular increment of formward projections for anchor set not specified");
		if (!$_POST['euler_ang_inc'.$i]) jobform($modelid, "error: no increment specified for euler angle search (Angular Reconstitution)");
//		if (!$_POST['keep_ordered'.$i]) jobform($modelid, "error: Please specify the percentage of ordered classes to keep after Angular Reconstitution");
		if (!$_POST['hamming_window'.$i]) jobform($modelid, "error: no hamming window specified");
		if (!$_POST['obj_size'.$i]) jobform($modelid, "error: object size as fraction of image size not specified");
		if (!$_POST['amask_dim'.$i]) jobform($modelid, "error: automask parameters not specified");
		if (!$_POST['amask_lp'.$i]) jobform($modelid, "error: automask parameters not specified");
		if (!$_POST['amask_sharp'.$i]) jobform($modelid, "error: automask parameters not specified");
		if (!$_POST['amask_thresh'.$i]) jobform($modelid, "error: automask parameters not specified");
		imagic3dRefine();
	}
}

elseif ($_POST['refinemodel'])  {
	if (!$_POST['model']) create3d0SummaryForm("Error: No model selected");
	if (!$_POST['stackval']) create3d0SummaryForm("Error: No stack selected");
	else {
		//$modelarrays = explode('|-|-|-|', $_POST['model']);
		//$modelkeys = explode('|~~|', $modelarrays[0]);
		//$modelvals = explode('|~~|', $modelarrays[1]);
		//$modeldata = array_combine($modelkeys, $modelvals);
		$modelid = $_POST['model'];	
		## get stack data
		$stackinfo = explode('|--|',$_POST['stackval']);
		$stackbox = $stackinfo[2];
		jobform($modelid);
	} 
}	
	
elseif ($_POST['duplicate'])  {
	$postdata = explode('|~~|', $_POST['duplicate']);
	$modelid = $postdata[1];
	jobform($modelid);
}

else create3d0SummaryForm();



############################################################
##
##		3d0SummaryForm
##
############################################################

function create3d0SummaryForm($extra=False) {
	// get session and experiment info
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	
	// create instance of class particledata
	$particle = new particledata();
	
	$reclassifieddata = $particle->getImagic3d0ReclassifiedModelsFromSessionId($expId);
	$norefdata= $particle->getImagic3d0NoRefModelsFromSessionId($expId);
	$clusterdata = $particle->get3d0ClusterModelsFromSessionId($expId);
	$tsdata = $particle->get3d0TemplateStackModelsFromSessionId($expId);
	$models = array();
	foreach (array($reclassifieddata, $norefdata, $clusterdata, $tsdata) as $a) {
		if ($a) $models = array_merge($models,$a);
	}
	$nummodels = count($models);

	$javafunc="<script src='../js/viewer.js'></script>\n";
  	processing_header("Imagic 3d0 Summary","Imagic 3d0 Summary",$javafunc);
  	
	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	
	
	// find each stack entry in database
	// THIS IS REALLY, REALLY SLOW
	$stackIds = $particle->getStackIds($expId);
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
	
	
	if (is_array($models) && $nummodels > 0)	{
		// separate shown from hidden
		$shown = array();
		$hidden = array();
		foreach ($models as $model)	{
			$imagic3d0Id = $model['DEF_id'];

			// first update hide value
			if ($_POST['hidemodel'.$imagic3d0Id]) {
				$particle->updateHide('ApImagic3d0Data',$imagic3d0Id,1);
				$model['hidden']=1;
			}
			elseif ($_POST['unhidemodel'.$imagic3d0Id]) {
				$particle->updateHide('ApImagic3d0Data',$imagic3d0Id,0);
				$model['hidden']='';
			}
			if ($model['hidden']==1) $hidden[]=$model;
			else $shown[]=$model;

		}

		echo "<form name='3d0summaryform' method='post' action='$formAction'>\n";
		
		// get stack selector
		echo"<B>Stack:</B><br>";
		$particle->getStackSelector($stackIds,$stackidval,"");
				
		$modeltable.="<P><input type='SUBMIT' name='refinemodel' value='Use this stack and model' onclick=\"parent.
			     location='imagic3dRefine.php?expId=$expId'\"><br>\n";
		foreach ($shown as $m) $modeltable.=modelEntry($m,$particle,True);

		// show hidden reclassifications
		if ($_GET['showHidden'] && $hidden) {
			if ($shown) $modeltable.="<hr />\n";
			$modeltable.="<b>Hidden models</b> ";
			$modeltable.="<a href='".$_SERVER['PHP_SELF']."?expId=$expId'>[hide]</a><br />\n";
			foreach ($hidden as $m) $modeltable.= modelEntry($m,$particle,True,True);
		}
		$modeltable.="<P><input type='SUBMIT' name='refinemodel' value='Use this stack and model' onclick=\"parent.
			     location='imagic3dRefine.php?expId=$expId'\"><br>\n";
		$modeltable.="</form>\n";
	}
	if ($hidden && !$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=True'>[Show Hidden Models]</a><br />\n";

	if ($shown || $hidden) {	
		echo $modeltable;	
	}
	else echo "<B>Project does not contain any Models.</B>\n";
	processing_footer();
	exit;
}

############################################################
##
##		Model Entry Form
##
############################################################

function modelEntry($model, $particle, $sum_specific_params=True, $hidden=False)	{

	$imagic3d0Id = $model['DEF_id'];

	// check to see if initial model was created from reference-free classification or reclassification
	if ($model['REF|ApImagicReclassifyData|reclass'])  {
		$modelparams = $particle->getImagicReclassParamsFrom3d0($imagic3d0Id);
		$reclassnum = $modelparams['DEF_id'];
		$norefClassId = $modelparams['REF|ApNoRefClassRunData|norefclass'];
		$clsavgpath = $modelparams['path']."/".$modelparams['runname'];
		$classimgfile = $clsavgpath."/reclassified_classums_sorted.img";
		$classhedfile = $clsavgpath."/reclassified_classums_sorted.hed";
	}

	if ($model['REF|ApNoRefClassRunData|norefclass']) {
		$modelparams = $particle->getNoRefClassRunParamsFrom3d0($imagic3d0Id);
		$norefClassId = $modelparams['DEF_id'];
		$norefId = $modelparams['REF|ApNoRefRunData|norefRun'];
		$norefparams = $particle->getNoRefParams($norefId);
		$clsavgpath = $norefparams['path']."/".$modelparams['classFile'];
		$classimgfile = $clsavgpath.".img";
		$classhedfile = $clsavgpath.".hed";
	}

	if ($model['REF|ApClusteringStackData|clusterclass']) {
		$clusterparams = $particle->getClusteringStackParamsFrom3d0($imagic3d0Id);
		$clusterId = $clusterparams['DEF_id'];
		$clsavgpath = $clusterparams['path'];
		$classhedfile = $clsavgpath."/".$clusterparams['avg_imagicfile'];
		$classimgfile = str_replace(".hed", ".img", $classhedfile);
	}
	
	if ($model['REF|ApTemplateStackData|templatestack']) {
		$tsparams = $particle->getTemplateStackParamsFrom3d0($imagic3d0Id);
		$tsId = $tsparams['DEF_id'];
		$clsavgpath = $tsparams['path'];
		$classhedfile = $clsavgpath."/".$tsparams['templatename'];
		$classimgfile = str_replace(".hed", ".img", $classhedfile);
	}

	// get 3 initial projections for angular reconstitution associated with model		
	$projections = $model['projections'];
	$projections = explode(";", $projections);
	$modeltable.= "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'><tr>\n";
	$modeltable.= "<td colspan='3'><b> 3 Initial Projections Used in Angular Reconstitution </b></td></tr><tr>";
	foreach ($projections as $key => $projection) {
		$num = $key + 1;
		$image = $projection - 1; // Imagic numbering system starts with 1 instead of 0
		$modeltable.= "<td colspan='1' align='center' valign='top'>";
		$modeltable.= "<img src='getstackimg.php?hed=$classhedfile
			&img=$classimgfile&n=".$image."&t=80&b=1&uh=0'><br/>\n";
		$modeltable.= "<i>projection $num</i></td>\n";
	}
	$modeltable.= "</tr><tr><td colspan='3' bgcolor='#bbffbb'>";
	if ($sum_specific_params) {
		// view class averages used for 3d0 in summary page (both norefs and reclassifications)
		$modeltable.= "<a href='viewstack.php?file=$classimgfile&expId=$expId&reclassId=$reclassnum'>";
		$modeltable.= "View all class averages used to create model</a>";
	}
	else {
		if ($norefClassId) {
			// note that ALL class averages will be used for refinement, NOT the reclassifications
			$norefclassdata = $particle->getNoRefClassRunData($norefClassId);
			$norefId = $norefclassdata['REF|ApNoRefRunData|norefRun'];
			$norefparams = $particle->getNoRefParams($norefId);
			$norefclassimgfile = $norefparams['path']."/".$norefclassdata['classFile'].".img";
			$modeltable.= "<a href='viewstack.php?file=$norefclassimgfile&expId=$expId'>";
			$modeltable.= "View all class averages used for THIS refinement</a>";
		}
		elseif ($clusterId) {
			$modeltable.= "<a href='viewstack.php?file=$classhedfile&expId=$expId'>";
			$modeltable.= "View all class averages used for this refinement</a>";
		}
	}
	$modeltable.= "</td></tr></table>\n<br>";
	$modeltable.= "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";

	// get list of png files in directory
	$pngfiles = array();
	$modeldir = opendir($model['path']."/".$model['runname']);
	while ($f = readdir($modeldir)) {
		if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;

	}
	sort($pngfiles);

			
	// display starting models
	$modeltable.= "<tr><TD COLSPAN=8>\n";
	//$modelkeys="DEF_id|~~|path|~~|name|~~|boxsize|~~|symmetry";
	//$modelvals="$model[DEF_id]|~~|$model[path]/$model[runname]|~~|$model[name]|~~|$model[boxsize]|~~|$model[symmetry]";
	if ($sum_specific_params) {			
		$modeltable.= "<input type='RADIO' NAME='model' VALUE='$model[DEF_id]' ";
	
		// check if model was selected
		if ($model['DEF_id']==$minf[0]) echo " CHECKED";
		$modeltable.= ">\n";
	}		
			

	if ($sum_specific_params) $modeltable.="Use ";
	$modeltable.="Model ID: <b>$model[DEF_id]</b>\n";

/*	$modeltable.= "<input type='BUTTON' NAME='rescale' VALUE='Rescale/Resize this model' onclick=\"parent.
	     location='uploadmodel.php?expId=$expId&rescale=TRUE&imagic3d0id=$model[DEF_id]'\"><br>\n";
*/
	if ($sum_specific_params) {			
		if ($hidden) $modeltable.= " <input class='edit' type='submit' name='unhidemodel".$imagic3d0Id."' value='unhide'>";
		else $modeltable.= " <input class='edit' type='submit' name='hidemodel".$imagic3d0Id."' value='hide'>";
	}

	// display all .png files in model directory
	$modeltable.= "<tr>";
	foreach ($pngfiles as $snapshot) {
		$snapfile = $model['path'].'/'.$model['runname'].'/'.$snapshot;
		$modeltable.= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>
			<img src='loadimg.php?h=80&filename=$snapfile' HEIGHT='80'>\n";
	}

	// display info about each model run
	$modeltable.= "</tr>\n";
	$modeltable.="<tr><TD COLSPAN=8>description: $model[description]</td>\n";
	$modeltable.="<tr><TD COLSPAN=8>path: $model[path]/$model[runname]/$model[name]</td></tr>\n";
	
	$modeltable.="<tr><td>pixel size:</td><td><b>$model[pixelsize]</b></td>
			  <td>box size:</td><td><b>$model[boxsize]</b></td>
	   		  <td>symmetry:</td><td><b>$model[symmetry]</b></td>
	   		  <td># class averages used:</td><td><b>$model[num_classums]</b></td></tr>\n";
	
	$modeltable.="<tr><td>Automask dimension parameter:</td><td><b>$model[amask_dim]</b></td>
			  <td>Automask low-pass parameter:</td><td><b>$model[amask_lp]</b></td>
			  <td>Automask sharpness parameter:</td><td><b>$model[amask_sharp]</b></td>
			  <td>Automask thresholding parameter:</td><td><b>$model[amask_thresh]</b></td></tr>\n";
	$modeltable.="<tr><td>Increment euler angle search:</td><td><b>$model[euler_ang_inc]</b></td>
			  <td>Increment forward projections:</td><td><b>$model[forw_ang_inc]</b></td>
			  <td>Hamming window:</td><td><b>$model[ham_win]</b></td>
			  <td>Object size as fraction of image size:</td><td><b>$model[obj_size]</b></td></tr>\n";
	$modeltable.= "</table><br><br>\n";
	$modeltable.= "<P>\n";


	if ($sum_specific_params) {
		return $modeltable;
	}
	else {
		$returnvalues = array();
		$returnvalues[] = $modeltable;
		$returnvalues[] = $norefClassId;
		return $returnvalues;
	}
	
}

############################################################
##
##		3d Refine Job Form
##
############################################################

function jobform($modelid, $extra=false) {

	$particle = new particledata();	
	
	// get experiment & model info
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$sessiondata=getSessionList($projectId,$expId);
	$modeldata = $particle->getImagic3d0Data($modelid);
	$clusterId = $modeldata['REF|ApClusteringStackData|clusterclass'];
	
	## get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$nump=$particle->getNumStackParticles($stackidval);
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
	$stackpath=$stackinfo[3];
	$stackname1=$stackinfo[4];
	$stackname2=$stackinfo[5];
	
	$stack=$stackname1;

	$numiters = ($_POST['numiters']) ? $_POST['numiters'] : 1;
	if ($_POST['duplicate']) {
		$numiters+=1;
		$j=$_POST['duplicate'];
	}
	else $j=$numiters;

	$javafunc .= writeJavaPopupFunctions('appion');
	processing_header("IMAGIC 3d Refinement Job Form","IMAGIC 3d Refinement Job Form",$javafunc);

	// write out errors if any came up
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";

	echo "<form name='imagic3dRefine' method='post' action='$formaction'><br />\n";

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// define default variables for directory and runid
	$numRefinements = count($particle->getImagic3dRefinementRunsFrom3d0($modelid));
	$newrefinerun = $numRefinements + 1;
	$outdir = ($_POST[output_directory]) ? $_POST[output_directory] : $modeldata['path']."/".$modeldata['runname'];
	$runid = ($_POST[runid]) ? $_POST[runid] : "refine".$newrefinerun;
	
	$doc_runname = docpop('runid', '<t><b>Run Name:</b>');
	$doc_outdir = docpop('outdir', '<b>Output Directory:</b>');
	$doc_description = docpop('descr', '<b>Description of 3d Refinement:</b>');
	$doc_mass = docpop('mass', '<b>Approximate mass in Kd</b>');

	$modelvalues = modelEntry($modeldata,$particle,False,True);
	echo $modelvalues[0];
	$norefClassId = $modelvalues[1];

	// form for output directory & runid
	echo "<TABLE cellspacing='10' cellpadding='10'><tr><td>";
	echo openRoundBorder();
	echo "	<b> $doc_outdir</b> <input type='text' name='output_directory' value='$outdir' size='50'><br /><br />\n
		<b> $doc_runname</b> <input type='text' name='runid' value='$runid' size='20'><br /><br />\n
		<b> $doc_description</b><br><textarea name='description' rows='3' cols='50'>$rundescrval</textarea><br><br>\n";
	echo closeRoundBorder();
	echo "</td></tr></table><br />";	


	// keys and documentation for user input values
/*	$display_keys = array('copy', 
				'itn', 
				'symmetry', 
				'mask_rad',
				'mra_inc', 
				'shift_orig', 
				'shift_this', 
				'samp_par', 
				'ign_images',
				'numclass', 
				'ign_members',
				'keep_classes',
				'forw_inc', 
				'euler_inc', 
				'keep_ordered',
				'ham_win', 
				'obj_size', 
				'amask_dim', 
				'amask_lp', 
				'amask_sharp',
				'amask_thresh', 
				'copy');
*/
	$display_keys = array('copy', 
						  'itn', 
						  'symmetry', 
						  'mask',
						  'MRA', 
						  'MSA', 
						  'Angular_Reconstitution', 
						  'Threed_Reconstruction', 
						  'Automasking', 
						  'copy');
	
	
	$bgcolor="#E8E8E8";
	echo "<br> <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
	<tr>\n";
	foreach ($display_keys as $k => $key) {
		$id = "$key";
		echo "	<td align='center' bgcolor='$bgcolor'> 
			<font class='sf'> 
			<a href='#' id=\"$id\" onMouseOver='popLayer(\"$key\", \"$id\")' onMouseOut='hideLayer()'>
			$key 
			</a></font></td>\n";
	}
	echo"  </tr><br>\n";
	$rcol = ($i % 2) ? '#FFFFFF' : '#FFFDCC';

	for ($i=1; $i<=$numiters; $i++)	{
		// define names for user-inputted values for each iteration
		$symmetryn = "symmetry".$i;
		$radiusn = "radius".$i;
		$mrarefs_ang_incn = "mrarefs_ang_inc".$i;
		$max_shift_orign = "max_shift_orig".$i;
		$max_shift_thisn = "max_shift_this".$i;
		$samp_paramn = "samp_param".$i;
		$ignore_imagesn = "ignore_images".$i;
		$num_classumsn = "num_classums".$i;
		$ignore_membersn = "ignore_members".$i;
		$keep_classesn = "keep_classes".$i;
		$forw_ang_incn = "forw_ang_inc".$i;
		$euler_ang_incn = "euler_ang_inc".$i;
		$keep_orderedn = "keep_ordered".$i;
		$hamming_windown = "hamming_window".$i;
		$obj_sizen = "obj_size".$i;
		$amask_dimn = "amask_dim".$i;
		$amask_lpn = "amask_lp".$i;
		$amask_sharpn = "amask_sharp".$i;
		$amask_threshn = "amask_thresh".$i;

		// define default parameters for 1st iteration
		if ($i==1)	{
			$symmetry = ($_POST[$symmetryn]) ? $_POST[$symmetryn] : $symmetry;
			$radius = ($_POST[$radiusn]) ? $_POST[$radiusn] : "";
			$mrarefs_ang_inc = ($_POST[$mrarefs_ang_incn]) ? $_POST[$mrarefs_ang_incn] : "25";
			$max_shift_orig = ($_POST[$max_shift_orign]) ? $_POST[$max_shift_orign] : "0.4";
			$max_shift_this = ($_POST[$max_shift_thisn]) ? $_POST[$max_shift_thisn] : "0.1";
			$samp_param = ($_POST[$samp_paramn]) ? $_POST[$samp_paramn] : "4";
			$ignore_images = ($_POST[$ignore_imagesn]) ? $_POST[$ignore_imagesn] : "10";
			$ignore_members = ($_POST[$ignore_membersn]) ? $_POST[$ignore_membersn] : "10";
			$num_classums = ($_POST[$num_classumsn]) ? $_POST[$num_classumsn] : "";
			$keep_classes = ($_POST[$keep_classesn]) ? $_POST[$keep_classesn] : "90";
			$forw_ang_inc = ($_POST[$forw_ang_incn]) ? $_POST[$forw_ang_incn] : "25";
			$euler_ang_inc = ($_POST[$euler_ang_incn]) ? $_POST[$euler_ang_incn] : "10";
			$keep_ordered = ($_POST[$keep_orderedn]) ? $_POST[$keep_orderedn] : "90";
			$hamming_window = ($_POST[$hamming_windown]) ? $_POST[$hamming_windown] : "0.8";
			$obj_size = ($_POST[$obj_sizen]) ? $_POST[$obj_sizen] : "0.8";
			$amask_dim = ($_POST[$amask_dimn]) ? $_POST[$amask_dimn] : "0.04";
			$amask_lp = ($_POST[$amask_lpn]) ? $_POST[$amask_lpn] : "0.3";
			$amask_sharp = ($_POST[$amask_sharpn]) ? $_POST[$amask_sharpn] : "0.3";
			$amask_thresh = ($_POST[$amask_threshn]) ? $_POST[$amask_threshn] : "15";
		}
		// copy parameters from previous post
		else 	{
			$symmetry = ($i>$j) ? $_POST['symmetry'.($i-1)] : $_POST[$symmetryn];
			$radius = ($i>$j) ? $_POST['radius'.($i-1)] : $_POST[$radiusn];
			$mrarefs_ang_inc = ($i>$j) ? $_POST['mrarefs_ang_inc'.($i-1)] : $_POST[$mrarefs_ang_incn];
			$max_shift_orig = ($i>$j) ? $_POST['max_shift_orig'.($i-1)] : $_POST[$max_shift_orign];
			$max_shift_this = ($i>$j) ? $_POST['max_shift_this'.($i-1)] : $_POST[$max_shift_thisn];
			$samp_param = ($i>$j) ? $_POST['samp_param'.($i-1)] : $_POST[$samp_paramn];
			$ignore_images = ($i>$j) ? $_POST['ignore_images'.($i-1)] : $_POST[$ignore_imagesn];
			$ignore_members = ($i>$j) ? $_POST['ignore_members'.($i-1)] : $_POST[$ignore_membersn];
			$num_classums = ($i>$j) ? $_POST['num_classums'.($i-1)] : $_POST[$num_classumsn];
			$keep_classes = ($i>$j) ? $_POST['keep_classes'.($i-1)] : $_POST[$keep_classesn];
			$forw_ang_inc = ($i>$j) ? $_POST['forw_ang_inc'.($i-1)] : $_POST[$forw_ang_incn];
			$euler_ang_inc = ($i>$j) ? $_POST['euler_ang_inc'.($i-1)] : $_POST[$euler_ang_incn];
			$keep_ordered = ($i>$j) ? $_POST['keep_ordered'.($i-1)] : $_POST[$keep_orderedn];
			$hamming_window = ($i>$j) ? $_POST['hamming_window'.($i-1)] : $_POST[$hamming_windown];
			$obj_size = ($i>$j) ? $_POST['obj_size'.($i-1)] : $_POST[$obj_sizen];
			$amask_dim = ($i>$j) ? $_POST['amask_dim'.($i-1)] : $_POST[$amask_dimn];
			$amask_lp = ($i>$j) ? $_POST['amask_lp'.($i-1)] : $_POST[$amask_lpn];
			$amask_sharp = ($i>$j) ? $_POST['amask_sharp'.($i-1)] : $_POST[$amask_sharpn];
			$amask_thresh = ($i>$j) ? $_POST['amask_thresh'.($i-1)] : $_POST[$amask_threshn];
		}
		$syms = $particle->getSymmetries();
		// print form with user input for all values
		echo "<tr>
       			<td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i|~~|$modelid' onclick='imagic3dRefine.submit()'></td>
       			<td bgcolor='$rcol'><b>$i</b></td>
				<td bgcolor='$rcol'><SELECT NAME='$symmetryn'><OPTION VALUE='$symmetry'>Select One</OPTION>\n";
                	foreach ($syms as $sym) {
                        	echo "<OPTION VALUE='$sym[DEF_id]'";
                        	if ($sym['DEF_id']==$_POST[$symmetryn]) echo " SELECTED";
				if ($sym['DEF_id']==$_POST["symmetry".($i-1)] && $symmetry == $_POST["symmetry".($i-1)]) echo " SELECTED";
				echo ">$sym[symmetry]";
                        	if ($sym['symmetry']=='C1') echo " (no symmetry)";
                        	echo "</OPTION>\n";
                	}
                	echo "</td>
				<td bgcolor='$rcol'><input type='text' NAME='$radiusn' SIZE='4' VALUE='$radius'></td>
				<td bgcolor='$rcol'><input type='text' NAME='$mrarefs_ang_incn' SIZE='3' VALUE='$mrarefs_ang_inc'>
									<input type='text' NAME='$max_shift_orign' SIZE='3' VALUE='$max_shift_orig'>
									<input type='text' NAME='$max_shift_thisn' SIZE='3' VALUE='$max_shift_this'>
									<input type='text' NAME='$samp_paramn' SIZE='3' VALUE='$samp_param'></td>
				<td bgcolor='$rcol'><input type='text' NAME='$ignore_imagesn' SIZE='3' VALUE='$ignore_images'>
									<input type='text' NAME='$num_classumsn' SIZE='4' VALUE='$num_classums'>
									<input type='text' NAME='$ignore_membersn' SIZE='3' VALUE='$ignore_members'>
									<input type='text' NAME='$keep_classesn' SIZE='3' VALUE='$keep_classes'></td>
				<td bgcolor='$rcol'><input type='text' NAME='$forw_ang_incn' SIZE='3' VALUE='$forw_ang_inc'>
									<input type='text' NAME='$euler_ang_incn' SIZE='3' VALUE='$euler_ang_inc'>
									<input type='text' NAME='$keep_orderedn' SIZE='3' VALUE='$keep_ordered'></td>
        		<td bgcolor='$rcol'><input type='text' NAME='$hamming_windown' SIZE='4' VALUE='$hamming_window'>
									<input type='text' NAME='$obj_sizen' SIZE='4' VALUE='$obj_size'></td>
        		<td bgcolor='$rcol'><input type='text' NAME='$amask_dimn' SIZE='4' value='$amask_dim'>
									<input type='text' NAME='$amask_lpn' SIZE='4' VALUE='$amask_lp'>
									<input type='text' NAME='$amask_sharpn' SIZE='4' value='$amask_sharp'>
									<input type='text' NAME='$amask_threshn' SIZE='4' VALUE='$amask_thresh'></td>
       			<td bgcolor='$rcol'><input type='radio' NAME='duplicate' VALUE='$i|~~|$modelid' onclick='imagic3dRefine.submit()'></td>
     	    	</tr>\n";
	}
	echo "</table>";

	echo "<br></b><input type='text' name='mass' value='$mass' size='4'> $doc_mass <br>";

	echo "<br><INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');

  	echo "<input type='hidden' NAME='numiters' VALUE='$numiters'><P>";
	echo "<input type='hidden' NAME='modelid' VALUE='$modelid'><P>";
	echo "<input type='hidden' NAME='norefClassId' VALUE='$norefClassId'><P>";
	echo "<input type='hidden' NAME='clusterId' VALUE='$clusterId'><P>";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";
	echo getSubmitForm("run imagic");
	echo "</form>\n";
	processing_footer();
	exit;
}

############################################################
##
##		3d Refine - Write Job Form
##
############################################################

function imagic3dRefine() {
	$expId = $_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$outdir = $_POST['output_directory'];
	$runid = $_POST['runid'];
	$modelid = $_POST['modelid'];
	$norefClassId = $_POST['norefClassId'];
	$clusterId = $_POST['clusterId'];
	$numiters = $_POST['numiters'];
	$description = $_POST['description'];
	$mass = $_POST['mass'];
	$commit = ($_POST['commit']=="on") ? '--commit' : '';
	
	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$stackpath=$stackinfo[4];
	$stackname1=$stackinfo[5];
	$stackname2=$stackinfo[6];
	
	// create batch files for each iteration, put them into working directory
	$command_array = array(); 	// separate command per iteration
	for ($i=1; $i<=$numiters; $i++) {

		$symmetry = $_POST['symmetry'.$i];
		$radius = $_POST['radius'.$i];
		$mrarefs_ang_inc = $_POST['mrarefs_ang_inc'.$i];
		$max_shift_orig = $_POST['max_shift_orig'.$i];
		$max_shift_this = $_POST['max_shift_this'.$i];
		$samp_param = $_POST['samp_param'.$i];
		$ignore_images = $_POST['ignore_images'.$i];
		$ignore_members = $_POST['ignore_members'.$i];
		$num_classums = $_POST['num_classums'.$i];
		$keep_classes = $_POST['keep_classes'.$i];
		$forw_ang_inc = $_POST['forw_ang_inc'.$i];
		$euler_ang_inc = $_POST['euler_ang_inc'.$i];
		$keep_ordered = $_POST['keep_ordered'.$i];
		$hamming_window = $_POST['hamming_window'.$i];
		$obj_size = $_POST['obj_size'.$i];
		$amask_dim = $_POST['amask_dim'.$i];
		$amask_lp = $_POST['amask_lp'.$i];
		$amask_sharp = $_POST['amask_sharp'.$i];
		$amask_thresh = $_POST['amask_thresh'.$i];

		// update actual job file that calls on the execution of each iteration

		$command = "imagic3dRefine.py";
		$command.= " --projectid=".$_SESSION['projectId'];
		$command.= " --stackid=$stackidval";
		$command.= " --imagic3d0id=$modelid";
		if ($norefClassId) $command .= " --norefClassId=$norefClassId";
		elseif ($clusterId) $command .= " --clusterId=$clusterId";
		$command.= " --runname=$runid";
		$command.= " --rundir=$outdir/$runid";
		$command.= " --numiters=$numiters --itn=$i";
		$command.= " --symmetry=$symmetry";
		$command.= " --radius=$radius";
		$command.= " --mrarefs_ang_inc=$mrarefs_ang_inc";
		$command.= " --max_shift_orig=$max_shift_orig";
		$command.= " --max_shift_this=$max_shift_this";
		$command.= " --samp_param=$samp_param";
		$command.= " --ignore_images=$ignore_images";
		$command.= " --ignore_members=$ignore_members";
		$command.= " --num_classes=$num_classums";
		$command.= " --keep_classes=$keep_classes";
		$command.= " --forw_ang_inc=$forw_ang_inc";
		$command.= " --euler_ang_inc=$euler_ang_inc";
		$command.= " --keep_ordered=$keep_ordered";
		$command.= " --ham_win=$hamming_window";
		$command.= " --object_size=$obj_size";
		$command.= " --amask_dim=$amask_dim";
		$command.= " --amask_lp=$amask_lp";
		$command.= " --amask_sharp=$amask_sharp";
		$command.= " --amask_thresh=$amask_thresh";
		$command.= " --description=\"$description\"";
		$command.= " --mass=$mass";
		if ($commit) $command.= " --commit";
		else $command.=" --no-commit";
		$command_array[] = $command;
	}

/*
	// write job file
	$jobfile = "{$runid}_imagic3dRefine.job";
	$tmpjobfile = "/tmp/$jobfile";
	$f = fopen($tmpjobfile,'w');
	fwrite($f,$command);
	fclose($f);

	// create appion directory & copy job file
	$cmd = "mkdir -p $outdir/$runid\n";
	$cmd.= "cp $tmpjobfile $outdir/$runid/$jobfile\n";
	$cmd.= "chmod 755 $outdir/$runid/$jobfile\n";
	exec_over_ssh($_SERVER['HTTP_HOST'], $user, $pass, $cmd, True);
*/
	if ($_POST['process']=="run imagic") {
		if (!($user && $pass)) jobform($modelid, "<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command_array,$outdir,$runid,$expId,'imagic3dRefine');
		// if errors:
		if ($sub) jobform($modelid, "<b>ERROR:</b> $sub");
	}

	processing_header("IMAGIC 3d Refinement Job Generator","IMAGIC 3d Refinement Job Generator",$javafunc);

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

/*	echo "<pre>";
	foreach ($command_array as $c) {
		echo htmlspecialchars($c);
	}
	echo "</pre>";
*/
	processing_footer();
	exit;
	
}










?>
