<?php

require_once('template.inc');
require_once('setupUtils.inc');

	setupUtils::checkSession();
	$update = false;	
	if(!empty($_SESSION['loginCheck'])){
		require_once(CONFIG_FILE);
		$update = true;
	}

	$template = new template;
	$template->wizardHeader("Step 4 : Additional setup for web tools", SETUP_CONFIG);
	
?>
	<script language="javascript">
	<!-- //

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
		  	el.size = 10;
		  
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
	
	<form name='wizard_form' method='POST' action='confirmConfig.php'>
	<?php
		foreach ($_POST as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
	?>
	
		
		<h3>Do you want to enable the Appion image processing pipeline</h3>
		<p>Select "YES" if you want to use Appion image processing.</p>
		<p>Note: Other processing software installation required.</p>
		<input type="radio" name="processing" value="true" <?php ($update) ? (defined("PROCESSING") && PROCESSING)? print("checked='yes'") : print("") : print(""); ?>
			onclick="setAppion(this)" />&nbsp;&nbsp;YES<br />
		<input type="radio" name="processing" value="false" <?php ($update) ? (defined("PROCESSING") && PROCESSING)? print("") : print("checked='yes'") : print("checked='yes'"); ?>
			onclick="setAppion(this)" />&nbsp;&nbsp;NO<br />
		<br />

		<h3>Enter Appion database prefix:</h3>
		<p>We recommend using 'ap' as the Appion database prefix.<br /> 
		   This prefix must match the prefix used during step number 11 of the 
		   <a href="http://ami.scripps.edu/redmine/projects/appion/wiki/Database_Server_Installation">Database Server Setup</a>. </p>
		<input type="text" size=5 name="def_processing_prefix" <?php ($update && PROCESSING === true) ? print("value='".DEF_PROCESSING_PREFIX."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value='ap'"); ?> /><br /><br />
		<br />

		<h3>Enter Image Processing Host(s) information:</h3>
		<p>Please enter your processing host name and the number of processors on individual nodes of this host.</p>
		<input name="addHost" type="button" value="Add" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="addRowToTable('', '');" />
		<input name="removeHost" type="button" value="Remove"  <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="removeRowFormTable('hosts');" />
		Please Click the "Add" Button to start. If you don't have a processing host, leave it empty.<br />
		<table border=0 cellspacing=8 style="font-size: 12px" id="hosts"></table><br />

		<h3>Register your cluster configuration file(s)</h3>
		<p>You can find a default cluster configuration file (default_cluster.php) in the myamiweb/processing folder.<br />
		   Create a new configuration file for each cluster with a different name base on the default_cluster.php.<br />
		   Please make sure you <font color="red">do not include (.php) in the input box</font>.<br />
		   Example: If your cluster configuration file name is cluster1.php, just enter cluster1 below.<br />	   
		</p>
		<input name="addCluster" type="button" value="Add" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="addClusterRow('');" />
		<input name="removeCluster" type="button" value="Remove" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="removeRowFormTable('clusters');" />
		Please Click the "Add" Button to start. If you don't know the cluster configure file name, leave it empty.<br />
		<table border=0 cellspacing=8 style="font-size: 12px" id="clusters"></table><br />	
		
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

		<h3>Enter the spherical aberration (Cs) constant for the microscope (in millimeters). <a href='http://en.wikipedia.org/wiki/Spherical_aberration'>Wikipedia</a> description.</h3>
		<p>Example : 2.0  </p>
		<input type="text" size=5 name="defaultcs" <?php ($update && PROCESSING === true) ? print("value='".DEFAULTCS."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); ?> /><br /><br />
		<br />
		
		<h3>Enter a temporary upload directory location (Optional).</h3>
		<p>This is a temporary directory that is accessible to both the web server and the processing servers for uploading images, templates, or models.</p>
		<input type="text" size=20 name="temp_images_dir" <?php ($update && PROCESSING === true) ? print("value='".TEMP_IMAGES_DIR."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); ?> /><br /><br />
		<br />
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
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

