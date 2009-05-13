<?php
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";


$templates=$leginondata->getTemplates();
$datadrives= array('data00', 'data07', 'data09', 'data11', 'data13', 'data15',
'data06', 'data08', 'data10', 'data12', 'data14', 'data16');
$filenames=array();
foreach ($templates as $f) {
    $filename = $f['name'];
    if (!file_exists($filename)) {
      foreach ($datadrives as $drive) {
        $nfile=ereg_replace('data..', $drive, $filename);
        if (file_exists($nfile)) {
          $filename=$nfile; 
          break;  
        }
      }
    }
    if (file_exists($filename)) {
			$filename=array('id'=>$filename, 'name'=>$filename);
			if (!in_array($filename, $filenames)) {
				$filenames[]=$filename;
			}
		}
}
$viewer=new viewer();
$sessionId=10;
$viewer->setSessionId($sessionId);
$viewer->setImageId($imageId);
$viewer->addFileSelector($filenames);
$viewer->setNbViewPerRow('1');
$pl_refresh_time=".5";
$viewer->addPlaybackControl($pl_refresh_time);
$playbackcontrol=$viewer->getPlaybackControl();
$javascript = $viewer->getJavascript();

$view1 = new view('Main View', 'v1');

$view1->setControl();
$view1->displayCloseIcon(false);
$view1->displayInfoIcon(false);
$view1->displayFFTIcon(false);
$view1->displayScaleIcon(false);
$view1->displayTargetIcon(false);
$view1->displayAdjustLink(false);
$view1->displayPresets(true);
$view1->displayAceIcon(false);
$view1->displayTagIcon(false);
$view1->displayComment(false); 
$view1->displayHideBt(false); 
$view1->displayNextBt(false); 
$view1->displayExemplarBt(false); 
$view1->displayDownloadIcon(false);
$view1->addMenuItems($playbackcontrol);
$view1->setDataTypes($datatypes);
$view1->displayPTCLIcon(false);
$view1->setSize(256);
$view1->setImageScript('getimgfile.php');
$view1->setPresetScript('getpresetfile.php');
$viewer->add($view1);


$javascript .= $viewer->getJavascriptInit();
viewer_header('image viewer', $javascript, 'initviewer()');
$viewer->display();
viewer_footer();
?>
