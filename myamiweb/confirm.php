<?php
require "inc/login.inc";

// if user already login, redirect to homepage
if ($login_check = $dbemauth->is_logged()) {
	header('Location: '.BASE_URL);
}

$hash=$_GET['hash'];

$username=$_GET['username'];

$confirm = $dbemauth->confirm($hash);

login_header("Appion / Leginon Register Confirmation");
?>
	<style>
	li {
   		list-style: none; padding:2px;
	}
	</style>
	<center><h1><?php echo PROJECT_TITLE; ?></h1></center>
	<hr/>
	<div>
<?php 
if ($confirm != 2) {
?>
	<p align="center"><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">
             <?php echo $confirm; ?>
        </font></p>
<?php 
} else {
?>
	<p align="center"><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">
            <?php echo $username; ?>registration has been confirmed
         </font></p>
	<p align="center"><font face="Arial, Helvetica, sans-serif" size="4">
            You can login by using your 'username' and 'password'.<br>
            Thanks.
         </font></p>    
<?php      
}
echo "</div>";
login_footer();
?>
