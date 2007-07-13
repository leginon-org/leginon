<?php

/**
 *	The Appion software is Copyright 2007
 *	The Scripps Research Institute, La Jolla, CA
 */

function parseAppionLoopParams () {
	$norejects = ($_POST[norejects]=="on") ? "1" : "0";
	$nowait = ($_POST[nowait]=="on") ? "1" : "0";
	$commit = ($_POST[commit]=="on") ? "1" : "0";
	$background = ($_POST[background]=="on") ? "1" : "0";
	$shuffle = ($_POST[shuffle]=="on") ? "1" : "0";
	$limit = $_POST[limit];
	$apcontinue = $_POST[apcontinue];

	if (!$norejects) $command.=" norejects";
	if (!$nowait) $command.=" nowait";
	if ($commit) $command.=" commit";
	if ($background) $command.=" background";
	if ($shuffle) $command.=" shuffle";
	if ($limit) $command.=" limit=$limit";
	if ($apcontinue == 'yes') $command.=" continue";
	elseif ($apcontinue == 'no') $command.=" nocontinue";

   return $command;
}

function createAppionLoopTable () {
	echo "<!-- BEGIN Appion Loop Param -->";
//	prettytable2();
//	<TR><TD BGCOLOR=#660000 ALIGN=CENTER><FONT COLOR=#DDDDDD>Appion Loop Params</FONT></TD></TR>
	echo "
<HR style='margin: 1em 1em 1em 0; border: 1px #333333 solid;
 border-collapse: collapse;'>

<INPUT TYPE='checkbox' NAME='norejects' $norejects>
Process rejected images<BR>

<INPUT TYPE='checkbox' NAME='nowait' $nowait checked>
Wait for more images after finishing<BR>

<INPUT TYPE='checkbox' NAME='commit' $commit>
Commit results to database<BR>

<INPUT TYPE='checkbox' NAME='background' $background>
Run in background mode<BR>

<INPUT TYPE='checkbox' NAME='shuffle' $shuffle>
Shuffle the images<BR>

Only process&nbsp;
<INPUT TYPE='text' NAME='limit' VALUE='$limit' SIZE='4'>&nbsp;
images<BR>

Continue?<BR>
<INPUT TYPE='radio' NAME='apcontinue' VALUE='yes' checked>
Continue unfinished run<BR>
<INPUT TYPE='radio' NAME='apcontinue' VALUE='no'>
Reprocess all images<BR>

";
	echo "<!-- END Appion Loop Param -->";
};

function prettytable2 () {
	echo "
<TABLE border=2 cellpadding=2 cellspacing=0 
 style='margin: 1em 1em 1em 0; border: 1px #333333 solid;
 border-collapse: collapse; text-align: left;'>
";
};
?>
