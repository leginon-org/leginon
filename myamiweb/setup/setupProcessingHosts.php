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
		
			
		if(!empty($_POST['processing_hosts'])){

			foreach ($_POST['processing_hosts'] as $processingHost){
				$validator->addValidation("host", $processingHost['host'], "req", "Cluster host name can not be empty.");
				$validator->addValidation("host", $processingHost['host'], "remoteServer", "Local cluster does not exist. Please make sure the cluster exists.");
				// TODO: add validations for the processing host params
				//$validator->addValidation("nproc", $processingHost['nproc'], "req", "Max number of processors per node can not be empty.");
				//$validator->addValidation("nproc", $processingHost['nproc'], "num", "Please provide a numeric input for maximum number of processors per node.");
			}
		}

			
		if($_POST['use_appion_wrapper'] == 'true'){
			$validator->addValidation("appion_wrapper_path", $_POST['appion_wrapper_path'], "abs_path");
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
	$template->wizardHeader("Step 5 : Configure Processing Hosts", SETUP_CONFIG);
	
?>
	<script language="javascript">
	<!-- //


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

		// TODO: there must be a way to improve this so it is easier to add new parameters
		function addRowToTable(host, nodesdef,nodesmax,ppndef,ppnmax,reconpn,walltimedef,
				walltimemax,cputimedef,cputimemax,memorymax,appionbin,appionlibdir,baseoutdir,
				localhelperhost,dirsep,wrapperpath,loginmethod,loginusername,passphrase,publickey,privatekey)
		{
			var tbl = document.getElementById('hosts');
			var lastRow = tbl.rows.length;

			var rowsPerIter = 22;

			// if there's no header row in the table, then iteration = lastRow + 1
			var iteration = lastRow / rowsPerIter;

			// get host name
			var row1 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
		  	var cellFirst = row1.insertCell(0);
		  	var textNode = document.createTextNode("Local cluster host name : ");
			cellFirst.appendChild(textNode);
			  
			var cellRight = row1.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][host]';
		  	el.value = host;
		  	el.size = 30;
		  	el.style.backgroundColor = "lightblue";
		  	cellRight.appendChild(el);

		  	// get default number of nodes to use for a job
			var row2 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row2.insertCell(0);
		  	var textNode = document.createTextNode("Default number of nodes per job :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row2.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][nodesdef]';
		  	el.value = nodesdef;
		  	el.size = 3;
		  	cellRight.appendChild(el);
		  	
		  	// get max number of nodes allowed for a job
			var row3 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row3.insertCell(0);
		  	var textNode = document.createTextNode("Max number of nodes per job :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row3.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][nodesmax]';
		  	el.value = nodesmax;
		  	el.size = 3;
		  	cellRight.appendChild(el);
		  	
		  	// get default number of processors per node
			var row4 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row4.insertCell(0);
		  	var textNode = document.createTextNode("Default number of processors per node :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row4.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][ppndef]';
		  	el.value = ppndef;
		  	el.size = 3;
		  	cellRight.appendChild(el);

			// get max processors per node
			var row5 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row5.insertCell(0);
		  	var textNode = document.createTextNode("Max number of processors per node :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row5.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][ppnmax]';
		  	el.value = ppnmax;
		  	el.size = 3;
		  	cellRight.appendChild(el);

		  	// get the number of reconstructions per node
			var row6 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row6.insertCell(0);
		  	var textNode = document.createTextNode("Max number of reconstructions per node :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row6.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][reconpn]';
		  	el.value = reconpn;
		  	el.size = 3;
		  	cellRight.appendChild(el);

		  	// get default wall time
			var row7 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row7.insertCell(0);
		  	var textNode = document.createTextNode("Default Wall Time (minutes) allowed :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row7.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][walltimedef]';
		  	el.value = walltimedef;
		  	el.size = 3;
		  	cellRight.appendChild(el);

		  	// get max wall time
			var row8 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row8.insertCell(0);
		  	var textNode = document.createTextNode("Max Wall Time (minutes) allowed :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row8.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][walltimemax]';
		  	el.value = walltimemax;
		  	el.size = 3;
		  	cellRight.appendChild(el);

		  	// get default cpu time 
			var row9 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row9.insertCell(0);
		  	var textNode = document.createTextNode("Default CPU time (minutes) allowed :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row9.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][cputimedef]';
		  	el.value = cputimedef;
		  	el.size = 3;
		  	cellRight.appendChild(el);

		  	// get max cpu time
			var row10 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row10.insertCell(0);
		  	var textNode = document.createTextNode("Max CPU time (minutes) allowed :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row10.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][cputimemax]';
		  	el.value = cputimemax;
		  	el.size = 3;
		  	cellRight.appendChild(el);

		  	// get max memory to use
			var row11 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row11.insertCell(0);
		  	var textNode = document.createTextNode("Max Memory (Gb) to use :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row11.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][memorymax]';
		  	el.value = memorymax;
		  	el.size = 3;
		  	cellRight.appendChild(el);

		  	// get the location of appion scripts on cluster, must end in slash, e.g., /usr/local/appion/bin/
			var row12 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row12.insertCell(0);
		  	var textNode = document.createTextNode("Path to Appion Scripts :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row12.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][appionbin]';
		  	el.value = appionbin;
		  	el.size = 30;
		  	cellRight.appendChild(el);

		  	// get the path to the appion lib dir, must end in slash, e.g., /usr/local/appion/appionlib/
			var rowLib = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = rowLib.insertCell(0);
		  	var textNode = document.createTextNode("Path to appionlib directory :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = rowLib.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][appionlibdir]';
		  	el.value = appionlibdir;
		  	el.size = 30;
		  	cellRight.appendChild(el);

		  	// get the base output directory, if empty, sends appion procession output to a location under the users home directory on the remote host
			var row13 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row13.insertCell(0);
		  	var textNode = document.createTextNode("Base output directory :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row13.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][baseoutdir]';
		  	el.value = baseoutdir;
		  	el.size = 30;
		  	cellRight.appendChild(el);

		  	// get the local helper host - for a remote processing host
			var row14 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row14.insertCell(0);
		  	var textNode = document.createTextNode("Local Helper Host :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row14.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][localhelperhost]';
		  	el.value = localhelperhost;
		  	el.size = 30;
		  	cellRight.appendChild(el);
		  	
		  	// get the directory seperator, eg. "/"
			var row15 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row15.insertCell(0);
		  	var textNode = document.createTextNode("Directory Seperator, eg. / :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row15.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][dirsep]';
		  	el.value = dirsep;
		  	el.size = 1;
		  	cellRight.appendChild(el);

		  	// get the path to the appion wrapper script, allows for multiple installations on the same machine
			var row16 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row16.insertCell(0);
		  	var textNode = document.createTextNode("Path to Appion Wrapper Script :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row16.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][wrapperpath]';
		  	el.value = wrapperpath;
		  	el.size = 30;
		  	cellRight.appendChild(el);

		  	// get the login method, USERPASSWORD or SHAREDKEY
			var row17 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row17.insertCell(0);
		  	var textNode = document.createTextNode("Login Method :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row17.insertCell(1);
		  	var el = document.createElement('select');
		  	el.name = 'processing_hosts['+iteration+'][loginmethod]';
		  	var option1 = document.createElement('option');
		  	option1.text = "User Password ";
		  	option1.value = "USERPASSWORD";
		  	var option2 = document.createElement('option');
		  	option2.text = "Shared Key ";
		  	option2.value = "SHAREDKEY";
		  	try {
			  	el.add(option1, null);
		  	} catch(error) {
			  	el.add(option1);
		  	}
		  	try {
			  	el.add(option2, null);
		  	} catch(error) {
			  	el.add(option2);
		  	}
			if (loginmethod == "SHAREDKEY") {
				 el.value = option2.value;
			} else {
				el.value = option1.value;
			}
		  	cellRight.appendChild(el);

		  	// get login username
			var row18 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row18.insertCell(0);
		  	var textNode = document.createTextNode("Login Username :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row18.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][loginusername]';
		  	el.value = loginusername;
		  	el.size = 30;
		  	cellRight.appendChild(el);

		  	// get login pass phrase
			var row19 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row19.insertCell(0);
		  	var textNode = document.createTextNode("Login Pass Phrase :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row19.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][passphrase]';
		  	el.value = passphrase;
		  	el.size = 30;
		  	cellRight.appendChild(el);

		  	// get public key file
			var row20 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row20.insertCell(0);
		  	var textNode = document.createTextNode("Public Key File :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row20.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][publickey]';
		  	el.value = publickey;
		  	el.size = 30;
		  	cellRight.appendChild(el);

		  	// get private key file
			var row21 = tbl.insertRow(lastRow);
			lastRow = lastRow +1;
			var cellFirst = row21.insertCell(0);
		  	var textNode = document.createTextNode("Private Key File :");
		  	cellFirst.appendChild(textNode);
		  
		  	var cellRight = row21.insertCell(1);
		  	var el = document.createElement('input');
		  	el.type = 'text';
		  	el.name = 'processing_hosts['+iteration+'][privatekey]';
		  	el.value = privatekey;
		  	el.size = 30;
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
	
		<h3>Enter Image Processing Host(s) information:</h3>
		<p>Please enter your processing host name and the number of processors on individual nodes of this host.</p>
		<input name="addHost" type="button" value="Add" <?php /*($update && PROCESSING === true) ? print("") : print("disabled"); */?> onclick="addRowToTable('','','','','','','','','','','','','','','','','','','','','');" />
		<!-- leave the remove button out, does not work -->
		<!-- <input name="removeHost" type="button" value="Remove"  <?php /*($update && PROCESSING === true) ? print("") : print("disabled");*/ ?> onclick="removeRowFormTable('hosts');" />-->
		Please Click the "Add" Button to start. If this is a new installation and you have not yet set up a processing host (<a href="http://emg.nysbc.org/redmine/projects/appion/wiki/Setup_Remote_Processing">Setup Remote Processing</a>), please skip this section and return here later.<br />
		
		<table border=0 cellspacing=8 style="font-size: 12px" id="hosts">
		<div id="error"><?php if($errMsg['host']) echo $errMsg['host']; ?></div>
		<div id="error"><?php if($errMsg['nproc']) echo $errMsg['nproc']; ?></div>
		</table><br />

				
		<input type="submit" value="NEXT" />
	</form>
	
<?php 

	if($_POST){
		$PROCESSING_HOSTS = $_POST['processing_hosts'];
	}

	if(!empty($PROCESSING_HOSTS)){
		foreach($PROCESSING_HOSTS as $processingHost) {
			echo "<script language=javascript>addRowToTable('".$processingHost['host']."', 
			'".$processingHost['nodesdef']."', 
			'".$processingHost['nodesmax']."', 
			'".$processingHost['ppndef']."', 
			'".$processingHost['ppnmax']."', 
			'".$processingHost['reconpn']."', 
			'".$processingHost['walltimedef']."', 
			'".$processingHost['walltimemax']."', 
			'".$processingHost['cputimedef']."', 
			'".$processingHost['cputimemax']."', 
			'".$processingHost['memorymax']."', 
			'".$processingHost['appionbin']."', 
			'".$processingHost['appionlibdir']."', 
			'".$processingHost['baseoutdir']."', 
			'".$processingHost['localhelperhost']."', 
			'".$processingHost['dirsep']."', 
			'".$processingHost['wrapperpath']."', 
			'".$processingHost['loginmethod']."', 
			'".$processingHost['loginusername']."', 
			'".$processingHost['passphrase']."', 
			'".$processingHost['publickey']."', 
			'".$processingHost['privatekey']."')</script>";
		}
	}
	
	$template->wizardFooter();
?>

