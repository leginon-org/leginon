<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
//require_once "inc/forms/basicRefineForm.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
	
if ($_POST['process']) {
	runAngularReconstitution();
}
else {
	createAngularReconstitutionForm();
}
	
function createAngularReconstitutionForm($extra=False, $title='automatedCommonLines.py Launcher', $heading='Automated Common Lines') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF'];
	}
	
	// connect to particle database
	$particle = new particledata();
	$clusterIds = $particle->getClusteringStacks($sessionId, $projectId);
//	$templateIds = $particle->getTemplateStacksFromSession($sessionId);
	$templateIds = $particle->getTemplateStacksFromProject($projectId);
	$aclrunsarray = $particle->getAngularReconstitutionRuns($sessionId);
	$aclruns= ($aclrunsarray) ? count($aclrunsarray) : 0;
	
	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript .= writeJavaPopupFunctions('appion');	
	
	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	echo "<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$sessionpath=getBaseAppionPath($sessioninfo).'/angrecon/';
	
	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';	
	
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'acl'.($aclruns+1)))
		$aclruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'acl'.($aclruns+1);
	$description = $_POST['description'];
	$clusteridstr = $_POST['clustervals'];
	list($clusterid,$apix,$boxsz,$num_classes,$totprtls) = split('\|--\|', $clusteridstr);
	$tsidstr = $_POST['tsvals'];
	list($tsid,$apix,$boxsz,$totprtls,$type) = split('\|--\|', $tsidstr);
	$weight = ($_POST && !$_POST['weight']) ? '' : 'checked';
	$prealign = ($_POST && !$_POST['prealign']) ? '' : 'checked';
	$scale = ($_POST && !$_POST['scale']) ? '' : 'checked';
	$nvol = ($_POST['nvol']) ? $_POST['nvol'] : '100';
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '8';
	$asqfilt = ($_POST['asqfilt']=='on') ? 'checked' : '';
//	$linmask = ($_POST['linmask']) ? $_POST['linmask'] : '0.67';
	$anginc = ($_POST['anginc']) ? $_POST['anginc'] : '2';
	$keep_ordered = ($_POST['keep_ordered']) ? $_POST['keep_ordered'] : '90';
	$filt3d = ($_POST['filt3d']) ? $_POST['filt3d'] : '30';
	$nref = ($_POST['nref']) ? $_POST['nref'] : '1';
	$usePCA = ($_POST && !$_POST['usePCA']) ? '' : 'checked';
	$numeigens = ($_POST['numeigens']) ? $_POST['numeigens'] : '20';
	$preftype = ($_POST['preftype']) ? $_POST['preftype'] : 'median';
//	$recalc = ($_POST['recalc']=='on') ? 'checked' : '';
	
	// options for the parameters
	echo "<table border='0' class='tableborder'>\n<TR><TD valign='top'>\n";
		echo "<table border='0' cellpadding='5'>\n";
			echo "<tr><td>\n";
				echo openRoundBorder();
				echo docpop('runname','<b>Angular Reconstitution Run Name:</b>');
				echo "<input type='text' name='runname' value='$runname'>\n";
				echo "<br />\n";
				echo "<br />\n";
				echo docpop('outdir','<b>Output Directory:</b>');
				echo "<br />\n";
				echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
				echo "<br />\n";
				echo "<br />\n";
				echo docpop('descr','<b>Description of Angular Reconstitution Run:</b>');
				echo "<br />\n";
				echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
				echo closeRoundBorder();
				echo "</td></tr>\n";

			// stack selection
			echo "<TR><TD>\n";
				if (!$clusterIds && !$templateIds) {
					echo "<font color='red'><B>No Clustering Stacks or Template Stacks for this Session</B></FONT>\n";
				} 
				else {
					if ($clusterIds) {
						echo "<br><b> Clustering Stack: </b>";
						echo "<br><SELECT NAME='clustervals'>\n";
						echo "<OPTION VALUE='select'>select one</OPTION>";
						foreach ($clusterIds as $c) {
							$clusterId = $c['DEF_id'];
							$apix = $c['pixelsize'];
							$boxsz = $c['boxsize'];
							$num_classes = $c['num_classes'];
							$totprtls = $c['num_particles'];
							echo "<OPTION VALUE='$clusterId|--|$apix|--|$boxsz|--|$num_classes|--|$totprtls'";
							if ($clusterid == $clusterId) echo " SELECTED";
							echo ">$clusterId: ($apix &Aring;/pixel, $boxsz pixels, $num_classes classes from $totprtls particles)</OPTION>\n";
						}
						echo "</SELECT>\n";						
					}
					if ($templateIds) {
						echo "<br><br>OR<br><br><b> Template Stack: </b>";
						echo "<br><SELECT NAME='tsvals'>\n";
						echo "<OPTION VALUE='select'>select one</OPTION>";
						foreach ($templateIds as $temp) {
							$templateId = $temp['DEF_id'];
							$templatename = $temp['templatename'];
							$apix = $temp['apix'];
							$boxsz = $temp['boxsize'];
							$totprtls = "";
							if ($temp['cls_avgs'] == 1) $type = "Class Averages";
							elseif ($temp['forward'] == 1) $type = "Forward Projections";
							echo "<OPTION VALUE='$templateId|--|$apix|--|$boxsz|--|$totprtls|--|$type'";
							if ($tsid == $templateId) echo " SELECTED";
							echo ">$templateId: $templatename ($apix &Aring;/pixel, $boxsz pixels)</OPTION>\n";
						}
						echo "</SELECT>\n";
					}
					
				}
				echo "</TD></TR>\n";
//			echo "<TR><TD VALIGN='TOP'>\n</TD></TR>\n";
			echo "<TR>\n<TD VALIGN='TOP'>\n";
				echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
				echo docpop('commit','<B>Commit to Database</B>');
				echo "<br><br>";
	
				echo "<INPUT TYPE='text' NAME='nproc' SIZE='4' VALUE='$nproc'>\n";
				echo "Number of Processors <br/>\n";
				echo "</TD></TR><TR></TR>\n";
			echo "</table>\n</TD>\n";
		echo "<TD CLASS='tablebg'><TABLE cellpading='5' BORDER='0'>\n";
			echo "<TR><TD VALIGN='TOP'>\n";
	
				echo "<INPUT TYPE='text' NAME='nvol' VALUE='$nvol' SIZE='4'>\n";
				echo docpop('nvol','Number of Volumes to Compute');
				echo "<br/>\n";
	
				echo "<br/>\n";
				echo "<b>Preparatory Parameters</b>\n";
				echo "<br/>\n";
	
				echo "<INPUT TYPE='checkbox' NAME='scale' $scale>\n";
				echo docpop('scale','Scale class averages to 64x64 pixels');
				echo "<br>";
	
				echo "<INPUT TYPE='checkbox' NAME='prealign' $prealign>\n";
				echo docpop('prealign','Iteratively align class averages to each other');
				echo "<br>";
	
				echo "<br/>\n";
				echo "<b>Angular Reconstitution</b>\n";
				echo "<br/>\n";
		
				echo "<INPUT TYPE='checkbox' NAME='weight' $weight>\n";;
				echo docpop('weight_randomization','Weight randomization based on image differences');
				echo "<br>";
			
				echo "<INPUT TYPE='checkbox' NAME='asqfilt' $asqfilt>\n";
				echo docpop('asqfilt','ASQ filter the sinogram lines');
				echo "<br/>\n";
	
				echo "<INPUT TYPE='text' NAME='linmask' VALUE='$linmask' SIZE='4'>\n";
				echo docpop('linmask','Linear mask radius for sinograms');
				echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
				echo "<br/>\n";
	
				echo "<INPUT TYPE='text' NAME='anginc' VALUE='$anginc' SIZE='4'>\n";
				echo docpop('ang_inc2','Angular Increment of Search');
				echo "<font size='-2'>(degrees)</font>\n";
				echo "<br/>\n";
		
				echo "<INPUT TYPE='text' NAME='keep_ordered' VALUE='$keep_ordered' SIZE='4'>\n";
				echo docpop('keep_ordered','Percentage of \'ordered\' images to keep');
				echo "<font size='-2'>(percentage)</font>\n";
				echo "<br/>\n";	
		
				echo "<INPUT TYPE='text' NAME='filt3d' VALUE='$filt3d' SIZE='4'>\n";
				echo docpop('threedfilt','Volume Filter');
				echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
				echo "<br/>\n";	
		
				echo "<br/>\n";
				echo "<b>3D Alignment</b>\n";
				echo "<br/>\n";

				echo "<INPUT TYPE='text' NAME='nref' VALUE='$nref' SIZE='4'>\n";
				echo docpop('nref','Number of Alignment References');
				echo "<br/>\n";	

				echo "<br/>\n";
				echo "<b>3D Classification</b>\n";
				echo "<br/>\n";
		
				echo "<INPUT TYPE='checkbox' NAME='usePCA' $usePCA>\n";
				echo docpop('usePCA','Use Principal Components Analysis');
				echo "<br>";
		
				echo "<INPUT TYPE='text' NAME='numeigens' VALUE='$numeigens' SIZE='4'>\n";
				echo docpop('numeigens','Number of Eigenimages');
				echo "<br><br/>\n";	

//				echo "<INPUT TYPE='checkbox' NAME='recalc' $recalc<br/>\n";
//				echo docpop('recalc','Recalculate volumes after PCA');
//				echo "<br><br>";
	
				echo docpop('PreferenceType', 'Preference Type for Affinity Propagation');
				echo "<br>\n";
				echo "<SELECT name='preftype'>";
				echo "<OPTION VALUE='median'>Median correlation, greatest # of classes</OPTION>";
				echo "<OPTION VALUE='minimum'>Minimum correlation, normal # of classes</OPTION>";
				echo "<OPTION VALUE='minlessrange'>Minimum correlation - range, fewest # of classes</OPTION>";
				echo "</SELECT><br>";

				echo "<br/>\n";
				echo "<b>3D Refinement</b>\n";
				echo "<br/>\n";

				echo "<INPUT TYPE='text' NAME='mask_radius' VALUE='$mask_radius' SIZE='4'>\n";
				echo docpop('cl_mask_radius','Radius of mask (&Aring;ngstroms)');
				echo "<br>\n";

				echo "<INPUT TYPE='text' NAME='inner_radius' VALUE='$inner_radius' SIZE='4'>\n";
				echo docpop('cl_inner_radius','Inner alignment radius (&Aring;ngstroms)');
				echo "<br>\n";

				echo "<INPUT TYPE='text' NAME='outer_radius' VALUE='$outer_radius' SIZE='4'>\n";
				echo docpop('cl_outer_radius','Outer alignment radius (&Aring;ngstroms)');
				echo "<br>\n";

				echo "<INPUT TYPE='text' NAME='mass' VALUE='$mass' SIZE='4'>\n";
				echo docpop('mass','Particle mass (kDa) - optional');
				echo "<br><br>\n";

//				echo "<br/>\n";
//				echo "<b>Model Evaluation</b>\n";
//				echo "<br/>\n";
		
//				$functions = new basicRefineForm();
//				$functions->insertSymmetrySelectionBox("symmetry");
	
				echo "</TD></TR>\n";
			echo "</table></TD></TR><TR></TR>\n";
	
		echo "<TR><TD COLSPAN='2' ALIGN='CENTER'>\n";
			echo getSubmitForm("Run Automated Common Lines");
			echo "</TD></TR>\n";
		echo "</table>\n";
	echo "</form>\n";

	processing_footer();
	exit;
	
}
	
function runAngularReconstitution() {
	/* *******************
	PART 1: Get variables
	******************** */
	$description = $_POST['description'];
	$clustervals = $_POST['clustervals'];
	$tsvals = $_POST['tsvals'];
	$nvol = $_POST['nvol'];
	$commit = ($_POST['commit']=="on") ? true : false;
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 1;
	$scale = ($_POST['scale']=="on") ? true : false;
	$prealign = ($_POST['prealign']=="on") ? true : false;
	$weight = ($_POST['weight']=="on") ? true : false;
	$asqfilt = ($_POST['asqfilt']=="on") ? true : false;
	$linmask = $_POST['linmask'];
	$anginc = $_POST['anginc'];
	$keep_ordered = $_POST['keep_ordered'];
	$filt3d = $_POST['filt3d'];
	$nref = $_POST['nref'];
	$usePCA = ($_POST['usePCA']=="on") ? true : false;
	$numeigens = $_POST['numeigens'];
//	$recalc = ($_POST['recalc']=="on") ? true : false;
	$preftype = $_POST['preftype'];
	$maskradius = $_POST['mask_radius'];
	$innerradius = $_POST['inner_radius'];
	$outerradius = $_POST['outer_radius'];
	$mass = $_POST['mass'];

	// get selected stack parameters
	if ($clustervals != 'select') 
		list($clusterid,$apix,$boxsz,$num_classes,$totprtls) = split('\|--\|', $clustervals);
	if ($tsvals != 'select') 
		list($tsid,$apix,$boxsz,$totprtls,$type) = split('\|--\|', $tsvals);

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	// make sure a clustering stack or template stack was selected
	if (!$clusterid && !$tsid)
		createAngularReconstitutionForm("<B>ERROR:</B> No stack selected");
	elseif ($clusterid && $tsid)
		createAngularReconstitutionForm("<B>ERROR:</B> must choose EITHER clustering stack OR template stack");
	
	// check for other parameters that need to be specified
	if (!$description)
		createAngularReconstitutionForm("<B>ERROR:</B> Enter a brief description of the run");
	if (!$nvol)
		createAngularReconstitutionForm("<B>ERROR:</B> Enter the number of volumes that you wish to create using Angular Reconstitution");
	if ($nproc > 8)
		createMaxLikeAlignForm("<B>ERROR:</B> Cannot currently use more than 8 processors with Imagic parallelization");

	/* *******************
	PART 3: Create program command
	******************** */

	// setup command
	$command ="automatedCommonLines.py ";
	$command.="--description=\"$description\" ";
	if ($clusterid) $command.="--clusterid=$clusterid ";
	elseif ($tsid) $command.="--templatestackid=$tsid ";
	$command.="--num_volumes=$nvol ";
	if ($scale) $command.="--scale ";
	if ($prealign) $command.="--prealign ";
	if (!$weight) $command.="--non_weighted_sequence ";
	if ($asqfilt) $command.="--asqfilter ";
	if ($linmask) $command.="--linear_mask=$linmask ";
	if ($anginc) $command.="--ang_inc=$anginc ";
	if ($keep_ordered) $command.="--keep_ordered=$keep_ordered ";
	if ($filt3d) $command.="--3d_lpfilt=$filt3d ";
	if ($nref) $command.="--nref=$nref ";
	if ($usePCA) $command.="--PCA ";
	if ($numeigens) $command.="--numeigens=$numeigens ";
//	if ($recalc) $command.="--recalculate_volumes ";
	if ($maskradius) $command.="--mask_radius=$maskradius ";
	if ($innerradius) $command.="--inner_radius=$innerradius ";
	if ($outerradius) $command.="--outer_radius=$outerradius ";
	if ($mass) $command.="--mass=$mass ";
	if ($preftype) $command.="--preftype=$preftype ";
	if ($nproc && $nproc>1) $command.="--nproc=$nproc ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= initModelRef(); // main init model ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'angrecon', $nproc);

	// if error display them
	if ($errors)
		createAngularReconstitutionForm($errors);
	exit;
}
	
	
?>
