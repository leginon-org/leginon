<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";

$defaultId=3956;
$defaultpreset='enn';
$sessionId=($_GET['expId']) ? $_GET['expId'] : $defaultId;
$preset=($_GET['preset']) ? $_GET['preset'] : $defaultpreset;
$viewsql=$_GET['vs'];

#$dir ='/usr/local/temp/';  
$dir = defined("TEMP_DIR") ? TEMP_DIR:"/tmp/";

$path = $dir . $sessionId . '/';

$fieldname = 'image shift';
$stats=false;
$imageshiftdata=$leginondata->getImageScopeXYValues($sessionId, $preset, $fieldname, $stats);

$xmlstr_top = <<< XML1
<MicroscopeImage xmlns="http://schemas.datacontract.org/2004/07/Fei.SharedObjects" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
    <microscopeData>
        <optics>
            <BeamShift xmlns:a="http://schemas.datacontract.org/2004/07/Fei.Types">
XML1;

$xmlstr_bottom = <<< XML2
            </BeamShift>
        </optics>
    </microscopeData>
</MicroscopeImage>
XML2;

if (!file_exists($path)) {
    mkdir($path, 0777, true);
}
foreach ($imageshiftdata as $datum) {
	$fileout = str_replace("mrc","xml",$datum['filename']);
	$fileout = $path . $fileout;
 
	$xmlstr_x = "\n                <a:_x>" . sprintf("%.5f",$datum['image_shift_x']*1e6) . "</a:_x>\n";
	$xmlstr_y = "                <a:_y>" . sprintf("%.6f",$datum['image_shift_y']*1e6) . "</a:_y>\n";

	$xmlstr = $xmlstr_top . $xmlstr_x . $xmlstr_y . $xmlstr_bottom;
	$xmls = new SimpleXMLElement($xmlstr);
	$xmls->asXml($fileout);

}

// Zip code from https://stackoverflow.com/questions/4914750/how-to-zip-a-whole-folder-using-php
// Get real path for our folder
$rootPath = realpath($path);

// Initialize archive object
$zip = new ZipArchive();
$zipfile = '/usr/local/temp/' . $sessionId . '.zip';
$zip->open($zipfile, ZipArchive::CREATE | ZipArchive::OVERWRITE);

// Initialize empty "delete list"
$filesToDelete = array();

// Create recursive directory iterator
/** @var SplFileInfo[] $files */
$files = new RecursiveIteratorIterator(
    new RecursiveDirectoryIterator($rootPath),
    RecursiveIteratorIterator::LEAVES_ONLY
);

$numfiles=0;
foreach ($files as $name => $file)
{
    // Skip directories (they would be added automatically)
    if (!$file->isDir())
    {
        // Get real and relative path for current file
        $filePath = $file->getRealPath();
        $relativePath = substr($filePath, strlen($rootPath) + 1);

        // Add current file to archive
        $zip->addFile($filePath, $relativePath);
	$numfiles += 1;

        // Add current file to "delete list"
        // delete it later cause ZipArchive create archive only after calling close function and ZipArchive lock files until archive created)
        if ($file->getFilename() != 'important.txt')
        {
            $filesToDelete[] = $filePath;
        }
    }
}

// Zip archive will be created only after closing object
$zip->close();
// Delete all files from "delete list"
#echo "Cleaning up ...<br>";
foreach ($filesToDelete as $file)
{
    unlink($file);
}
rmdir($path);

$sessionName = $leginondata->getSessionName($sessionId);
$archive_file_name = $sessionName . '_xml.zip';

header("Content-type: application/zip"); 
    header("Content-Disposition: attachment; filename=$archive_file_name"); 
    header("Pragma: no-cache"); 
    header("Expires: 0"); 
    readfile("$zipfile");

?>
