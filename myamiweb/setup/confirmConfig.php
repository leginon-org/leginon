<?php

require_once('template.inc');
require_once('setupUtils.inc');

	setupUtils::checkSession();

	$template = new template;
	$template->wizardHeader("Step 5 : Confirm your settings", SETUP_CONFIG);

?>

	<form name='wizard_form' method='POST' action='review.php'>
	
	<?php 
		foreach ($_SESSION['post'] as $name => $value){
			if($name == 'processing_hosts' && is_array($value)){

				$count = 0;
				foreach($value as $key){
					echo "<input type='hidden' name='".$name."[".$count."][host]' value='".$key['host']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][nodesdef]' value='".$key['nodesdef']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][nodesmax]' value='".$key['nodesmax']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][ppndef]' value='".$key['ppndef']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][ppnmax]' value='".$key['ppnmax']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][reconpn]' value='".$key['reconpn']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][walltimedef]' value='".$key['walltimedef']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][walltimemax]' value='".$key['walltimemax']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][cputimedef]' value='".$key['cputimedef']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][cputimemax]' value='".$key['cputimemax']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][memorymax]' value='".$key['memorymax']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][appionbin]' value='".$key['appionbin']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][appionlibdir]' value='".$key['appionlibdir']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][baseoutdir]' value='".$key['baseoutdir']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][localhelperhost]' value='".$key['localhelperhost']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][dirsep]' value='".$key['dirsep']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][wrapperpath]' value='".$key['wrapperpath']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][loginmethod]' value='".$key['loginmethod']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][loginusername]' value='".$key['loginusername']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][passphrase]' value='".$key['passphrase']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][publickey]' value='".$key['publickey']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][privatekey]' value='".$key['privatekey']."' />";
					$count++;
				}
			}
			elseif($name == 'cluster_configs' && is_array($value)){
				$count = 0;

				foreach($value as $key){
					echo "<input type='hidden' name='".$name."[]' value='".$key."' />";
				}
			}
			else{
				$value = trim($value);
				echo "<input type='hidden' name='".$name."' value='".$value."' />";
			}
		}
	?>
		
		<h3>Please review the settings you have entered.</h3>
		
	<?php 
		foreach ($_SESSION['post'] as $name => $value){
			if($name == 'processing_hosts' && is_array($value)){
				echo "<p>" . strtoupper($name) . " :<br />";
				
				foreach($value as $key){
					echo "<br />&emsp;&emsp;Host : " . $key['host'] . "&nbsp;&nbsp;";
					echo "<br />&emsp;&emsp;&emsp;&emsp;Default number of nodes per job : " . $key['nodesdef'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Max number of nodes per job : " . $key['nodesmax']; 
					echo "<br />&emsp;&emsp;&emsp;&emsp;Default number of processors per node : " . $key['ppndef'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Max number of processors per node : " . $key['ppnmax'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Max number of reconstructions per node : " . $key['reconpn'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Default Wall Time allowed : " . $key['walltimedef'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Max Wall Time allowed : " . $key['walltimemax'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Default CPU time allowed : " . $key['cputimedef'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Max CPU time allowed : " . $key['cputimemax'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Max Memory to use : " . $key['memorymax'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Path to Appion Scripts : " . $key['appionbin'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Path to Appion Scripts : " . $key['appionlibdir'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Base output directory : " . $key['baseoutdir'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Local Helper Host : " . $key['localhelperhost'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Directory Seperator : " . $key['dirsep'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Path to Appion Wrapper Script : " . $key['wrapperpath']; 
					echo "<br />&emsp;&emsp;&emsp;&emsp;Login Method : " . $key['loginmethod'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Login Username : " . $key['loginusername'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Login Pass Phrase : " . $key['passphrase'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Public Key File : " . $key['publickey'];
					echo "<br />&emsp;&emsp;&emsp;&emsp;Private Key File : " . $key['privatekey'] . "<br />";				
				}
				echo "</p>";
			}
			elseif($name == 'cluster_configs' && is_array($value)){
				echo"<p>" . strtoupper($name) . " : <br />";
				foreach($value as $name)
					echo "&nbsp;&nbsp;&nbsp;&nbsp;Cluster configure file : " . $name . "<br />";
			}				
			elseif(!empty($value))
				echo "<p>" . strtoupper($name) . " : " . $value . "</p>";
		}
	
	?>
		
		<br />
		<input type="hidden" name="create_file" value="true" />
		<input type="submit" value="Create Web Tools Config file" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>