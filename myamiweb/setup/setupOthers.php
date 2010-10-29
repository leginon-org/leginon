<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once('../inc/formValidator.php');

	setupUtils::checkSession();
	$update = false;	
	if(!empty($_SESSION['loginCheck'])){
		require_once(CONFIG_FILE);
		$update = true;
	}
	
	if($_POST){

		$validator = new formValidator();
		
		if($_POST['enable_cache'] == 'true'){
			$validator->addValidation("cache_path", $_POST['cache_path'], "abs_path");
			$validator->addValidation("cache_path", $_POST['cache_path'], "path_exist");
			$validator->addValidation("cache_path", $_POST['cache_path'], "folder_permission");
		}
		
		$validator->addValidation("mrc2any", $_POST['mrc2any'], "abs_path");
		
		if($_POST['processing'] == 'true'){
						
			$validator->addValidation("def_processing_prefix", $_POST['def_processing_prefix'], "minlen=1");
			$validator->addValidation("def_processing_prefix", $_POST['def_processing_prefix'], "maxlen=10");
			$validator->addValidation("def_processing_prefix", $_POST['def_processing_prefix'], "alpha");
			
			$validator->addValidation("defaultcs", $_POST['defaultcs'], "float");
			$validator->addValidation("temp_images_dir", $_POST['temp_images_dir'], "abs_path");
			$validator->addValidation("temp_images_dir", $_POST['temp_images_dir'], "path_exist");
			$validator->addValidation("temp_images_dir", $_POST['temp_images_dir'], "folder_permission");
			
			if(!empty($_POST['processing_hosts'])){

				foreach ($_POST['processing_hosts'] as $processingHost){
					$validator->addValidation("host", $processingHost['host'], "req", "Cluster host name can not be empty.");
					$validator->addValidation("host", $processingHost['host'], "remoteServer", "Local cluster does not exist. Please make sure the cluster exists.");
					$validator->addValidation("nproc", $processingHost['nproc'], "req", "Max number of processors per node can not be empty.");
					$validator->addValidation("nproc", $processingHost['nproc'], "num", "Please provide a numeric input for maximum number of processors per node.");
				}
			}

			if(!empty($_POST['cluster_configs'])){

				foreach ($_POST['cluster_configs'] as $clusterConfig){
					$fileLocation = "../processing/".$clusterConfig.".php";
					$validator->addValidation("cluster_configs", $fileLocation, "file_exist", "Remote cluster configuration file does not exist. Please create it first.");
				}
			}
			
			if($_POST['use_appion_wrapper'] == 'true'){
				$validator->addValidation("appion_wrapper_path", $_POST['appion_wrapper_path'], "abs_path");
			}
		}
		
		$validator->runValidation();
		$errMsg = $validator->getErrorMessage();

		
		if(empty($errMsg)){
			
			$_SESSION['post'] = $_POST;
			setupUtils::redirect('confirmConfig.php');
			exit();
		}
		
	}

	$template = new template;
	$template->wizardHeader("Step 4 : Additional setup for web tools", SETUP_CONFIG);
	
?>
	<script language="javascript">
	<!-- //

		function enableCache(obj){

			if(obj.value == "true"){
				wizard_form.cache_path.style.backgroundColor = "#ffffff";
				wizard_form.cache_path.readOnly = false;
			}else{
				wizard_form.cache_path.style.backgroundColor = "#eeeeee";
				wizard_form.cache_path.readOnly = true;
				wizard_form.cache_path.value = "";
			}
		}

		function useWrapper(obj){
	
			if(obj.value == "true"){
				wizard_form.appion_wrapper_path.style.backgroundColor = "#ffffff";
				wizard_form.appion_wrapper_path.readOnly = false;
			}else{
				wizard_form.appion_wrapper_path.style.backgroundColor = "#eeeeee";
				wizard_form.appion_wrapper_path.readOnly = true;
				wizard_form.appion_wrapper_path.value = "";
			}
		}
	
		function setAppion(obj){
			
			if(obj.value == "true"){
				wizard_form.def_processing_prefix.style.backgroundColor = "#ffffff";
				wizard_form.def_processing_prefix.readOnly = false;
				wizard_form.hide_imagic[0].disabled = false;
				wizard_form.hide_imagic[1].disabled = false;
				wizard_form.hide_matlab[0].disabled = false;
				wizard_form.hide_matlab[1].disabled = false;
				wizard_form.hide_feature[0].disabled = false
				wizard_form.hide_feature[1].disabled = false;
				wizard_form.temp_images_dir.style.backgroundColor = "#ffffff";
				wizard_form.temp_images_dir.readOnly = false;
				wizard_form.defaultcs.style.backgroundColor = "#ffffff";
				wizard_form.defaultcs.readOnly = false;
				wizard_form.addHost.disabled = false;
				wizard_form.removeHost.disabled = false;
				wizard_form.addCluster.disabled = false;
				wizard_form.removeCluster.disabled = false;
				
			}else{
				
				wizard_form.def_processing_prefix.style.backgroundColor = "#eeeeee";
				wizard_form.def_processing_prefix.readOnly = true;
				wizard_form.hide_imagic[0].disabled = true;
				wizard_form.hide_imagic[1].disabled = true;
				wizard_form.hide_matlab[0].disabled = true;
				wizard_form.hide_matlab[1].disabled = true;
				wizard_form.hide_feature[0].disabled = true;
				wizard_form.hide_feature[1].disabled = true;
				wizard_form.temp_images_dir.style.backgroundColor = "#eeeeee";
				wizard_form.temp_images_dir.readOnly = true;
				wizard_form.temp_images_dir.value = "";
				wizard_form.defaultcs.style.backgroundColor = "#eeeeee";
				wizard_form.defaultcs.readOnly = true;
				wizard_form.defaultcs.value = "";
				wizard_form.addHost.disabled = true;
				wizard_form.removeHost.disabled = true;
				wizard_form.addCluster.disabled = true;
				wizard_form.removeCluster.disabled = true;
				

				var tbl = document.getElementById('hosts');
				var lastRow = tbl.rows.length;
				var i = 0;

				for(i=0 ; i<lastRow ; i++){
					removeRowFormTable('hosts');
				}

				var tbl = document.getElementById('clusters');
				var lastRow = tbl.rows.length;
				var i = 0;

				for(i=0 ; i<lastRow ; i++){
					removeRowFormTable('clusters');
				}
			}
		}

		function addRowToTable(host, nproc)
		{
			var tbl = document.getElementById('hosts');
			var lastRow = tbl.rows.length;

			// if there's no header row in the table, then iteration = lastRow + 1
			var iteration = lastRow;
			var row = tbl.insertRow(lastRow);
		  
			// first cell
		  	var cellFirst = row.insertCell(0);
		  	var textNode = document.createTextNode("Local cluster host name : ");
			cellFirst.appendChild(textNode);
			  
			// second cell
			var cellRight = row.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+lastRow+'][host]';
		  	el.value = host;
		  	el.size = 20;
		  
		  	cellRight.appendChild(el);
	
		    // thired cell
			var cellFirst = row.insertCell(2);
		  	var textNode = document.createTextNode("Max number of processors per node :");
		  	cellFirst.appendChild(textNode);
		  
  		    // last cell
		  	var cellRight = row.insertCell(3);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+lastRow+'][nproc]';
		  	el.value = nproc;
		  	el.size = 3;
		  
		  	cellRight.appendChild(el);
		}
	
		function addClusterRow(cluster)
		{
			var tbl = document.getElementById('clusters');
			var lastRow = tbl.rows.length;

			// if there's no header row in the table, then iteration = lastRow + 1
			var iteration = lastRow;
			var row = tbl.insertRow(lastRow);
		  
			// first cell
		  	var cellFirst = row.insertCell(0);
		  	var textNode = document.createTextNode("Remote cluster configuration filename : ");
			cellFirst.appendChild(textNode);
			  
			// second cell
			var cellRight = row.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'cluster_configs['+lastRow+']';
		  	el.value = cluster;
		  	el.size = 15;
		  
		  	cellRight.appendChild(el);
	
		}
	
		function removeRowFormTable(host)
		{
		  	var tbl = document.getElementById(host);
		  	var lastRow = tbl.rows.length;
		  	if (lastRow > 0) tbl.deleteRow(lastRow - 1);
		}
	// -->
	</script>
	
	<form name='wizard_form' method='POST' action='<?php echo $_SERVER['PHP_SELF']; ?>'>
	<?php
		foreach ($_SESSION['post'] as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
	?>
	
		<h3>Do you want to enable image caching for faster image viewing?</h3>
		<p>Note: To use image caching, you need to setup the caching location.</p>
		<input type="radio" name="enable_cache" value="true" 
		<?php 
			if($_POST){
				($_POST['enable_cache'] == 'true') ? print("checked='yes'") : print("");
			}else{
				($update) ? (defined("ENABLE_CACHE") && ENABLE_CACHE)? print("checked='yes'") : print("") : print(""); 
			}
		?>
			onclick="enableCache(this)" />&nbsp;&nbsp;YES<br />
		<input type="radio" name="enable_cache" value="false" 
		<?php 
			if($_POST){
				($_POST['enable_cache'] == 'false') ? print("checked='yes'") : print("");
			}else{
				($update) ? (defined("ENABLE_CACHE") && ENABLE_CACHE)? print("") : print("checked='yes'") : print("checked='yes'"); 
			}
		?>
			onclick="enableCache(this)" />&nbsp;&nbsp;NO<br />
		
		<p>Example : /srv/www/cache/  </p>
		<div id="error"><?php if($errMsg['cache_path']) echo $errMsg['cache_path']; ?></div>
		<input type="text" size=35 name="cache_path" 
		<?php 
			if($_POST){
				($_POST['enable_cache'] == 'true') ? print("value='".$_POST['cache_path']."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); 
			}else{
				($update && ENABLE_CACHE) ? print("value='".CACHE_PATH."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); 
			}
		?> /><br /><br />
		Please make sure the apache user has write access to this folder. (example: chown 'your_apache_user' /srv/www/cache/)  <br />
		<br />

		<h3>Enable download images as TIFF or JPEG</h3>
		<p>Please provide the path to the mrc2any python module. The path may be found by typing "which mrc2any" at a command prompt.   
			See <a target='_blank' href='http://ami.scripps.edu/redmine/projects/appion/wiki/Install_the_Web_Interface'>installation documentation</a> for help. <br /><br />
			Example : /usr/bin/mrc2any  </p>
		<div id="error"><?php if($errMsg['mrc2any']) echo $errMsg['mrc2any']; ?></div>
		<input type="text" size=25 name="mrc2any" 
		<?php 			
			if($_POST){
				print("value='".$_POST['mrc2any']."'");
			}else{
				($update) ? print("value='".MRC2ANY."'") : print("value=''"); 
			}
		
		?> /><br /><br />
		<br />
				
		<h3>Do you want to enable the Appion image processing pipeline</h3>
		<p>Select "YES" if you want to use Appion image processing.</p>
		<p>Note: Other processing software installation required.</p>
		<input type="radio" name="processing" value="true" 
		<?php 
			if($_POST){
				($_POST['processing'] == 'true') ? print("checked='yes'") : print("");
			}else{		
				($update) ? (defined("PROCESSING") && PROCESSING)? print("checked='yes'") : print("") : print(""); 
			}
		?>
			onclick="setAppion(this)" />&nbsp;&nbsp;YES<br />
		<input type="radio" name="processing" value="false" 
		<?php 
			if($_POST){
				($_POST['processing'] == 'false') ? print("checked='yes'") : print("");
			}else{			
				($update) ? (defined("PROCESSING") && PROCESSING)? print("") : print("checked='yes'") : print("checked='yes'"); 
			}
		?>
			onclick="setAppion(this)" />&nbsp;&nbsp;NO<br />
		<br />

		<h3>Enter Appion database prefix:</h3>
		<p>We recommend using 'ap' as the Appion database prefix.<br /> 
		   This prefix must match the prefix used during step number 11 of the 
		   <a href="http://ami.scripps.edu/redmine/projects/appion/wiki/Database_Server_Installation">Database Server Setup</a>. </p>
		<div id="error"><?php if($errMsg['def_processing_prefix']) echo $errMsg['def_processing_prefix']; ?></div>
		<input type="text" size=10 name="def_processing_prefix" 
		<?php 
			if($_POST){
				($_POST['processing'] == 'true') ? print("value='".$_POST['def_processing_prefix']."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value='ap'");
			}else{
				($update && PROCESSING === true) ? print("value='".DEF_PROCESSING_PREFIX."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value='ap'"); 
			}
		?> /><br /><br />
		<br />

		<h3>Enter Image Processing Host(s) information:</h3>
		<p>Please enter your processing host name and the number of processors on individual nodes of this host.</p>
		<input name="addHost" type="button" value="Add" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="addRowToTable('', '');" />
		<input name="removeHost" type="button" value="Remove"  <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="removeRowFormTable('hosts');" />
		Please Click the "Add" Button to start. If you don't have a processing host, leave it empty.<br />
		
		<table border=0 cellspacing=8 style="font-size: 12px" id="hosts">
		<div id="error"><?php if($errMsg['host']) echo $errMsg['host']; ?></div>
		<div id="error"><?php if($errMsg['nproc']) echo $errMsg['nproc']; ?></div>
		</table><br />

		<h3>Register your cluster configuration file(s)</h3>
		<p>You can find a default cluster configuration file (default_cluster.php) in the myamiweb/processing folder.<br />
		   Create a new configuration file for each cluster with a different name base on the default_cluster.php.<br />
		   Please make sure you <font color="red">do not include (.php) in the input box</font>.<br />
		   Example: If your cluster configuration file name is "cluster.php", just enter "cluster" below.<br />	   
		</p>
		<input name="addCluster" type="button" value="Add" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="addClusterRow('');" />
		<input name="removeCluster" type="button" value="Remove" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="removeRowFormTable('clusters');" />
		Please Click the "Add" Button to start. If you don't know the cluster configure file name, leave it empty.<br />
		
		<table border=0 cellspacing=8 style="font-size: 12px" id="clusters">
		<div id="error"><?php if($errMsg['cluster_configs']) echo $errMsg['cluster_configs']; ?></div>
		</table><br />	
		
		<h3>Do you wish to use the IMAGIC image processing package</h3>
		<p>Note: IMAGIC software installation required.</p>
		<input type="radio" name="hide_imagic" value="false" <?php ($update) ? (defined("HIDE_IMAGIC") && HIDE_IMAGIC)? print("") : print("checked='yes'") : print("disabled"); ?> />
		&nbsp;&nbsp;YES<br />
		<input type="radio" name="hide_imagic" value="true" <?php ($update) ? (defined("HIDE_IMAGIC") && HIDE_IMAGIC)? print("checked='yes'") : print("") : print("disabled checked='yes'"); ?> />
		&nbsp;&nbsp;NO<br />
		<br />

		<h3>Do you wish to use programs that require MATLAB?</h3>
		<input type="radio" name="hide_matlab" value="false" <?php ($update) ? (defined("HIDE_MATLAB") && HIDE_MATLAB)? print("") : print("checked='yes'") : print("disabled checked='yes'"); ?> />
		&nbsp;&nbsp;YES<br />
		<input type="radio" name="hide_matlab" value="true" <?php ($update) ? (defined("HIDE_MATLAB") && HIDE_MATLAB)? print("checked='yes'") : print("") : print("disabled"); ?> />
		&nbsp;&nbsp;NO<br />
		<br />

		<h3>Do you want to use image processing tools that are still under development?</h3>
		<p>Note: Tools still under development are not fully functioning. We suggest hiding these features.</p>
		<input type="radio" name="hide_feature" value="false" <?php ($update) ? (defined("HIDE_FEATURE") && HIDE_FEATURE)? print("") : print("checked='yes'") : print("disabled"); ?> />
		&nbsp;&nbsp;YES<br />	
		<input type="radio" name="hide_feature" value="true" <?php ($update) ? (defined("HIDE_FEATURE") && HIDE_FEATURE)? print("checked='yes'") : print("") : print("disabled checked='yes'"); ?> />
		&nbsp;&nbsp;NO<br />

		<br />

		<h3>Enter the spherical aberration (Cs) constant for the microscope (in millimeters). <a target='_blank' href='http://en.wikipedia.org/wiki/Spherical_aberration'>Wikipedia</a> description.</h3>
		<p>Example : 2.0  </p>
		<div id="error"><?php if($errMsg['defaultcs']) echo $errMsg['defaultcs']; ?></div>
		<input type="text" size=5 name="defaultcs" 
		<?php 
			if($_POST){
				($_POST['processing'] == 'true') ? print("value='".$_POST['defaultcs']."'") : print("readOnly=\"true\" style=\"background:#eeeeee\"");
			}else{
				($update && PROCESSING === true) ? print("value='".DEFAULTCS."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); 
			}
		?> /><br /><br />
		<br />
		
		<h3>Enter a temporary upload directory location.</h3>
		<p>This is a temporary directory that is accessible to both the web server and the processing servers for uploading images, templates, or models.</p>
		<div id="error"><?php if($errMsg['temp_images_dir']) echo $errMsg['temp_images_dir']; ?></div>
		<input type="text" size=25 name="temp_images_dir" 
		<?php 
			if($_POST){
				($_POST['processing'] == 'true') ? print("value='".$_POST['temp_images_dir']."'") : print("readOnly=\"true\" style=\"background:#eeeeee\"");
			}else{
				($update && PROCESSING === true) ? print("value='".TEMP_IMAGES_DIR."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); 
			}
		?> /><br /><br />
		<br />
		
		<input type="submit" value="NEXT" />
	</form>
	
<?php 

	if($_POST){
		$PROCESSING_HOSTS = $_POST['processing_hosts'];
		$CLUSTER_CONFIGS = $_POST['cluster_configs'];
	}
	
	if(!empty($PROCESSING_HOSTS)){
		foreach($PROCESSING_HOSTS as $processingHost)
			echo "<script language=javascript>addRowToTable('".$processingHost['host']."', '".$processingHost['nproc']."')</script>";
	}
	if(!empty($CLUSTER_CONFIGS)){
		foreach($CLUSTER_CONFIGS as $clusterConfig)
			echo "<script language=javascript>addClusterRow('".$clusterConfig."')</script>";
	}
	
	$template->wizardFooter();
?>

