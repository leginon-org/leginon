<?php

require_once('template.inc');
require_once('setupUtils.inc');
	
	$template = new template;
	$template->wizardHeader("Step 5 : Review your setup");
	
	if($_POST['create_file']){
		var_dump($_POST);
	}
?>

	<form name='wizard_form' method='POST' action='<?php echo $PHP_SELF; ?>'>

	<?php 
		foreach ($_POST as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
	?>
		
		<h3>Please review all the inputs you have been entered.</h3>
		
	<?php 
		foreach ($_POST as $key => $value){
			echo "<p>" . strtoupper($key) . " : " . $value . "</p>";
		}
	
	?>
		
		<br />
		<input type="hidden" name="create_file" value="true" />
		<input type="submit" value="Create Web Tools Config file" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>