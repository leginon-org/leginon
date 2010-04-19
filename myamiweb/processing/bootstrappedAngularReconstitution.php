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

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
	
if ($_POST) {
	runAngularReconstitution();
}
else {
	createAngularReconstitutionForm();
}
	
function createAngularReconstitutionForm($extra=False, $title='bootstrappedAngularReconstitution.py Launcher', $heading='Bootstrapped Angular Reconstitution') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectFromExpId($sessionId);
		$formAction=$_SERVER['PHP_SELF'];
	}
	
	// connect to particle database
	$particle = new particledata();
	$clusterIds = $particle->getClusteringStacks($sessionId, $projectId);
//	$templateIds = $particle->getTemplateStacksFromSession($sessionId);
	$templateIds = $particle->getTemplateStacksFromProject($projectId);
	$barrunsarray = $particle->getAngularReconstitutionRuns($sessionId);
	$barruns= ($barrunsarray) ? count($barrunsarray) : 0;
	
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
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","angrecon/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	
	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';	
	
	// Set any existing parameters in form
	$sessionpathval = ($_POST['rundir']) ? $_POST['rundir'] : $sessionpath;
	while (file_exists($sessionpathval.'bar'.($barruns+1)))
		$barruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'bar'.($barruns+1);
	$description = $_POST['description'];
	$clusteridstr = $_POST['clustervals'];
	list($clusterid,$apix,$boxsz,$num_classes,$totprtls) = split('\|--\|', $clusteridstr);
	$tsidstr = $_POST['tsvals'];
	list($tsid,$apix,$boxsz,$totprtls,$type) = split('\|--\|', $tsidstr);
	$weight = ($_POST['weight']=='on' || !$_POST['weight']) ? 'checked' : '';
	$prealign = ($_POST['prealign']=='on') ? 'checked' : '';
	$scale = ($_POST['scale']=='on' || !$_POST['scale']) ? 'checked' : '';
	$nvol = ($_POST['nvol']) ? $_POST['nvol'] : '100';
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '8';
	$anginc = ($_POST['anginc']) ? $_POST['anginc'] : '2';
	$keep_ordered = ($_POST['keep_ordered']) ? $_POST['keep_ordered'] : '90';
	$filt3d = ($_POST['filt3d']) ? $_POST['filt3d'] : '20';
	$nref = ($_POST['nref']) ? $_POST['nref'] : '1';
	$usePCAcheck = ($_POST['usePCA']=='on' || !$_POST['usePCA']) ? 'checked' : '';	
	$numeigens = ($_POST['numeigens']) ? $_POST['numeigens'] : '69';
	$preftype = ($_POST['preftype']) ? $_POST['preftype'] : 'median';
	$recalc = ($_POST['recalc']=='on') ? 'checked' : '';
	
	// options for the parameters
	echo "<table border='0' class='tableborder'>\n<TR><TD valign='top'>\n";
		echo "<table border='0' cellpadding='5'>\n";
			echo "<tr><td>\n";
				echo openRoundBorder();
				echo docpop('runname','<b>Angular Reconstitution Run Name:</b>');
				echo "<input type='text' name='runname' value='$runname'>\n";
				echo "<br />\n";
				echo "<br />\n";
				echo docpop('rundir','<b>Output Directory:</b>');
				echo "<br />\n";
				echo "<input type='text' name='rundir' value='$sessionpathval' size='38'>\n";
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
	
				echo "<INPUT TYPE='checkbox' NAME='scale' $scale\n";
				echo docpop('scale','Scale class averages to 64x64 pixels');
				echo "<br>";
	
				echo "<INPUT TYPE='checkbox' NAME='prealign' $prealign\n";
				echo docpop('prealign','Iteratively align class averages to each other');
				echo "<br>";
	
				echo "<br/>\n";
				echo "<b>Angular Reconstitution</b>\n";
				echo "<br/>\n";
		
				echo "<INPUT TYPE='checkbox' NAME='weight' $weight\n";
				echo docpop('weight_randomization','Weight randomization based on image differences');
				echo "<br>";
	
				echo "<INPUT TYPE='text' NAME='anginc' VALUE='$anginc' SIZE='4'>\n";
				echo docpop('ang_inc','Angular Increment of Search');
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
		
				echo "<INPUT TYPE='checkbox' NAME='usePCA' $usePCAcheck\n";
				echo docpop('usePCA','Use Principal Components Analysis');
				echo "<br>";
		
				echo "<INPUT TYPE='text' NAME='numeigens' VALUE='$numeigens' SIZE='4'>\n";
				echo docpop('numeigens','Number of Eigenimages');
				echo "<br/>\n";	

				echo "<INPUT TYPE='checkbox' NAME='recalc' $recalc\n";
				echo docpop('recalc','Recalculate volumes after PCA');
				echo "<br><br>";
	
				echo docpop('PreferenceType', 'Preference Type for Affinity Propagation');
				echo "<br>\n";
				echo "<SELECT name='preftype'>";
				echo "<OPTION VALUE='median'>Median correlation, greatest # of classes</OPTION>";
				echo "<OPTION VALUE='minimum'>Minimum correlation, normal # of classes</OPTION>";
				echo "<OPTION VALUE='minlessrange'>Minimum correlation - range, fewest # of classes</OPTION>";
				echo "</SELECT><br>";
				echo "</TD></TR>\n";
			echo "</table></TD></TR><TR></TR>\n";
	
		echo "<TR><TD COLSPAN='2' ALIGN='CENTER'>\n";
			echo getSubmitForm("Run Bootstrapped Angular Reconstitution");
			echo "</TD></TR>\n";
		echo "</table>\n";
	echo "</form>\n";

	processing_footer();
	exit;
	
}
	
function runAngularReconstitution() {
	$expId = $_GET['expId'];
	$runname = $_POST['runname'];
	$rundir = $_POST['rundir'];
	$description = $_POST['description'];
	$clustervals = $_POST['clustervals'];
	$tsvals = $_POST['tsvals'];
	$nvol = $_POST['nvol'];
	$commit = ($_POST['commit']=="on") ? true : false;
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 1;
	$scale = ($_POST['scale']=="on") ? true : false;
	$prealign = ($_POST['prealign']=="on") ? true : false;
	$weight = ($_POST['weight']=="on") ? true : false;
	$anginc = $_POST['anginc'];
	$keep_ordered = $_POST['keep_ordered'];
	$filt3d = $_POST['filt3d'];
	$nref = $_POST['nref'];
	$usePCA = ($_POST['usePCA']=="on") ? true : false;
	$numeigens = $_POST['numeigens'];
	$recalc = ($_POST['recalc']=="on") ? true : false;
	$preftype = $_POST['preftype'];
	
	// get selected stack parameters
	if ($clustervals != 'select') 
		list($clusterid,$apix,$boxsz,$num_classes,$totprtls) = split('\|--\|', $clustervals);
	if ($tsvals != 'select') 
		list($tsid,$apix,$boxsz,$totprtls,$type) = split('\|--\|', $tsvals);
	
	// make sure a clustering stack or template stack was selected
	if (!$clusterid && !$tsid)
		createAngularReconstitutionForm("<B>ERROR:</B> No stack selected");
	elseif ($clusterid && $tsid)
		createAngularReconstitutionForm("<B>ERROR:</B> must choose EITHER clustering stack OR template stack");
	
	// check for other parameters that need to be specified
	if (!$description)
		createAngularReconstitutionForm("<B>ERROR:</B> Enter a brief description of the run");
	if (!$rundir)
		createAngularReconstitutionForm("<B>ERROR:</B> Enter an output directory");
	if (!$runname)
		createAngularReconstitutionForm("<B>ERROR:</B> Enter a run name");
	if (!$nvol)
		createAngularReconstitutionForm("<B>ERROR:</B> Enter the number of volumes that you wish to create using Angular Reconstitution");
	if ($nproc > 8)
		createMaxLikeAlignForm("<B>ERROR:</B> Cannot currently use more than 8 processors with Imagic parallelization");
	
	// make sure outdir ends with '/' and append run name
	if (substr($rundir,-1,1)!='/') $rundir.='/';
	$rundir = $rundir.$runname;

	// setup command
	$command ="bootstrappedAngularReconstitution.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	if ($clusterid) $command.="--clusterid=$clusterid ";
	elseif ($tsid) $command.="--templatestackid=$tsid ";
	$command.="--nvol=$nvol ";
	if ($scale) $command.="--scale ";
	if ($prealign) $command.="--prealign ";
	if (!$weight) $command.="--non_weighted_sequence ";
	if ($anginc) $command.="--ang_inc=$anginc ";
	if ($keep_ordered) $command.="--keep_ordered=$keep_ordered ";
	if ($filt3d) $command.="--3d_lpfilt=$filt3d ";
	if ($nref) $command.="--nref=$nref ";
	if ($usePCA) $command.="--PCA ";
	if ($numeigens) $command.="--numeigens=$numeigens ";
	if ($recalc) $command.="--recalculate_volumes ";
	if ($preftype) $command.="--preftype=$preftype ";
	if ($nproc && $nproc>1) $command.="--nproc=$nproc ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Run Bootstrapped Angular Reconstitution") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		
		if (!($user && $password)) createAngularReconstitutionForm("<B>ERROR:</B> Enter a user name and password");
		
		$sub = submitAppionJob($command,$rundir,$runname,$expId,'angrecon',False,False,False,$nproc);
		// if errors:
		if ($sub) createAngularReconstitutionForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("Bootstrapped Angular Reconstitution Run Params","Bootstrapped Angular Reconstitution Params");
		echo "<table width='600' class='tableborder' border='1'>";
			echo "<tr><td colspan='2'><br/>\n";
				echo "	<tr><td colspan='2'><b>Angular Reconstitution Command:</b><br />$command</td></tr>
						<tr><td>run id</td><td>$runname</td></tr>
						<tr><td>run directory</td><td>$rundir</td></tr> ";
				if ($clusterid) echo "	<tr><td>clustering stack id</td><td>$clusterid</td></tr>";
				elseif ($tsid) echo "	<tr><td>template stack id</td><td>$tsid</td></tr>";
				echo "	<tr><td>number of volumes</td><td>$nvol</td></tr>";
				if ($scale) {
					echo "	<tr><td>scale averages</td><td>YES</td></tr>";
				}
				else {
					echo "	<tr><td>scale averages</td><td>NO</td></tr>";
				}
				if ($prealign) {
					echo "	<tr><td>align averages</td><td>YES</td></tr>";
				}
				else {
					echo "	<tr><td>align averages</td><td>NO</td></tr>";
				}
				if ($weight) {
					echo "	<tr><td>weight sequence randomization</td><td>YES</td></tr>";
				}
				else {
					echo "	<tr><td>weight sequence randomization</td><td>NO</td></tr>";
				}
				echo "	<tr><td>angular search increment</td><td>$anginc</td></tr>
						<tr><td>keep % ordered images</td><td>$keep_ordered</td></tr>
						<tr><td>lowpass filter volumes</td><td>$filt3d &Aring;ngstroms</td></tr>
						<tr><td>num 3D references for alignment</td><td>$nref</td></tr>";
				if ($usePCA) {
					echo "	<tr><td>PCA</td><td>YES</td></tr>
							<tr><td>number Eigenimages</td><td>$numeigens</td></tr>";
					if ($recalc) {
						echo "	<tr><td>recalculate after PCA</td><td>YES</td></tr>";
					}
					else {
						echo "	<tr><td>recalculate after PCA</td><td>NO</td></tr>";
					}
				}
				else {
					echo "	<tr><td>PCA</td><td>NO</td></tr>";
				}
				echo "	<tr><td>Preference type</td><td>$preftype</td></tr>
						<tr><td>commit</td><td>$commit</td></tr>
			</table>\n";
		processing_footer();
	}
}
	
	
?>