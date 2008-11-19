<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require  "inc/particledata.inc";
require  "inc/processing.inc";
require  "inc/leginon.inc";
require  "inc/project.inc";

create3d0SummaryForm();

function create3d0SummaryForm($extra=False)	{
	// get session and experiment info
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	
	// create instance of class particledata
	$particle = new particledata();
	
	$reclassifieddata = $particle->getImagic3d0ReclassifiedModelsFromSessionId($expId);
	$norefdata= $particle->getImagic3d0NoRefModelsFromSessionId($expId);
	$models = array_merge($reclassifieddata, $norefdata);
	$nummodels = count($models);
	
	$javafunc="<script src='../js/viewer.js'></script>\n";
  	processing_header("Imagic 3d0 Summary","Imagic 3d0 Summary",$javafunc);
  	
	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";

	echo "<FORM NAME='viewerform' METHOD='POST' ACTION='$formAction'>\n";
	
	if (is_array($models) && $nummodels > 0)	{
		foreach ($models as $model)	{
			$imagic3d0Id = $model['DEF_id'];

			// check to see if initial model was created from reference-free classification or reclassification
			if ($model['REF|ApImagicReclassifyData|reclass'])  {
				$modelparams = $particle->getImagicReclassParamsFrom3d0($imagic3d0Id);
				$reclassnum = $modelparams['DEF_id'];
				$clsavgpath = $modelparams['path']."/".$modelparams['runname'];
				$classimgfile = $clsavgpath."/reclassified_classums_sorted.img";
				$classhedfile = $clsavgpath."/reclassified_classums_sorted.hed";
			}

			if ($model['REF|ApNoRefClassRunData|norefclass']) {
				$modelparams = $particle->getNoRefClassRunParamsFrom3d0($imagic3d0Id);
				$norefId = $modelparams['REF|ApNoRefRunData|norefRun'];
				$norefparams = $particle->getNoRefParams($norefId);
				$clsavgpath = $norefparams['path']."/".$modelparams['classFile'];
				$classimgfile = $clsavgpath.".img";
				$classhedfile = $clsavgpath.".hed";
			}
		

			// get 3 initial projections for angular reconstitution associated with model		
			$projections = $model['projections'];
			$projections = explode(";", $projections);
			$projectiontable = "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'><tr>\n";
			$projectiontable.= "<td colspan='3'><b> 3 Initial Projections Used in Angular Reconstitution </b></td></tr><tr>";
			foreach ($projections as $key => $projection) {
				$num = $key + 1;
				$image = $projection - 1; // Imagic numbering system starts with 1 instead of 0
				$projectiontable.= "<td colspan='1' align='center' valign='top'>";
				$projectiontable.= "<img src='getstackimg.php?hed=$classhedfile
					&img=$classimgfile&n=".$image."&t=80&b=1&uh=0'><br/>\n";
				$projectiontable.= "<i>projection $num</i></td>\n";
			}
			$projectiontable.= "</tr><tr><td colspan='3' bgcolor='#bbffbb'>";
			$projectiontable.= "<a href='viewstack.php?file=$classimgfile&expId=$expId&reclassId=$reclassnum'>";
			$projectiontable.= "View all class averages used to create model</a>";
			$projectiontable.= "</td></tr></table>\n<BR/>";
			echo $projectiontable;

			echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";

			// get list of png files in directory
			$pngfiles = array();
			$modeldir = opendir($model['path']."/".$model['runname']);
			while ($f = readdir($modeldir)) {
				if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;

			}
			sort($pngfiles);

			
			// display starting models
			echo "<tr><TD COLSPAN=8>\n";
			$modelvals="$model[DEF_id]|--|$model[path]/$model[runname]|--|$model[name]|--|$model[boxsize]|--|$model[symmetry]";
			echo "<input type='RADIO' NAME='model' VALUE='$modelvals' ";
			
			// check if model was selected
			if ($model['DEF_id']==$minf[0]) echo " CHECKED";
			echo ">\n";
			
			echo"Use ";
			echo"Model ID: <b>$model[DEF_id]</b>\n";
		/*	echo "<input type='BUTTON' NAME='rescale' VALUE='Rescale/Resize this model' onclick=\"parent.
			     location='uploadmodel.php?expId=$expId&rescale=TRUE&imagic3d0id=$model[DEF_id]'\"><BR>\n";
		*/

			// display all .png files in model directory
			echo "<tr>";
			foreach ($pngfiles as $snapshot) {
				$snapfile = $model['path'].'/'.$model['runname'].'/'.$snapshot;
				echo "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'>
					<IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
			}

			// display info about each model run
			echo "</tr>\n";
			echo"<tr><TD COLSPAN=8>description: $model[description]</td></tr>\n";
			echo"<tr><TD COLSPAN=8>path: $model[path]/$model[runname]/$model[name]</td></tr>\n";
			echo"<tr><td>pixel size:</td><td><b>$model[pixelsize]</b></td>
			     <td>box size:</td><td><b>$model[boxsize]</b></td>
			     <td>symmetry:</td><td><b>$model[symmetry]</b></td>
			     <td># class averages used:</td><td><b>$model[num_classums]</b></td></tr>\n";
			echo"<tr><td>Automask dimension parameter:</td><td><b>$model[amask_dim]</b></td>
			     <td>Automask low-pass parameter:</td><td><b>$model[amask_lp]</b></td>
			     <td>Automask sharpness parameter:</td><td><b>$model[amask_sharp]</b></td>
			     <td>Automask thresholding parameter:</td><td><b>$model[amask_thresh]</b></td></tr>\n";
			echo"<tr><td>Increment euler angle search:</td><td><b>$model[euler_ang_inc]</b></td>
			     <td>Increment forward projections:</td><td><b>$model[forw_ang_inc]</b></td>
			     <td>Hamming window:</td><td><b>$model[ham_win]</b></td>
			     <td>Object size as fraction of image size:</td><td><b>$model[obj_size]</b></td></tr>\n";
			echo "</TABLE><BR/><BR/>\n";
			echo "<P>\n";
		}
	}
	
	echo "</FORM>\n";
	processing_footer();
	exit;
}



?>
