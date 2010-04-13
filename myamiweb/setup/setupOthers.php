<?php

require_once('template.inc');
require_once('setupUtils.inc');

	$template = new template;
	$template->wizardHeader("Step 4 : Others setup for web tools");
	
?>

	<form name='wizard_form' method='POST' action='review.php'>

	<?php 
		foreach ($_POST as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
	?>
		
		<h3>Do you want to enable the image processing pipeline (Appion)</h3>
		<p>Select "YES" if you want to use Appion image processing.</p>
		<p>PS: Other processing software installation required.</p>
		<input type="radio" name="processing" value="true" />&nbsp;&nbsp;YES<br />
		<input type="radio" name="processing" value="false" />&nbsp;&nbsp;NO<br />
		
		<br />
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>