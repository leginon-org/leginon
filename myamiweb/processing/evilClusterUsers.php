<?php

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

$CLUSTER_HOSTNAME = "garibaldi.scripps.edu";

main();

/* ***********************************
*********************************** */
function searchScripps($searchstr, $eviluser) {
	$data = array ('s1' => $searchstr, 'operation' => 'search');
	$data = http_build_query($data);

	$context_options = array (
		'http' => array (
			'method' => 'POST',
			'header'=> "Content-type: application/x-www-form-urlencoded\r\n"
				. "Content-Length: " . strlen($data) . "\r\n",
			'content' => $data
		)
	);

	$context = stream_context_create($context_options);
	$fp = fopen('http://www.scripps.edu/directory/index.php', 'r', false, $context);
	$rawdata = '';
	while (!feof($fp)) {
		$buffer = fgets($fp, 1024);
		//echo $buffer."\n";
		if (!preg_match("/^<TR VALIGN/", $buffer))
			continue;
		if (!preg_match("/".$eviluser."/", $buffer))
			continue;
		$rawdata = $buffer;
		break;
	}
	fclose($fp);
	if (!$rawdata)
		return array();

	$opens = split(">", $rawdata);

	foreach ($opens as $rawopen) {
		if (substr($rawopen, 0, 36) != "<a href=\"index.php?operation=view&r=")
			continue;
		preg_match("/^<a href=\"(index.php\?operation=view\&r=[0-9]*)/", $rawopen, $matches);
		$faceurl = "http://www.scripps.edu/directory/".$matches[1];
		break;
		//echo $faceurl."<br/>\n";
	}
	unset($opens);

	$fp = fopen($faceurl, 'r', false);
	while (!feof($fp)) {
		$buffer = fgets($fp, 1024);
		//echo $buffer."\n";
		if (!preg_match("/^<tr><td align/", $buffer))
			continue;
		if (preg_match("/<img src=\"(hr_photos\/Pic.*\.JPG)\"/", $buffer, $matches)) {
			$imageurl = "http://www.scripps.edu/directory/".$matches[1];
			//echo $imageurl."<br/>\n";
		}
		if (preg_match("/Title :.*valign=top>(.*)<\/td><\/tr>/", $buffer, $matches)) {
			$title = $matches[1];
			//echo $title."<br/>\n";
			break;
		}
	}
	fclose($fp);

	return array('title'=>$title, 'imageurl'=>$imageurl);

};

/* ***********************************
*********************************** */
function getUserUsage($eviluser) {
	$usage = array(
		'totalnodes'=>0,
		'totaltasks'=>0, 
		'runnodes'=>0, 
		'runtasks'=>0, 
		'queuenodes'=>0, 
		'queuetasks'=>0, 
	);

	$cmd = "qstat -u ".$eviluser;
	$result = runCommand($cmd);
	$rawdatas = streamToArray($result);
	foreach ($rawdatas as $rawdata) {
		//echo print_r($rawdata)."<br/>\n";
		if (!preg_match("/^[0-9]+\./", $rawdata[0]))
			continue;
		$nodes = (int) $rawdata[5];
		$tasks = (int) $rawdata[6];
		$status = $rawdata[9];

		// stats
		$usage['totalnodes'] += $nodes;
		$usage['totaltasks'] += $tasks;
		if ($status == "R") {
			$usage['runnodes'] += $nodes;
			$usage['runtasks'] += $tasks;
		} elseif ($status == "Q") {
			$usage['queuenodes'] += $nodes;
			$usage['queuetasks'] += $tasks;
		} else {
			echo "Unknown status: $status<br/>\n";
		}
	}
	//echo $usage['totalnodes']."::".$usage['totaltasks']."<br/>\n";
	unset($rawdatas);
	return $usage;
};


/* ***********************************
*********************************** */
function runCommand($cmd) {
	global $CLUSTER_HOSTNAME;
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$result = exec_over_ssh($CLUSTER_HOSTNAME, $user, $pass, $cmd, True);
	return $result;
};

/* ***********************************
*********************************** */
function fingerUser($eviluser) {
	$cmd = "finger ".$eviluser;
	$result = runCommand($cmd);
	$rawdatas = streamToArray($result);
	foreach ($rawdatas as $rawdata) {
		if ($rawdata[0] != "Login:")
			continue;
		//echo print_r($rawdata)."<br/>\n";
		//echo $rawdata."<br/>\n";
		$fullname = $rawdata[3]." ".$rawdata[4];
		//echo $fullname."<br/>\n";
		unset($rawdatas);
		return $fullname;
	}
	unset($rawdatas);
	return 0;
}

/* ***********************************
*********************************** */
function getEvilUsers() {
	$cmd = "qstat | sed 's/  */ /g' | cut -f3 -d' ' | sort | uniq -c | sort -n | tail -30";
	$result = runCommand($cmd);

	$rawuserdatas = streamToArray($result);
	$evilusers = array();
	foreach ($rawuserdatas as $rawuserdata) {
		if ($rawuserdata[0] <= 1)
			continue;
		//echo $rawuserdata[1]."<br/>\n";
		$evilusers[] = $rawuserdata[1];
	}
	unset($rawuserdatas);
	return array_reverse($evilusers);
};

/* ***********************************
*********************************** */
function formatUser($eviluser, $fullname, $usage, $userinfo) {
	$userstring = "";
	$userstring .= "<table class='tablebubble'><tr><td>\n";
	if (array_key_exists('imageurl', $userinfo)) {
		$userstring .= "<a href='".$userinfo['imageurl']."'>\n";
		$userstring .= "  <img height='100' src='".$userinfo['imageurl']."'>\n";
		$userstring .= "</a><br/>\n";
	}
	$userstring .= "Name: ".$fullname."<br/>\n";
	$userstring .= "Title: ".$userinfo['title']."<br/>\n";
	$userstring .= "Email: $eviluser@scripps.edu<br/>\n";
	$userstring .= "Tasks: ".$usage['runtasks']." running (".$usage['queuetasks']." more queued)<br/>\n";
	$userstring .= "</td></tr></table>\n";
	return $userstring;
};

/* ***********************************
*********************************** */
function main() {
	$javascript = '';
	processing_header("Evil Cluster Users", "Evil Cluster Users", $javascript);

	// we have to be logged in
	$errors = checkLogin();
	if ($errors) {
		echo "<font color='#cc3333' size='+1'>$errors</font>\n";
		exit;
	}

	// get the evil users
	$evilusers = getEvilUsers();

	//foreach ($evilusers as $eviluser) {
	//	echo $eviluser."<br/>\n";
	//}

	// loop over users
	echo "<table cellpading='15'>\n";
	$count = 0;
	foreach ($evilusers as $eviluser) {

		//echo $eviluser."<br/>\n";

		$fullname = fingerUser($eviluser);

		$usage = getUserUsage($eviluser);

		// remove minor users
		if ($usage['totaltasks'] < 20)
			continue;

		$userinfo = searchScripps($eviluser, $eviluser);

		if ($count % 3 == 0)
			echo "<tr><td>\n";
		else
			echo "<td>\n";

		echo formatUser($eviluser, $fullname, $usage, $userinfo);

		if ($count % 3 == 2)
			echo "</td></tr>\n";
		else
			echo "</td><td></td>\n";
		$count ++;

	}
	echo "</table>\n";

	processing_footer();
	exit;

};

?>
