<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once 'inc/viewer.inc';
require_once 'inc/login.inc';
require_once 'inc/xmldata.inc';


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
$view1->displayInfoIcon(false);
$view1->setSize(512);

$viewer->add($view1);

$javascript .= $viewer->getJavascriptInit();
login_header('image viewer', $javascript, 'initviewer()');

echo '<a class="header" href="'.BASE_URL.'test/checkwebserver.php"> [Troubleshoot] </a>';

?>
<a class="header" target="xmldata" href="test/viewerdata.xml">View XML data &raquo;</a>
<?php
$viewer->display();
login_footer();
?>
