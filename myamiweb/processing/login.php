<?php
require "inc/particledata.inc";
require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

if ($_POST['login']) {
  $errors=checkLogin();
  if ($errors) loginform($errors);
  $previous=$_GET['prev'];
  if ($_GET['expId']) $previous.="?expId=$_GET[expId]";
  header("location:$previous");
}

loginform();

function loginform($extra=false) {
    processing_header('Appion Login','Appion Login',false,false);
    $formAction=$_SERVER['PHP_SELF'];
    $expId=$_GET['expId'];
    $prev=$_GET['prev'];
    if ($expId) $formAction.="?expId=$expId";
    if (!$expId && $prev) $formAction.="?prev=$prev";
    if ($expId && $prev) $formAction.="&prev=$prev";

    if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

    displayLogin($formAction);

    processing_footer();
    exit;
  }
?>
