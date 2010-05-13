<?php

require_once('template.inc');
require_once('setupUtils.inc');

	setupUtils::checkSession();
	$update = false;	
	if($_SESSION['loginCheck']){
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
		  	var textNode = document.createTextNode("Processing Host Name : ");
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
		  	var textNode = document.createTextNode("Max number of processor per node :");
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
		  	var textNode = document.createTextNode("Cluster configure filename : ");
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
		<p>We recommend using 'ap' as Appion database prefix.</p>
		<input type="text" size=5 name="def_processing_prefix" <?php ($update && PROCESSING === true) ? print("value='".DEF_PROCESSING_PREFIX."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value='ap'"); ?> /><br /><br />
		<br />

		<h3>Enter Image Processing Host(s) information:</h3>
		<p>Please enter your processing host name and the number of processors on individual nodes of this host.</p>
		<input name="addHost" type="button" value="Add" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="addRowToTable('', '');" />
		<input name="removeHost" type="button" value="Remove"  <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="removeRowFormTable('hosts');" />
		Please Click the "Add" Button to start. If you don't have a processing host, leave it empty.<br />
		<table border=0 cellspacing=8 style="font-size: 12px" id="hosts"></table><br />

		<h3>Register your cluster configure file(s)</h3>
		<p>You can find a default cluster configure file (default_cluster.php) under the processing folder.<br />
		   Create a new configure file for each cluster with different name base on the default_cluster.php.<br />
		   Please make sure <font color="red">do not include (.php) in the input box</font>.<br />
		   Example: If your cluster configure file name is cluster1.php, just enter cluster1 below.<br />	   
		</p>
		<input name="addCluster" type="button" value="Add" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="addClusterRow('');" />
		<input name="removeCluster" type="button" value="Remove" <?php ($update && PROCESSING === true) ? print("") : print("disabled"); ?> onclick="removeRowFormTable('clusters');" />
		Please Click the "Add" Button to start. If you don't know the cluster configure file name, left it empty.<br />
		<table border=0 cellspacing=8 style="font-size: 12px" id="clusters"></table><br />	
		
		<h3>Do you want to hide the IMAGIC image processing package menu items in image processing pipeline</h3>
		<p>Select "NO" if you want to use IMAGIC.</p>
		<p>Note: IMAGIC software installation required.</p>
		<input type="radio" name="hide_imagic" value="true" <?php ($update) ? (defined("HIDE_IMAGIC") && HIDE_IMAGIC)? print("checked='yes'") : print("") : print("disabled checked='yes'"); ?> />
		&nbsp;&nbsp;YES<br />
		<input type="radio" name="hide_imagic" value="false" <?php ($update) ? (defined("HIDE_IMAGIC") && HIDE_IMAGIC)? print("") : print("checked='yes'") : print("disabled"); ?> />
		&nbsp;&nbsp;NO<br />
		<br />

		<h3>Do you want to hide image processing tools that are under development?</h3>
		<p>Note: Tools still under development are not fully functioning. We suggest hiding these features.</p>
		<input type="radio" name="hide_feature" value="true" <?php ($update) ? (defined("HIDE_FEATURE") && HIDE_FEATURE)? print("checked='yes'") : print("") : print("disabled"); ?> />
		&nbsp;&nbsp;YES<br />
		<input type="radio" name="hide_feature" value="false" <?php ($update) ? (defined("HIDE_FEATURE") && HIDE_FEATURE)? print("") : print("checked='yes'") : print("disabled checked='yes'"); ?> />
		&nbsp;&nbsp;NO<br />		
		<br />
		
		<h3>Enter the spherical aberration constant for the microscope (Cs. Value).</h3>
		<p>Example : 2.0</p>
		<input type="text" size=5 name="defaultcs" <?php ($update && PROCESSING === true) ? print("value='".DEFAULTCS."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=''"); ?> /><br /><br />
		<br />
		
		<h3>Enter a temporary upload directory location.</h3>
		<p>You can setup a temporary directory for upload images, templates, models. (Optional)</p>
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

