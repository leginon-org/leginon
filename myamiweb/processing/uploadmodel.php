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
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$rescale=$_GET['rescale'];

	$particle = new particledata();

	// find out if rescaling an existing initial model
	if ($rescale) {
		$modelid=$_GET['modelid'];
		$modelinfo = $particle->getInitModelInfo($modelid);
	}

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($rescale) $formAction .="&rescale=TRUE&modelid=$modelid";
  
	processing_header($title,$heading);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","models",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
  
	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$res = ($_POST['res']) ? $_POST['res'] : '';
	$contour = ($_POST['contour']) ? $_POST['contour'] : '1.5';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.5';
	$model = ($_POST['model']) ? $_POST['model'] : '';
	$modelname = ($_POST['modelname']) ? $_POST['modelname'] : '';
	$description = $_POST['description'];
	$newmodel = ($_POST['newmodel']) ? $_POST['newmodel'] : $outdir.'/rescale.mrc';
  
	$syms = $particle->getSymmetries();
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	if (!$rescale) echo"<A HREF='emanJobGen.php?expId=$expId&modelonly=True'>[rescale an existing model]</A><P>\n";
	echo"<TABLE>
    <TR>
      <TD VALIGN='TOP'>
      <BR/>\n";
	if ($rescale) echo "
      <B>New Model Name:</B><BR>
      <INPUT TYPE='text' NAME='newmodel' VALUE='$newmodel' SIZE='50'><br />\n";
	else echo"
      <B>Model file name with path:</B><BR/>
      <INPUT TYPE='text' NAME='modelname' VALUE='$modelname' SIZE='50'><br />\n";
	echo"
      <P>
      <B>Model Description:</B><BR/>
      <TEXTAREA NAME='description' ROWS='3' COLS='65'>$description</TEXTAREA>
      </TD>
    </TR>
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
		echo "$symmetry[symmetry]<BR>
    <INPUT TYPE='hidden' NAME='sym' VALUE='$symid'>
    <B>Model Resolution:</B> $res<BR>
    <INPUT TYPE='hidden' NAME='res' VALUE='$res' SIZE='5'>
    <INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'><B>New Pixel Size</B> (originally $modelinfo[pixelsize])<BR>
    <INPUT TYPE='hidden' NAME='origapix' VALUE='$modelinfo[pixelsize]'>
    <INPUT TYPE='text' NAME='boxsize' SIZE='5' VALUE='$boxsize'><B>New Box Size</B> (originally $modelinfo[boxsize])<BR>\n";
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
		echo"
      </SELECT>
      <P>
      <INPUT TYPE='text' NAME='res' VALUE='$res' SIZE='5'> Model Resolution
      <BR>
      <INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'>
      Pixel Size <FONT SIZE='-2'>(in &Aring;ngstroms per pixel)</FONT>\n";
	}
	echo "
      <P>
      <B>Snapshot Options:</B>
      <BR>
      <INPUT TYPE='text' NAME='contour' VALUE='$contour' SIZE='5'> Contour Level
      <BR>
      <INPUT TYPE='text' NAME='zoom' VALUE='$zoom' SIZE='5'> Zoom
      <P>
      </TD>
    </TR>
    </TABLE>
  </TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <hr>
      <input type='submit' name='process' value='Just Show Command'>\n";
	if ($_SESSION['username']) echo "<input type='submit' name='process' value='Upload Model'>\n";
	echo "  <br />
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runUploadModel() {
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "uploadModel.py ";

	$contour=$_POST['contour'];
	$zoom=$_POST['zoom'];
	$session=$_POST['sessionname'];

	//make sure a model root was entered
	$model=$_POST['model'];
	if ($_POST['modelname']) $model=$_POST['modelname'];

	//make sure a apix was provided
	$apix=$_POST['apix'];
	if (!$apix) createUploadModelForm("<B>ERROR:</B> Enter the pixel size");
  
	// if rescaling, make sure there is a boxsize
	if ($_POST['newmodel']) {
		$model=$_POST['newmodel'];
		$boxsize=$_POST['boxsize'];
		$origapix=$_POST['origapix'];
		if (!$boxsize) createUploadModelForm("<B>ERROR:</B> Enter the final box size of the model");
	}

	if (!$model) createUploadModelForm("<B>ERROR:</B> Enter a root name of the model");
  
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createUploadModelForm("<B>ERROR:</B> Enter a brief description of the model");

	//make sure a resolution was provided
	$res=$_POST['res'];
	if (!$res) createUploadModelForm("<B>ERROR:</B> Enter the model resolution");

	// make sure a symmetry was selected
	$sym = $_POST['sym'];
	if (!$sym) createUploadModelForm("<B>ERROR:</B> Select a symmetry");

	// filename will be the runid if running on cluster
	$runid = basename($model);
	$runid = $runid.'.upload';

	if (!$_GET['modelid']) $command.="--file=$model ";
	$command.="--session=$session ";
	$command.="--apix=$apix ";
	$command.="--res=$res ";
	$command.="--symmetry=$sym ";
	if ($boxsize) $command.="--boxsize=$boxsize ";
	if ($contour) $command.="--contour=$contour ";
	if ($zoom) $command.="--zoom=$zoom ";
	if ($_POST['newmodel']) $command.="--modelid=$_GET[modelid] ";
	$command.="--description='$description' ";
	
	// submit job to cluster
	if ($_POST['process']=="Upload Model") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadModelForm("<B>ERROR:</B> You must be logged in to submit");

		submitAppionJob($command,$outdir,$runid,$expId,'uploadmodel',True,True);

		// check that upload finished properly
		$jobf = $outdir.'/'.$runid.'/'.$runid.'.appionsub.log';
		$status = "Model was uploaded";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while uploading, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Model Upload", "Model Upload");
		echo "$status\n";
	}

	else processing_header("UploadModel Command","UploadModel Command");
	
	// rest of the page
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>UploadModel Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>model name</TD><TD>$model</TD></TR>
	<TR><TD>symmetry ID</TD><TD>$sym</TD></TR>
	<TR><TD>apix</TD><TD>$apix</TD></TR>
	<TR><TD>res</TD><TD>$res</TD></TR>
	<TR><TD>contour</TD><TD>$contour</TD></TR>
	<TR><TD>zoom</TD><TD>$contour</TD></TR>
	<TR><TD>session</TD><TD>$session</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
	processing_footer();
}
?>
