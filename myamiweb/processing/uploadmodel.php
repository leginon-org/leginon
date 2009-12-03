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
	runUploadModel();
}

// Create the form page
else {
	createUploadModelForm();
}

function createUploadModelForm($extra=false, $title='UploadModel.py Launcher', $heading='Upload an Initial Model') {
	$particle = new particledata();
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$rescale=$_GET['rescale'];
	if ($_GET['densityId']) {
		$densityid = $_GET['densityId'];
		$densityinfo = $particle->get3dDensityInfo($densityid);
		$apix = $densityinfo['pixelsize'];
		$res = $densityinfo['resolution'];
		$boxsize = $densityinfo['boxsize'];
		$description = $densityinfo['description'];
	} else {
	// find out if rescaling an existing initial model
		if ($rescale) {
			$modelid=$_GET['modelid'];
			$modelinfo = $particle->getInitModelInfo($modelid);
			$_POST['apix'] = $modelinfo['pixelsize'];
			$_POST['res'] = $modelinfo['resolution'];
			$_POST['sym'] = $modelinfo['REF|ApSymmetryData|symmetry'];
		} else {
			if ($_GET['apix'])
				$_POST['apix'] = $_GET['apix'];
			if ($_GET['sym'])
				$_POST['sym'] = $_GET['sym'];
		}
	}
	

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($rescale) $formAction .="&rescale=TRUE&modelid=$modelid";
	if ($densityid) $formAction .="&densityId=$densityid";
  
	processing_header($title,$heading,False,True);
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
		$outdir=ereg_replace("rawdata","models",$outdir);
		$outdir=$outdir."/accepted";
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
  
	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : $apix;
	$res = ($_POST['res']) ? $_POST['res'] : $res;
	$boxsize = ($_POST['boxsize']) ? $_POST['boxsize'] : $boxsize;
	$contour = ($_POST['contour']) ? $_POST['contour'] : '1.5';
	$mass = ($_POST['mass']) ? $_POST['mass'] : '';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.0';
	$model = ($_POST['model']) ? $_POST['model'] : '';
	$modelname = ($_POST['modelname']) ? $_POST['modelname'] : '';
	$description = ($_POST['description']) ? $_POST['description']: $description;
	$newmodel = ($_POST['newmodel']) ? $_POST['newmodel'] : $outdir.'/rescale.mrc';
  
	$syms = $particle->getSymmetries();
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	if (!$densityid &&!$rescale) echo"<A HREF='emanJobGen.php?expId=$expId&modelonly=True'>[rescale an existing model]</A><P>\n";
	echo"<table>
    <TR>
      <TD VALIGN='TOP'>";
	if ($rescale) echo "
      <br>\n
      <B>New Model Name:</B><br>
      <INPUT TYPE='text' NAME='newmodel' VALUE='$newmodel' SIZE='50'><br />\n";
	else {
		if ($densityid) {
			echo "<b> 3D density id: $densityid<b><br/>\n";
		} else {
			echo"<b>Model file name with path:</b><br />\n";
			echo "<INPUT TYPE='text' NAME='modelname' VALUE='$modelname' SIZE='50'><br />\n";
		}
	}
	echo"
      <P>
      <B>Model Description:</B><br>
      <TEXTAREA NAME='description' ROWS='3' COLS='65'>$description</TEXTAREA>
      </TD>
    </tr>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>
      <P>
      <B>Model Symmetry:</B>\n";
	if ($rescale) {
		$symid=$modelinfo['REF|ApSymmetryData|symmetry'];
		$symmetry=$particle->getSymInfo($symid);
		$res = $modelinfo['resolution'];
		$apix = ($_POST['apix']) ? $_POST['apix'] : $modelinfo['pixelsize'];
		$boxsize = ($_POST['boxsize']) ? $_POST['boxsize'] : $modelinfo['boxsize'];
		echo "$symmetry[symmetry]<br>
    <INPUT TYPE='hidden' NAME='sym' VALUE='$symid'>
    <B>Model Resolution:</B> $res<br>
    <INPUT TYPE='hidden' NAME='res' VALUE='$res' SIZE='5'>
    <INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'><B>New Pixel Size</B> (originally $modelinfo[pixelsize])<br>
    <INPUT TYPE='hidden' NAME='origapix' VALUE='$modelinfo[pixelsize]'>
    <INPUT TYPE='text' NAME='boxsize' SIZE='5' VALUE='$boxsize'><B>New Box Size</B> (originally $modelinfo[boxsize])<br>\n";
	}
	else {
		echo"
      <SELECT NAME='sym'>
      <OPTION VALUE=''>Select One</OPTION>\n";
		foreach ($syms as $sym) {
			echo "<OPTION VALUE='$sym[DEF_id]'";
			if ($sym['DEF_id']==$_POST['sym']) echo " SELECTED";
			echo ">$sym[symmetry]";
			if ($sym['symmetry']=='C1') echo " (no symmetry)";
			echo "</OPTION>\n";
		}
		echo "</select>\n";
		echo "<P>\n";
		echo "<INPUT TYPE='text' NAME='res' VALUE='$res' SIZE='5'> Model Resolution\n";
 		echo "<br />\n";
 		echo "<INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'>\n";
 		echo "Pixel Size <FONT SIZE='-2'>(in &Aring;ngstroms per pixel)</FONT>\n";
		if ($densityid) {
			echo "<br />\n";
			echo "<INPUT TYPE='text' NAME='boxsize' SIZE='5' VALUE='$boxsize'>\n";
			echo "Square Box Size <FONT SIZE='-2'>(in pixels)</FONT>\n";
		}
	}
	echo "
      <P>
      <B>Snapshot Options:</B>
      <br>
      <INPUT TYPE='text' NAME='contour' VALUE='$contour' SIZE='5'> Contour Level
      <br>
      <INPUT TYPE='text' NAME='mass' VALUE='$mass' SIZE='5'> Mass (in kDa)
      <br>
      <INPUT TYPE='text' NAME='zoom' VALUE='$zoom' SIZE='5'> Zoom
      <P>
      </TD>
    </tr>
    </table>
  </TD>
  </tr>
  <TR>
    <TD ALIGN='CENTER'>
      <hr>
	";
	echo getSubmitForm("Upload Model");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runUploadModel() {
	$expId = $_GET['expId'];
	$modelid = $_GET['modelid'];
	$densityid = $_GET['densityId'];
	
	$outdir = $_POST['outdir'];

	$command = "uploadModel.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";

	$boxsize=$_POST['boxsize'];
	$contour=$_POST['contour'];
	$mass=$_POST['mass'];
	$zoom=$_POST['zoom'];
	$session=$_POST['sessionname'];

	$model=$_POST['model'];
	if ($_POST['modelname']) $model=$_POST['modelname'];
	//make sure a model root was entered if upload an independent file
	if (!$modelid && !$densityid && !$model) createUploadModelForm("<B>ERROR:</B> Enter a root name of the model");

	//make sure a apix was provided
	$apix=$_POST['apix'];
	if (!$apix) createUploadModelForm("<B>ERROR:</B> Enter the pixel size");
  
	// if rescaling, make sure there is a boxsize
	if ($_POST['newmodel']) {
		$model=$_POST['newmodel'];
		$origapix=$_POST['origapix'];
		if (!$boxsize) createUploadModelForm("<B>ERROR:</B> Enter the final box size of the model");
	}

	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createUploadModelForm("<B>ERROR:</B> Enter a brief description of the model");

	//make sure a resolution was provided
	$res=$_POST['res'];
	if (!$res) createUploadModelForm("<B>ERROR:</B> Enter the model resolution");

	// make sure a symmetry was selected
	$sym = $_POST['sym'];
	if (!$sym) createUploadModelForm("<B>ERROR:</B> Select a symmetry");

	// set runname according to upload type
	$runname = getTimestring();
	if ($densityid) {
		$command.="--densityid=$densityid ";
		$runname = density.$densityid."_".$runname;
	} else {
		if ($modelid) {
			$command.="--modelid=$modelid ";
			$runname = density.$modelid."_".$runname;
		} else {
			$command.="--file=$model ";	
			$basename = basename($model);
			$prefixnames = explode("-",$basename);
			if (count($prefixnames) > 1) {
				$runname = $prefixnames[0]."_".$runname;
			} else {
				$runname = "file"."_".$runname;
			}
		}
	}

	$command.="--session=$session ";
	$command.="--runname=$runname ";
	$command.="--apix=$apix ";
	$command.="--res=$res ";
	$command.="--symmetry=$sym ";
	if ($boxsize) $command.="--boxsize=$boxsize ";
	if ($contour) $command.="--contour=$contour ";
	if ($mass) $command.="--mass=$mass ";
	if ($zoom) $command.="--zoom=$zoom ";
	$command.="--description=\"$description\" ";
	
	// submit job to cluster
	if ($_POST['process']=="Upload Model") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadModelForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'uploadmodel',False);
		// if errors:
		if ($sub) createUploadModelForm("<b>ERROR:</b> $sub");
		exit;
	}

	else processing_header("UploadModel Command","UploadModel Command");
	
	// rest of the page
	echo"
	<table class='tableborder' width='600' border='1'>
	<tr><td colspan='2'>
	<B>UploadModel Command:</B><br>
	$command
	</td></tr>
	<tr><td>old model id</td><td>$modelid</td></tr>
	<tr><td>3dDensity id</td><td>$densityid</td></tr>
	<tr><td>model name</td><td>$model</td></tr>
	<tr><td>symmetry ID</td><td>$sym</td></tr>
	<tr><td>apix</td><td>$apix</td></tr>
	<tr><td>res</td><td>$res</td></tr>
	<tr><td>contour</td><td>$contour</td></tr>
	<tr><td>zoom</td><td>$contour</td></tr>
	<tr><td>session</td><td>$session</td></tr>
	<tr><td>description</td><td>$description</td></tr>
	</table>\n";
	processing_footer();
}
?>
