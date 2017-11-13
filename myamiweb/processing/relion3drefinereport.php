<?php
require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
//require_once "inc/util.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

$expId = $_GET['expId'];
$runId = $_GET['rId'];

$particle = new particledata();
list($runparams) = $particle->getSelectionParams($runId);
$templateparams = $particle->getTemplateRunParams($runId);

processing_header("Relion 3D Refine Report","Relion 3D Refine Report for $runparams[name]");

//echo pickingsummarytable($runId);

$particlestats = $particle->getStats($runId);
echo "<table cellspacing='1' cellpadding='2'><tr><td><span class='datafield0'>Total particles for $runparams[name]: </span></td><td>$particlestats[totparticles]</td></tr></table>\n";



echo '<a target="_blank" href="../ngl/webapp.php?expId=4062&filename=/gpfs/appion/cnegro/17jun23d/extract/relion3drefine21/run_half1_class001_unfil.mrc">Halfmap1</a><br>';

echo '<a target="_blank" href="../ngl/webapp.php?expId=4062&filename=/gpfs/appion/cnegro/17jun23d/extract/relion3drefine21/run_half2_class001_unfil.mrc">Halfmap2</a>';

# more display about the particles
	//echo "<h4>Particle Position Histograms</h4>\n";
	echo "<table cellspacing='1' cellpadding='2'><tr><td>";

	$imgwidth="75%";
		//echo '<a href="loadimg.php?rawgif=1&filename='.$runparams[path].'/PearsonCorrelation.gif"/>';
		//echo "<a href='loadimg.php?&filename=".$runparams[path]."/PearsonCorrelation.gif'/>";

		echo '<img border="0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/fsc.gif"/>';
		echo '</td><td>';
		echo '<img border="0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/XYcoordinates.gif"/>';
		echo '</td></tr>';
		echo '<tr><td>';
		echo '<img border="0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/EulerAngleDistribution.gif"/>';
		echo '</td><td>';
		echo '<img border="0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/ThreeDFSC.gif"/>';
		echo '</td></tr>';
		echo '<tr><td>';
		echo '<img border="0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/DefocusV.gif"/>';
		echo '</td><td>';
		echo '<img border="0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/DefocusU.gif"/>';
		echo '</td></tr>';
		echo '<tr><td>';
		echo '<img border="0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/SpearmanCorrelation.gif"/>';
		echo '<td>';
		echo '<img border="    0" style="width:'.$imgwidth.';" src="loadimg.php?rawgif=1&filename='.$runparams[path].'/PearsonCorrelation.gif">';
	echo "</td></tr></table>\n";

//Report selection run parameters
#$title = "Selection parameters";
#$exclude_fields = array('DEF_timestamp');
#$particle->displayParameters($title,$runparams,$exclude_fields,$expId);

processing_footer();
