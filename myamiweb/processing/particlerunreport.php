<?php
require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
//require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";

$expId = $_GET['expId'];
$runId = $_GET['rId'];

$particle = new particledata();

list($runparams) = $particle->getSelectionParams($runId);
$templateparams = $particle->getTemplateRunParams($runId);

processing_header("Particle run report","Particle report for $runparams[name]");

$particlestats = $particle->getStats($runId);
echo "<table cellspacing='1' cellpadding='2'><tr><td><span class='datafield0'>Total particles for $runparams[name]: </span></td><td>$particlestats[totparticles]</td></tr></table>\n";
//Report template run parameters
if (count($templateparams) > 0) {
	$template_fields = array('id', 'apix', 'description', 'range_start', 'range_end', 'range_incr');
	echo "<h4>Template images and parameters</h4>\n";
	echo "<table>";
	foreach($templateparams as $template){
		$templatepath=$template[path]."/".$template[tname];
		echo '<tr><td>';
			echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>";
			echo "<tr>\n";
				echo "<td colspan='2'><IMG alt='$templatepath' SRC='loadimg.php?filename=$templatepath&rescale=True' WIDTH='100'></td>\n";
			echo "</tr>\n";
			foreach($template_fields as $key) {
				if ($template[$key]) {
					echo "<tr>\n";
						echo "<td><span class='datafield0'>$key</span></td>";
						echo "<td>$template[$key]</td>";
					echo "</tr>\n";
				}
			}
			echo "</table>\n";
		echo "</td></tr>";
	}
	echo "</table>";
}

//Report selection run parameters
$title = "Selection parameters";
$exclude_fields = array('DEF_timestamp');
$particle->displayParameters($title,$runparams,$exclude_fields);

processing_footer();