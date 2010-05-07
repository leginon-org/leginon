<?php

require_once('template.inc');
require_once('setupUtils.inc');

	setupUtils::checkSession();

	$template = new template;
	$template->wizardHeader("Step 5 : Confirm all your inputs", SETUP_CONFIG);

?>

	<form name='wizard_form' method='POST' action='review.php'>
	
	<?php 
		foreach ($_POST as $name => $value){
			if($name == 'processing_hosts' && is_array($value)){

				$count = 0;
				foreach($value as $key){
					echo "<input type='hidden' name='".$name."[".$count."][host]' value='".$key['host']."' />";
					echo "<input type='hidden' name='".$name."[".$count."][nproc]' value='".$key['nproc']."' />";
					$count++;
				}
			}
			else{
				$value = trim($value);
				echo "<input type='hidden' name='".$name."' value='".$value."' />";
			}
		}
	?>
		
		<h3>Please review all the inputs you have been entered.</h3>
		
	<?php 
		foreach ($_POST as $name => $value){
			if($name == 'processing_hosts' && is_array($value)){
				echo "<p>" . strtoupper($name) . " :<br />";
				
				foreach($value as $key){
					echo "&nbsp;&nbsp;&nbsp;&nbsp;Host : " . $key['host'] . "&nbsp;&nbsp;";
					echo "&nbsp;&nbsp;&nbsp;&nbsp;Number of Nodes : " . $key['nproc'] . "<br />";
				}
				echo "</p>";
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