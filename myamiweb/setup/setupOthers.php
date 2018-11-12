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
		
		if($_POST['processing'] == 'true'){
						
			$validator->addValidation("def_processing_prefix", $_POST['def_processing_prefix'], "minlen=1");
			$validator->addValidation("def_processing_prefix", $_POST['def_processing_prefix'], "maxlen=10");
			$validator->addValidation("def_processing_prefix", $_POST['def_processing_prefix'], "alpha");
			
			$validator->addValidation("temp_images_dir", $_POST['temp_images_dir'], "abs_path");
			$validator->addValidation("temp_images_dir", $_POST['temp_images_dir'], "path_exist");
			$validator->addValidation("temp_images_dir", $_POST['temp_images_dir'], "folder_permission");
			$validator->addValidation("default_appion_path", $_POST['default_appion_path'], "abs_path");
			$validator->addValidation("default_appion_path", $_POST['default_appion_path'], "path_exist");
			//$validator->addValidation("default_appion_path", $_POST['default_appion_path'], "folder_permission");
						
			if($_POST['use_appion_wrapper'] == 'true'){
				$validator->addValidation("appion_wrapper_path", $_POST['appion_wrapper_path'], "abs_path");
			}
		}
		
		$validator->runValidation();
		$errMsg = $validator->getErrorMessage();

		
		if(empty($errMsg)){
			
			$_SESSION['post'] = $_POST;
			if ($_POST['processing'] == 'true') {
				setupUtils::redirect('setupProcessingHosts.php');
			} else {
				setupUtils::redirect('confirmConfig.php');
			}
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
				wizard_form.default_appion_path.style.backgroundColor = "#ffffff";
				wizard_form.default_appion_path.readOnly = false;
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
				wizard_form.default_appion_path.style.backgroundColor = "#eeeeee";
				wizard_form.default_appion_path.readOnly = true;
				wizard_form.default_appion_path.value = "";
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

	// -->
	</script>
	
	<form name='wizard_form' method='POST' action='<?php echo $_SERVER['PHP_SELF']; ?>'>
	<?php
		foreach ($_SESSION['post'] as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
	?>
	
		<h3>Enter Redux Image Server location and port:</h3>
		<p>Enter the name of the server that is running the Redux image server, ex. redux.schools.edu:</p>
		<p><a href="http://emg.nysbc.org/redmine/projects/appion/wiki/Install_Redux_image_server">Redux Server Setup Guide</a></p>
		<p>(Enter "localhost" if Redux server is on the webserver computer)</p>
		<input type="text" size=35 name="server_host" 
		<?php 			
			if($_POST){
				print("value='".$_POST['server_host']."'");
			}else{
				($update) ? print("value='".SERVER_HOST."'") : print("value=''"); 
			}
		?> /><br /><br />
		<p>Enter the port used by the Redux image server, ex. 55123:</p>
		<input type="text" size=35 name="server_port" 
		<?php 			
			if($_POST){
				print("value='".$_POST['server_port']."'");
			}else{
				($update) ? print("value='".SERVER_PORT."'") : print("value=''"); 
			}
		?> /><br /><br />

		<h3>Do you want to enable PHP image caching for faster image viewing?</h3>
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
		Please make sure the apache user has read access to this folder. (example: chown 'your_apache_user' /srv/www/cache/)  <br />
		<br />

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
		   <a href="http://emg.nysbc.org/redmine/projects/appion/wiki/Database_Server_Installation">Database Server Setup</a>. </p>
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
		
		<h3>Enter a default Appion base directory location.</h3>
		<p>Please setup a default Appion directory that is accessible (read, write and execute) to all the Appion users.</p>
		<p>Example: /example/path/appion <br />'/example/path' - folder in your file server. <br />'appion' - folder for saving Appion image processing result.
		<div id="error"><?php if($errMsg['default_appion_path']) echo $errMsg['default_appion_path']; ?></div>
		<input type="text" size=25 name="default_appion_path" 
		<?php 
			if($_POST){
				($_POST['processing'] == 'true') ? print("value='".$_POST['default_appion_path']."'") : print("readOnly=\"true\" style=\"background:#eeeeee\"");
			}else{
				($update && PROCESSING === true) ? print("value='".DEFAULT_APPION_PATH."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); 
			}
		?> /><br /><br />
		<br />
		
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
	
	$template->wizardFooter();
?>

