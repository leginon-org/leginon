<?
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require 'inc/viewer.inc';
require 'inc/xmldata.inc';


$xmldata = new xmldata(XML_DATA);

$imageId=$xmldata->getLastFilenameId();
$sessionId=$xmldata->getSessionId();
$filenames=$xmldata->getFilenames();

$viewer = new viewer();
$viewer->setImageId($imageId);
$viewer->setSessionId($sessionId);
$viewer->addFileSelector($filenames);
$javascript = $viewer->getJavascript();

$view1 = new view('Simple Viewer', 'v1');
$view1->setImageReportScript('imgreportxml.php');
$view1->setHistogramScript('imagehistogramxml.php');
$view1->setDownloadScript('downloadxml.php');
$view1->setImageScript('getimgxml.php');
$view1->setPresetScript('getpresetxml.php');
$view1->displayPTCLIcon(false);
$view1->displayTagIcon(false);
$view1->displayACEIcon(false);
$view1->displayTargetIcon(false);
$view1->displayExportLink(false);
$view1->setSize(512);

$viewer->add($view1);

$javascript .= $viewer->getJavascriptInit();
viewer_header('image viewer', $javascript, 'initviewer()');
?>
<a class="header" target="xmldata" href="test/viewerdata.xml">View XML data &raquo;</a>
<?$viewer->display();
viewer_footer();
?>
