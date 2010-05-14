<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";

$expId= $_GET['expId'];
$densityId= $_GET['densityId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId&densityId=$densityId";
$projectId=getProjectId();

$particle = new particledata();

$density = $particle->get3dDensityFromId($densityId);
$javascript = editTextJava();

processing_header("3d Density Volume Report", "3d Density Volume Report", $javascript);


// get updated description
if ($_POST['updateDesc'.$densityId]) {
	updateDescription('Ap3dDensityData', $densityId, $_POST['newdescription'.$densityId]);
	$density['description']=$_POST['newdescription'.$densityId];
}

# get list of png files in directory
$pngfiles=array();
$densitydir= opendir($density['path']);
while ($f = readdir($densitydir)) {
	if (eregi($density['name'].'.*\.png$',$f)) $pngfiles[] = $f;
}
sort($pngfiles);

    // display starting density
$j = "Density ID: $densityId";
$densitytable = apdivtitle($j);
foreach ($pngfiles as $snapshot) {
	$snapfile = $density['path'].'/'.$snapshot;
	$densitytable.= "<a border='0' href='loadimg.php?filename=$snapfile' target='snapshot'>";
	$densitytable.= "<img src='loadimg.php?s=120&filename=$snapfile' height='120'></a>\n";
}
$sym=$particle->getSymInfo($density['REF|ApSymmetryData|symmetry']);

# add edit button to description if logged in
$descDiv = ($_SESSION['username']) ? editButton($densityid, $density['description']) : $density['description'];

$densitytable.= "<br />\n";
$densitytable.= "<b>pixel size:</b> $density[pixelsize]<br />\n";
$densitytable.= "<b>box size:</b> $density[boxsize]<br />\n";
$densitytable.= "<b>symmetry:</b> $sym[symmetry]<br />\n";
$densitytable.= "<b>resolution:</b> $density[resolution]<br />\n";
$modelfile = $density['path']."/".$density['name'];
$modellink .= "<font size='-2'><a href='download.php?file=$modelfile'>\n";
$modellink .= "  <img src='../img/dwd_bt_off.gif' border='0' width='15' height='15' alt='download model'>\n";
$modellink .= "</a></font>\n";
$densitytable.= "<b>Filename:</b><br />$modelfile $modellink<br />\n";
$densitytable.= "<b>Description:</b><br />$descDiv<br />\n";

$densitytable.= "<b>History:</b><br />\n";
if ($density['REF|ApRctRunData|rctrun'])
	$densitytable .= "<A HREF='rctreport.php?expId=$expId&rctId="
		.$density['REF|ApRctRunData|rctrun']."'>RCT volume run #"
		.$density['REF|ApRctRunData|rctrun']."</A>\n";
elseif ($density['REF|ApRefineIterData|iterid'])
	$densitytable .= "<A HREF='reconreport.php?expId=$expId&reconId="
		.$density['refrun']."'>EMAN refinement run #"
		.$density['refrun']."</A>\n";
elseif ($density['pdbid'])
	$densitytable .= "<A HREF='http://www.rcsb.org/pdb/cgi/explore.cgi?pdbId="
		.$density['pdbid']."'> PDB id "
		.$density['pdbid']."&nbsp;<img src='img/external.png' BORDER='0' HEIGHT='10' WIDTH='10'>"
		."</A>\n";
elseif ($density['emdbid'])
	$densitytable .= "<A HREF='http://www.ebi.ac.uk/msd-srv/emsearch/atlas/"
		.$density['emdbid']."_visualization.html'> EMDB id "
		.$density['emdbid']."&nbsp;<img src='img/external.png' BORDER='0' HEIGHT='10' WIDTH='10'>"
		."</A>\n";
else
	$densitytable .= "<I>unknown</I>\n";
$densitytable.= "<br/><br/>\n";

$densitytable.= "<b>Initial Model:</b><br/>\n";
$densitytable.= "<A HREF='uploadmodel.php?expId=$expId&densityId=$densityId"
	."&pdbmod=$density[path]/$density[name]'>Upload Density file as an Initial Model</A><br/>\n";

echo $densitytable;

processing_footer();
exit;

?>
