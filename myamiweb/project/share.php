<?
require("inc/project.inc.php");
require("inc/leginon.inc");
#require("inc/user.inc.php");
require("inc/share.inc.php");
#require_once("inc/mysql.php");

if ($_GET[cp])
	$selectedprojectId=$_GET[cp];
if ($_POST[currentproject])
	$selectedprojectId=$_POST[currentproject];
$project = new project();
$projects = $project->getProjects("order");

project_header("Experiment Sharing");

// Check user privileges
$sessionId = $_GET['id'];
checkExptAccessPrivilege($sessionId,'shareexperiments');
$is_admin = checkExptAdminPrivilege($sessionId,'shareexperiments');
?>

<form method="POST" name="projectform" action="<?=$_SERVER['REQUEST_URI'] ?>">
<input type="hidden" name="sessionId" value="<?= $sessionId ?>">

<h3>Selected Experiment </h3>
<table class="tableborder" border="1" valign="top">
<?
	$info = $leginondata->getSessionInfo($_GET['id']);
	$keys_to_display = array('Name', 'Purpose', 'Total Duration', 'Instrument', 'User');
	foreach ($info as $k=>$v) {
	if (!in_array($k, $keys_to_display))
		continue;
	echo "<tr> ";
	echo "<td> ";
	echo $k;
	echo "</td> ";
	echo "<td> ";
	echo $v;
	echo "</td> ";
	echo "</tr>\n";
	}
?>
</table>
<h3>Select a user to share this experiment with:</h3>
<p>
<?
	if ($is_admin) {
?>
<img src="img/info.png"> Users with no password set won't be listed; go
to <a class="header" href="user.php">[user]</a> to update user's profile.
</p>
<?
	};
	
	// Functions to add and delete a shared user on button click
	$s = new share();
	$db = $s->mysql;
	$userId = $_POST['userId'];
	if ($_POST['bt']=="add") {
		if ($userId && $sessionId) {
			$s->share_session_add($userId, $sessionId);
		}
	} else if ($_POST['bt']=="remove" && $_POST['ck']) {
		$s->share_session_del($_POST['ck'], $sessionId);
	}


	// Create a drop down list of users with passwords
	$q = "select u.`DEF_id` as userId, u.* from UserData u "
			."where "
			."u.password<>'' "
			."order by `full name`";

	$users = $leginondata->mysql->getSQLResult($q);

	if ($is_admin) {
	?>
	<select name="userId">
	<?
		echo "<option value='default' > -- select user -- </option>";
		foreach($users as $user) {
			$s = ($user['userId']==$_POST['userId']) ? "selected" : "";
			$o = ($user['full name']) ? $user['full name'] : $user['name'];
			echo "<option value='".$user['userId']."' $s >"
					.$o
					."</option>\n";
			
		}
	?>
	</select>
	<?
	
	// Display the add button
	$bt_add= "<input class='bt1' type='submit' name='bt' value='add'>";
	echo $bt_add;
	
	if ($ln=$_GET['ln']) {
		echo "<a class=\"header\" href=\"$ln\"> Back to project list</a>";
	}
	} else {
	echo '<font color="red">[Login as owner or admin to change sharing]</font>';
	}
	echo "<br />";
	
	// Create a list of users that are sharing this experiment
	$q = "select * from shareexperiments where `REF|leginondata|SessionData|experiment`=".$info['SessionId'];
	$r = $project->mysql->getSQLResult($q);
	foreach ($r as $v) {
		$sql_users[] = "`DEF_id`='".$v['REF|leginondata|UserData|user']."'";
	}
	if ($sql_users) {	
	$q = "select u.DEF_id as userId, u.* from ".DB_LEGINON.".`UserData` as u where ".join(' OR ', $sql_users);

	$r = $project->mysql->getSQLResult($q);
	echo "<br>";
	
	// Display the users that this experiment has been shared with
	if (!empty($r)) {
		echo "Experiment shared with: <br>";
	}
	echo "<table>";
	foreach ($r as $v) {
		$ck = "<input type='checkbox' name='ck[]' value='".$v['userId']."'>";
		$cuser = ($v['full name']);
#		$cuser = ($v['lastname']||$v['firstname']) ? $v['lastname']." ".$v['firstname']:$v['login'];
		echo "<tr>";
		echo "<td>";
		echo $ck."  ".$cuser;
		echo "</td>";		
		echo "</tr>";
	}
	echo "</table>";
	
	// Add a delete button if the user is logged in as Admin/Owner
	$bt_del = "<input class='bt1' type='submit' name='bt' value='remove'>";
	echo "<br>";
		if ($is_admin && !empty($r)) {
			echo $bt_del;
		}
	}
	
?>
</form>
<?
project_footer();
?>
