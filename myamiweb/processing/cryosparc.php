<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";
// --- Set  experimentId
$expId = $_GET['expId'];
if (!is_numeric($expId) || $expId == 0) {
	// special case for uploading images to a new session coming from a known project
	$projectId = $_GET['projectId'];
	checkProjectAccessPrivilege($projectId);
} else {
	checkExptAccessPrivilege($expId,'data');
	$projectId = getProjectId();
}
$projectdata = new project();
$sessiondata=getSessionList($projectId,$expId);
$sessioninfo=$sessiondata['info'];
$sessions=$sessiondata['sessions'];
$currentproject = $projectdata->getProjectInfo($projectId);
$presets=$sessiondata['presets'];
$outDir = getBaseAppionPath($sessioninfo).'/csLIVE/';
processing_header("Appion cryoSPARC", "cryoSPARC");
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST) {
    runProgram();
}
// CREATE FORM PAGE
else {
    if ($_GET['delId']) {
        delete($_GET['delId']);
    }
    elseif ($_GET['id']) {
        display($_GET['id']);
    }
    else {
        createForm();
    }
}

// CREATE FORM PAGE
function createForm($extra=false) {
    if ($extra) {
        echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
    }
    if (privilege('groups') > 3 ){
        echo"<FORM NAME='viewerform' method='POST'>\n";
        echo"<p>Please enter cryoSPARC project and job id for a cryoSPARC 3D refinement job.</p>
        <TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
        <tr>
        <td>";
        //echo "<label for='hosts'>Select a host: </label>";
        echo "<select id='hosts' name='hosts' >";
        global $CRYOSPARC_HOSTS;
        foreach ($CRYOSPARC_HOSTS as $array) {
        	foreach($array as $key => $value)
        		echo "<option value='".$value."'>".$key." - ".$value."</option>";
        }
        
        echo "</select>";
        echo "</td><td>";
        echo "<label for='projectId'>Project ID: </label>";
        echo "<input type='text' id='project' name='projectId' size='6'>";
        echo "</td>
        <td>";
        echo "<label for='jobId'>Job ID: </label>";
        echo "<input type='text' id='job' name='jobId' size='6'>";
        echo "</td>
        <td>
        <input type='submit' value='Submit'>
        </td>
    	</tr>
    	</table>
        </form>\n";
    }
    else {
        echo "<p>Administration privileges is needed to add new cryoSPARC job. Please ask an Administrator to add cryoSPARC job, if needed.</p>";
    }
    $particle = new particledata();
    $expId = $_GET['expId'];
    $jobs = $particle->getCryosparcJobs($expId);
    if ($jobs) {
        echo "<h3>Available CryoSPARC Jobs</h3>";
        echo"<TABLE BORDER=1 CLASS=tableborder CELLPADDING=15>
        <tr>
		<th>Host IP</th>
        <th>Project ID</th>
        <th>Job ID</th>
        <th></th>
        <th></th>
        </tr>";
        $phpself = $_SERVER['PHP_SELF'];
        foreach ($jobs as $job){
            $id = $job[id];
            echo "<tr>
			<td>$job[IP]</td>
            <td>$job[projectId]</td>
            <td>$job[jobId]</td>
            <td><a href='$phpself?expId=$expId&id=$id'>Summary</a></td>
            <td><a href='$phpself?expId=$expId&delId=$id'>Delete</a></td>
            </tr>";
        }
        echo "</table>";
    }
}

$class_info = ""; 
// --- parse data and process on submit
function runProgram() {
    
    /* *******************
     PART 1: Get variables
     ******************** */
    $expId = $_GET['expId'];
    $projectId = $_POST['projectId'];
    $jobId = $_POST['jobId'];
    $host = $_POST['hosts'];
    if (!$projectId || !$jobId){
        createForm("Please provide a valid cryoSPARC project and job id");
        exit;
    }
    $manager = new MongoDB\Driver\Manager("mongodb://".$host.":".CRYOSPARC_PORT);
    $query = new MongoDB\Driver\Query(array('project_uid' => "$projectId", 'job_uid' => "$jobId"));
    $cursor = $manager->executeQuery('meteor.events', $query);
    $results = $cursor->toArray();
    if (!$results){
        createForm("Could not find cryoSPARC project '$projectId' with job id '$jobId'");
        exit;
    }
    $particle = new particledata();
    $id = $particle->insetCryosparcJob($expId, $projectId, $jobId, $host);
    $my_array = display($id);
    if ($_SESSION['loggedin']) {
    	global $outDir;
    	$processhost = getHosts()[0]['host'];
    	$user = $_SESSION['username'];
    	$pass = $_SESSION['password'];
    	$cmd = "mkdir -p ".$outDir;
    	$cmd .= "; cd ".$outDir;
    	foreach ($my_array as $key => $value) {
    		$cmd .= "; wget ".$value." -O ".$key;
    	}
    	global $class_info;
    	if ($class_info) {
    		$cmd .= "; echo ".$class_info." > class_info";
    	}
    	$r = exec_over_ssh($processhost, $user, $pass, $cmd, true);
    	echo "<h4>Saved files at ".$outDir."</h4>";
    }
    
}

function display($id) {
    
    $particle = new particledata();
    $job = $particle->getCryosparcJobs($_GET['expId'], $id);
    $manager = new MongoDB\Driver\Manager("mongodb://".$job[0][IP].":".CRYOSPARC_PORT);
    $query = new MongoDB\Driver\Query(array('project_uid' => $job[0][projectId], 'job_uid' => $job[0][jobId]));
    $cursor = $manager->executeQuery('meteor.events', $query);
    $results = $cursor->toArray();
    $out_text = '';
    $fcs = '';
    $classes = '';
    $box_size = '';
    $pixel_size = '';
    $nparticles = '';
    foreach ($results as $result){
        if (strpos($result->text, "FSC Iteration") !== false){
            $fcs = $result;
        }
        elseif (strpos($result->text, "2D classes for iteration") !== false){
        	$classes = $result;
        }
        elseif (strpos($result->text, "2D classes for iteration") !== false){
        	$classes = $result;
        }
        elseif (strpos($result->text, "Particle box size:") !== false){
        	$box_size = $result;
        }
        elseif (strpos($result->text, "Particle pixel size:") !== false){
        	$pixel_size = $result;
        }
        elseif (strpos($result->text, "Found ") !== false){
        	$nparticles = $result;
        }
        $out_text .= $result->text.'<br>';
    }
    if ($fcs) {
	    echo "<table border=1 CLASS=tableborder CELLPADDING=15>
	        <tr><td>";
	
	    echo '
	    <!-- NGL -->
	    <script src="../ngl/js/ngl.js"></script>
	
	    <!-- UI -->
	    <script src="../ngl/js/lib/signals.min.js"></script>
	    <script src="../ngl/js/lib/tether.min.js"></script>
	    <script src="../ngl/js/lib/colorpicker.min.js"></script>
	    <script src="../ngl/js/ui/ui.js"></script>
	    <script src="../ngl/js/ui/ui.extra.js"></script>
	    <script src="../ngl/js/ui/ui.ngl.js"></script>
	    <script src="../ngl/js/gui.js"></script>
	
	    <!-- EXTRA -->
	    <script src="../ngl/js/plugins.js"></script>
	
	    <script>
	        NGL.cssDirectory = "../ngl/css/";
	        var stage;
	        document.addEventListener( "DOMContentLoaded", function(){
	            stage = new NGL.Stage("viewport");
	                
	            var oReq = new XMLHttpRequest();    
	            
	            oReq.open("GET", "../proxy.php?csurl=http://'.CRYOSPARC.':39000/download_result_file/'.$job[0][projectId].'/'.$job[0][jobId].'.volume.map", true);
	            oReq.responseType = "arraybuffer";            
	            oReq.onload = function(oEvent) {
	              var blob = new Blob([oReq.response],  { type: "application/octet-binary"} );
	              var filename = "'.$job[0][jobId].'";
	              stage.loadFile(blob, {ext: "mrc", name: filename}).then(function (component) {
	            	  component.addRepresentation("surface");
	            	  component.autoView();
	            	});
	              
	            };
	            oReq.send();            
	            } );            
	
	    </script>
	    <div id="viewport" style="width:500px; height:300px;"></div>';
	    echo "<p style='text-align:center'><a href='http://".$job[0][IP].":39000/download_result_file/".$job[0][projectId]."/".$job[0][jobId].".volume.map'>Download Map</a></p>";
	    echo "</td><td><img src='http://".$job[0][IP].":39000/file/".$fcs->imgfiles[0]->fileid."'>";
	    echo "</td></tr></table>";
	    $return_array = array("fsc.png"=>"http://".$job[0][IP].":39000/file/".$fcs->imgfiles[0]->fileid);
    }
    else{
    	echo "<table border=1 CLASS=tableborder CELLPADDING=15>
	        <tr><td>";
    	echo "<img width='100%' src='http://".$job[0][IP].":39000/file/".$classes->imgfiles[0]->fileid."'>";
    	echo "</td></tr></table>";
    	$return_array = array("2dclasses.png"=>"http://".$job[0][IP].":39000/file/".$classes->imgfiles[0]->fileid);
    	global $class_info;
    	$class_info =  $box_size->text.$pixel_size->text.$nparticles->text;
    	$class_info =  str_replace("\n", "\t==", $class_info);
    }
    echo "<h1>CryoSPARC Output</h1>"; 
    echo $out_text;
    return $return_array;
}

function delete($id) {
    $particle = new particledata();
    $particle->deleteCryosparcJob($_GET['expId'], $id);
    createForm();
}

processing_footer();
?>