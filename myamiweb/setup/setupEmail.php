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
		
		if($_POST['enable_login'] == 'true'){
			$validator->addValidation("email_title", $_POST['email_title'], "req");
			$validator->addValidation("email_title", $_POST['email_title'], "alpha_s");
			$validator->addValidation("admin_email", $_POST['admin_email'], "email");
		}
		
		if($_POST['enable_smtp'] == 'true'){
			$smtpAuth = ($_POST['smtp_auth'] == 'true') ? true : false;
			
			$validator->addValidation("smtp_host", $_POST['smtp_host'], "req");
			$validator->addValidation("smtp_server", array( 'host' => $_POST['smtp_host'], 
															'email' => $_POST['admin_email'],
															'auth' => $smtpAuth, 
															'username' => $_POST['smtp_username'],
															'password' => $_POST['smtp_password']), "smtp");
		}
		
		if($_POST['smtp_auth'] == 'true'){
			$validator->addValidation("smtp_username", $_POST['smtp_username'], "req");
			$validator->addValidation("smtp_password", $_POST['smtp_password'], "req");
		}
		$validator->runValidation();
		$errMsg = $validator->getErrorMessage();
		
		if(empty($errMsg)){
			
			$_SESSION['post'] = $_POST;
			setupUtils::redirect('setupDatabase.php');
			
			exit();
		}		
	}
	
	$template = new template;
	$template->wizardHeader("Step 2 : Login System and Administrator Email Address", SETUP_CONFIG);
	
?>

	<script language="javascript">
	<!-- //

		function setLogin(obj){

			if(obj.value == "true"){
				
				wizard_form.email_title.style.backgroundColor = "#ffffff";
				wizard_form.email_title.readOnly = false;
				wizard_form.admin_email.style.backgroundColor = "#ffffff";
				wizard_form.admin_email.readOnly = false;
				wizard_form.enable_smtp[0].disabled = false;
				wizard_form.enable_smtp[0].checked = true;
				wizard_form.enable_smtp[1].disabled = false;
				
			}else{
				
				wizard_form.email_title.style.backgroundColor = "#eeeeee";
				wizard_form.email_title.readOnly = true;
				wizard_form.email_title.value = "";
				wizard_form.admin_email.style.backgroundColor = "#eeeeee";
				wizard_form.admin_email.readOnly = true;
				wizard_form.admin_email.value = "";
				wizard_form.enable_smtp[0].disabled = true;
				wizard_form.enable_smtp[0].checked = false;
				wizard_form.enable_smtp[1].disabled = true;
				wizard_form.enable_smtp[1].checked = false;
				wizard_form.smtp_host.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_host.readOnly = true;
				wizard_form.smtp_host.value = "";
				wizard_form.smtp_auth[0].disabled = true;
				wizard_form.smtp_auth[0].checked = false;
				wizard_form.smtp_auth[1].disabled = true;
				wizard_form.smtp_auth[1].checked = false;
				wizard_form.smtp_username.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_username.readOnly = true;
				wizard_form.smtp_username.value = "";
				wizard_form.smtp_password.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_password.readOnly = true;
				wizard_form.smtp_password.value = "";
			}		
		}
		function setReadOnly_SMTP(obj){

			if(obj.value == "true"){
				
				wizard_form.smtp_host.style.backgroundColor = "#ffffff";
				wizard_form.smtp_host.readOnly = false;
				wizard_form.smtp_auth[0].disabled = false;
				wizard_form.smtp_auth[0].checked = true;
				wizard_form.smtp_auth[1].disabled = false;

			}else{

				wizard_form.smtp_host.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_host.readOnly = true;
				wizard_form.smtp_host.value = "";
				wizard_form.smtp_auth[0].disabled = true;
				wizard_form.smtp_auth[0].checked = false;
				wizard_form.smtp_auth[1].disabled = true;
				wizard_form.smtp_auth[1].checked = false;
				wizard_form.smtp_username.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_username.readOnly = true;
				wizard_form.smtp_username.value = "";
				wizard_form.smtp_password.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_password.readOnly = true;
				wizard_form.smtp_password.value = "";
			}
		}

		function setReadOnly_AUTH(obj){

			if(obj.value == "true"){
				
				wizard_form.smtp_username.style.backgroundColor = "#ffffff";
				wizard_form.smtp_username.readOnly = false;
				wizard_form.smtp_password.style.backgroundColor = "#ffffff";
				wizard_form.smtp_password.readOnly = false;

			}else{
				wizard_form.smtp_username.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_username.readOnly = true;
				wizard_form.smtp_username.value = "";
				wizard_form.smtp_password.style.backgroundColor = "#eeeeee";
				wizard_form.smtp_password.readOnly = true;
				wizard_form.smtp_password.value = "";
				
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
	
		<h3>Enable Login System:</h3>		
		
		<p>You may enable the login feature to restrict access to Leginon and Appion projects.</p>
		 
		<input type="radio" name="enable_login" value="false" 
		<?php  
			if($_POST){
				($_POST['enable_login'] == 'false') ? print("checked='yes'") : print("");
			}else{
				($update) ? (ENABLE_LOGIN)? print("") : print("checked='yes'") : print("checked='yes'");
			}
		?> 
			onclick="setLogin(this)" />&nbsp;&nbsp;NO<br />
		<input type="radio" name="enable_login" value="true" 
		<?php 
			if($_POST){
				($_POST['enable_login'] == 'true') ? print("checked='yes'") : print("");
			}else{
				($update) ? (ENABLE_LOGIN)? print("checked='yes'") : print("") : print(""); 
			}
		
		
		?> 
			onclick="setLogin(this)" />&nbsp;&nbsp;YES<br />
		<br />
		<h3>Enter outgoing email subject line:</h3>
		<p>example: The Scripps Research Institute</p>
		<div id="error"><?php if($errMsg['email_title']) echo $errMsg['email_title']; ?></div>
		<input type="text" size=50 name="email_title" 
			<?php 
				if($_POST){
					print("value='".$_POST['email_title']."'");
				}else{			
					if($update && ENABLE_LOGIN === true) 
						print("value='".EMAIL_TITLE."'"); 
					else 
						print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
				}
			?> /><br /><br />
		<br />
		<h3>Enter administrator email address:</h3>
		<p>The web tools will use this email address to 
		send email to the web tools users.</p>
		<div id="error"><?php if($errMsg['admin_email']) echo $errMsg['admin_email']; ?></div>
		<input type="text" size=35 name="admin_email" 
			<?php
				if($_POST){
					print("value='".$_POST['admin_email']."'");
				}else{
					if($update && ENABLE_LOGIN === true)
						print("value='".ADMIN_EMAIL."'");
					else 
						print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
				}
			?> /><br /><br />
		<br />
		<div id="error"><?php if($errMsg['smtp_server']) echo $errMsg['smtp_server']."<br /><br />"; ?></div>
		<h3>Determine a mail server to send outgoing email:</h3>
		<p>Select "SMTP server" to enter your SMTP host information.<br />
		If your institution does not provide an SMTP server, please select "Use regular PHP mail" to use the local computer.</p>
		&nbsp;<input type="radio" name="enable_smtp" value="false" 
		<?php 
			if($_POST){
				($_POST['enable_login'] == 'false') ? print("disabled ") : (($_POST['enable_smtp'] == 'false') ? print("checked='yes'") : print(""));
			}else{
				($update && ENABLE_LOGIN === true) ? (ENABLE_SMTP)? print("") : print("checked='yes'") : print("disabled"); 
			}
		?> 
			onclick="setReadOnly_SMTP(this)" />&nbsp;&nbsp;I want to use regular PHP mail.<br />
		&nbsp;<input type="radio" name="enable_smtp" value="true" 
		<?php 
			if($_POST){
				($_POST['enable_login'] == 'false') ? print("disabled ") : (($_POST['enable_smtp'] == 'true') ? print("checked='yes'") : print(""));
			}else{
				($update && ENABLE_LOGIN === true) ? (ENABLE_SMTP)? print("checked='yes'") : print("") : print("disabled"); 
			}
		?> 
			onclick="setReadOnly_SMTP(this)" />&nbsp;&nbsp;I want to use our SMTP server.<br /><br />
		<br />
		
		<h3>Enter your SMTP host name:</h3>
		<p>example: mail.school.edu</p>
		<div id="error"><?php if($errMsg['smtp_host']) echo $errMsg['smtp_host']; ?></div>
		<input type="text" size=35 name="smtp_host" 
			<?php 
				if($_POST){
					($_POST['enable_smtp'] == 'true') ? print("value='".$_POST['smtp_host']."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
				}else{
					($update && ENABLE_SMTP === true) ? print("value='".SMTP_HOST."'") : print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
				}
			?> /><br /><br />
		<br />
		<h3>Does your SMTP server require authentication?</h3>
		<p>Check with your email administrator.<br />
		Select "Yes" if using authentication. "No" if authentication is not required.</p>
		&nbsp;<input type="radio" name="smtp_auth" value="false" 
		<?php 
			if($_POST){
				(($_POST['enable_smtp'] == 'false') || empty($_POST['enable_smtp'])) ? print("disabled ") : (($_POST['smtp_auth'] == 'false') ? print("checked='yes'") : print(""));
			}else{
				($update && ENABLE_SMTP === true) ? (SMTP_AUTH)? print("") : print("checked='yes'") : print("disabled"); 
			}
		?> 
			onclick="setReadOnly_AUTH(this)" />&nbsp;&nbsp;No.<br />
		&nbsp;<input type="radio" name="smtp_auth" value="true" 
		<?php 
			if($_POST){
				(($_POST['enable_smtp'] == 'false') || empty($_POST['enable_smtp'])) ? print("disabled ") : (($_POST['smtp_auth'] == 'false') ? print("") : print("checked='yes'"));
			}else{
				($update && ENABLE_SMTP === true) ? (SMTP_AUTH)? print("checked='yes'") : print("") : print("disabled"); 
			}
		?> 
			onclick="setReadOnly_AUTH(this)" />&nbsp;&nbsp;Yes.<br /><br />
		<br />
		<h3>Enter your SMTP Authentication Username and Password:</h3>
		<p>If your SMTP server requires authentication, You need to enter the username and password.</p>
		<div id="error"><?php if($errMsg['smtp_username']) echo $errMsg['smtp_username']; ?></div>
		
		&nbsp;Username: &nbsp;
		<input type="text" size=20 name="smtp_username" 
		<?php 
			if($_POST){
				if($_POST['smtp_auth'] == 'true') 
					print("value='".$_POST['smtp_username']."'");
				else
					print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
			}else{
				if($update && SMTP_AUTH === true) 
					print("value='".SMTP_USERNAME."'"); 
				else
					print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
			}
		?> /><br /><br />
		<div id="error"><?php if($errMsg['smtp_password']) echo $errMsg['smtp_password']; ?></div>
		&nbsp;Password: &nbsp;
		<input type="text" size=20 name="smtp_password" 
		<?php 
			if($_POST){
				if($_POST['smtp_auth'] == 'true') 
					print("value='".$_POST['smtp_password']."'");
				else
					print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
			}else{		
				if($update && SMTP_AUTH === true)
					print("value='".SMTP_PASSWORD."'");
				else
					print("readOnly=\"true\" style=\"background:#eeeeee\" value=\"\""); 
			}
		?> /><br /><br />
		<br />
		
		<input type="submit" value="NEXT" />

	</form>
	 
<?php 
		
	$template->wizardFooter();
?>