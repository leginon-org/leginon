<?
require "inc/project.inc.php";
require_once("inc/leginon.inc");
require_once "inc/user.inc.php";
require_once "inc/utilpj.inc.php";

//if ($_GET['cp'])
//	$selectedprojectId=$_GET['cp'];
$orderBy = $_GET['sort'];

//if ($_POST['currentproject'])
//	$selectedprojectId=$_POST['currentproject'];

$login_check = $dbemauth->is_logged();

$is_admin = (privilege('users')>3);
login_header('User');
$userdata = new user();
$users = $userdata->getUsers($orderBy);

foreach ($users as $k=>$p) {
	$email = $p['email'];
	$userId = $p['userId'];
	if ($is_admin) {
		$users[$k]["edit"]="<a href='updateuser.php?userId=$userId'><img border='0' src='img/edit.png'></a>";
		//$users[$k]["del"]="<a href='deleteuser.php?userId=$userId'><img border='0' src='img/del.png'></a>";
	}
	//$users[$k]["name"]=$p['lastname'].(($p['firstname'])? ', '.$p['firstname']:'');
	$users[$k]["lastname"]=$p['lastname'];
	$users[$k]["firstname"]=$p['firstname'];
	$users[$k]["username"]=$p['username'];
	$users[$k]["email"]="<a href='mailto:$email'>".$p['email']."</a>";
	$users[$k]["institution"]=$p['institution']." ".$p['dept']." ".$p['address'];
	$users[$k]["phone"]=$p['phone'];
}

$columns=array(
	'lastname'=>'Lastname',
	'firstname' => 'Firstname',
	'email'=>'Email',
	'username'=>'Username',
	'institution'=>'Institution',
	'phone'=>'Phone');
$display_header=true;

if ($is_admin) {
	$columns=array_merge(array('edit'=>''), $columns);
}

project_header("Users");
if ($is_admin) {
	echo "<a class='header' href='updateuser.php'>Add new user</a>"; 
}
echo " - currently ".count($users)." users";
echo data2table($users, $columns, $display_header);
project_footer();
?>
