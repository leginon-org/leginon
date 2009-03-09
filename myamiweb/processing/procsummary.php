<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *  Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";

$leginondata = new leginondata();
$particle = new particledata();

processing_header("Appion Data Processing Summary", "Appion Data Processing Summary");

$totSessions = $leginondata->getTotalSessions();
$totImgs = $leginondata->getTotalImgs();
echo "<b>Total Sessions:</b> ";
echo commafy($totSessions);
echo "<br />\n";
echo "<b>Total Images:</b> ";
echo commafy($totImgs);
echo "<br />\n";

$aceinfo = array();
$acestats = $particle->getTotalAceStats();
$runs = $acestats['runs'];
$imgs = $acestats['img'];
$conf = $acestats['conf'];
$sess = $acestats['sessions'];

$aceinfo['Total ACE runs'] = commafy($runs);
$aceinfo['Sessions with Processing'] = commafy($sess);
$aceinfo['Sessions with Processing'] .= " (".round($sess/$totSessions*100)."%)";
$aceinfo['Total Processed Images'] = commafy($imgs);
$aceinfo['Total Processed Images'] .= " (".round($imgs/$totImgs*100)."%)";
$aceinfo['Imgs w/ Conf > 0.8'] = commafy($conf);
$aceinfo['Imgs w/ Conf > 0.8'] .= " (".round($conf/$imgs*100)."%)";
$particle->displayParameters("ACE Info", $aceinfo,array(),$expId);

echo "<br />\n";

$totalPrtls = $particle->getSloppyTotalParticleStats();
$prtlinfo = array();
$runs = $totalPrtls['runs'];
$dog = $totalPrtls['dog'];
$manual = $totalPrtls['manual'];
$tilt = $totalPrtls['tilt'];
$template = $runs-$dog-$manual-$tilt;
$particles = $totalPrtls['particles'];
$avgp = $particles/$runs;
$sess = $totalPrtls['sessions'];
$imgs = $totalPrtls['imgs'];

$prtlinfo['Total Selection Runs'] = commafy($runs);
$prtlinfo['Total TemplatePicker Runs'] = commafy($template);
$prtlinfo['Total TemplatePicker Runs'] .= " (".round($template/$runs*100)."%)";
$prtlinfo['Total DOGPicker Runs'] = commafy($dog);
$prtlinfo['Total DOGPicker Runs'] .= " (".round($dog/$runs*100)."%)";
$prtlinfo['Total ManualPicker Runs'] = commafy($manual);
$prtlinfo['Total ManualPicker Runs'] .= " (".round($manual/$runs*100)."%)";
$prtlinfo['Total TiltPicker Runs'] = commafy($tilt);
$prtlinfo['Total TiltPicker Runs'] .= " (".round($tilt/$runs*100)."%)";
$prtlinfo['Sessions with Processing'] = commafy($sess);
$prtlinfo['Sessions with Processing'] .= " (".round($sess/$totSessions*100)."%)";
$prtlinfo['Total Processed Images'] = commafy($imgs);
$prtlinfo['Total Processed Images'] .= " (".round($imgs/$totImgs*100)."%)";
$prtlinfo['Total Selected Particles'] = commafy($particles);
$prtlinfo['Avg Prtl/Run'] = commafy(round($avgp));
$particle->displayParameters("Particle Selection Info",$prtlinfo,array(),$expId);

echo "<br />\n";
$totalStacks = $particle->getSloppyTotalStackStats();
$stacks = $totalStacks['stacks'];
$particles = $totalStacks['particles'];
$avgp = $particles/$stacks;

$stackinfo = array();
$stackinfo['Total Stacks'] = commafy($stacks);
$stackinfo['Total Particles'] = commafy($particles);
$stackinfo['Avg Prtl/Stack'] = commafy(round($avgp));
$particle->displayParameters("Stack Info",$stackinfo,array(),$expId);

echo "<br />\n";
$totalRecons = $particle->getSloppyTotalReconStats();
$particles = $totalRecons['particles'];
$runs = $totalRecons['runs'];
$iters = $totalRecons['iter'];

$reconinfo = array();
$reconinfo['Total Recons'] = commafy($runs);
$reconinfo['Total Iterations'] = commafy($iters);
$reconinfo['Total Classified Particles'] = commafy($particles);
$particle->displayParameters("Recon Info",$reconinfo,array(),$expId);

echo "<br />\n";
$totalTemplates = $particle->getTotalTemplates();
$totalModels = $particle->getTotalModels();
$templatemodelinfo = array();
$templatemodelinfo['Total Templates'] = commafy($totalTemplates['templates']);
$templatemodelinfo['Total Initial Models'] = commafy($totalModels['models']);
$particle->displayParameters("Templates/Models",$templatemodelinfo,array(),$expId);

processing_footer();
?>
