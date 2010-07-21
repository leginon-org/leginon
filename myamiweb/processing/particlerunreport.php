<?php
require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
//require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

$expId = $_GET['expId'];
$runId = $_GET['rId'];

$particle = new particledata();

list($runparams) = $particle->getSelectionParams($runId);
$templateparams = $particle->getTemplateRunParams($runId);

processing_header("Particle run report","Particle report for $runparams[name]");

echo pickingsummarytable($runId);

$particlestats = $particle->getStats($runId);
echo "<table cellspacing='1' cellpadding='2'><tr><td><span class='datafield0'>Total particles for $runparams[name]: </span></td><td>$particlestats[totparticles]</td></tr></table>\n";
//Report template run parameters
if ($templateparams) {
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

$partdownlink .= "<font size='+1'><a href='downloadparticledata.php?expId=$expId&selectionId=$runId'>\n";
$partdownlink .= "  <img src='img/download_arrow.png' border='0' width='16' height='17' alt='download stack'>&nbsp;download particle data\n";
$partdownlink .= "</a></font><br/>\n";
echo $partdownlink;

echo "<h4>Particle Position Histograms</h4>\n";
echo "<table cellspacing='1' cellpadding='2'><tr><td>";

		echo "<a href='particlePositionGraph.php?expId=$expId&rId=$runId&haxis=xcoord&hg=1'>";
		echo "<img border='0' src='particlePositionGraph.php?expId=$expId&w=256&rId=$runId&haxis=xcoord&hg=1'>";
		echo "</td><td>";
		echo "<a href='particlePositionGraph.php?expId=$expId&rId=$runId&haxis=ycoord&hg=1'>";
		echo "<img border='0' src='particlePositionGraph.php?expId=$expId&w=256&rId=$runId&haxis=ycoord&hg=1'>";
echo "</td></tr></table>\n";
//Report selection run parameters
$title = "Selection parameters";
$exclude_fields = array('DEF_timestamp');
$particle->displayParameters($title,$runparams,$exclude_fields,$expId);

processing_footer();
