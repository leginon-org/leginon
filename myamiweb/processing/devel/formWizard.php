<?php

require_once('../../setup/template.inc');

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_GET['show']) {
	showForm();
} else {
	createForm();
}

function createForm()
{
	// obtain default values
	$toolname = $_POST['toolname'] ? $_POST['toolname'] : "New Appion Tool";


	$template = new template;
	$template->wizardHeader("Appion Form Generator", "../../css/setup.css");

	echo "<form name='wizard_form' method='POST' action='".$_SERVER['PHP_SELF']."?show=1'>\n";

	// Tool name
	echo $template->textEntry('Enter descriptive title for tool', 
		'toolname', 'New Appion Tool for Processing', $size=50);

	echo "<br/><br/><br/>\n";

	// Run prefix
	echo $template->textEntry('Default run prefix',
		'runprefix', 'appionrun', $size=15);

	// Run prefix
	echo $template->textEntry('Default run prefix',
		'runprefix', 'appionrun', $size=15);

	echo "<br/><br/><br/>\n";

	echo "<input type='submit' value='Generate form'/>\n";
	echo "</form>\n";

		
	$template->wizardFooter();
};


function showForm()
{
	foreach ($_POST as $field=>$value)
	{
		if ($value)
			echo "$field: $value<br/>\n";
	}
	echo "<pre>what up holmes!</pre>\n";
}
?>
