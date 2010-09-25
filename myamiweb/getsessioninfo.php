<?php
require("inc/mysql.inc");
require("config.php");

$baseurl=BASE_URL;


$db = &new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);


//If no search string is passed, then we can't search
if(empty($_GET['q'])) {
    echo '&nbsp;';
} else {
    //Remove whitespace from beginning & end of passed search.
    $search = split(' ',($_GET['q']));
	foreach ($search as $s) {
		$word = trim($s);
		if (!$word)
			continue;
		$sql_where[] = "(s.name LIKE '%".$word."%' OR "
			."s.comment LIKE '%".$word."%')";
	}
    //Query the DB and store the result in a variable
    $q = "select s.DEF_id as id, s.name,s.comment,count(a.`DEF_id`) as `nb` from SessionData s ";
    $q .= "left join AcquisitionImageData a ";
    $q .= "on (a.`REF|SessionData|session`=s.`DEF_id`) ";
		$q .= "where ".join(' AND ', $sql_where);
		$q .= " group by a.`REF|SessionData|session` ";
		$q .= " order by s.`DEF_id` desc ";
		$r = $db->getSQLResult($q);
    if($r) {
		echo count($r)." match".((count($r)>1)?"es":"")."<br>";
	foreach ($r as $row) {
	$link = $baseurl."summary.php?expId=".$row['id'];
	// $link_tomo = $baseurl."tomo/index.php?sessionId=".$row['id'];
	$link_iv = "<a href='".$baseurl."imageviewer.php?expId=".$row['id']."'>[view]</a>";
	$link_3wiv = "<a href='".$baseurl."3wviewer.php?expId=".$row['id']."'>[3w view]</a>";
	$link_rctiv = "<a href='".$baseurl."rctviewer.php?expId=".$row['id']."'>[rct]</a>";
        echo $link_iv.$link_rctiv." <b><a href=\"$link\">".$row['name']."</a></b> - ".$row['nb']." image".(($row['nb']>1)?"s":"")." - <i>".$row['comment']."</i><br>\n";
	}
    }else {
        echo 'Not Found.';
    }
}


?> 
