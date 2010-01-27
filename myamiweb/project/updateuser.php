<?
require("inc/project.inc.php");
require("inc/leginon.inc");
require("inc/user.inc.php");
login_header();
$user = new user();

$groups = $leginondata->getGroups('name');
$userId = ($_GET[id]) ? $_GET[id] : $_POST[userId];
if (empty($userId) || !($user->checkUserExistsbyId($userId))) {
	$ptitle='- new user';
	$action='add';
	$f_date=date("j/n/Y");
} else {
	$curuser = $user->getUserInfo($userId);
	list($curlogin) = $user->getLoginInfo($userId);
	foreach($curuser as $k=>$f){
		$k = str_replace(' ','_', $k);
		$$k = $f;
  }
	$enable_admin_ckeck = ($curlogin['privilege']==2) ? "checked" : "";
	$ptitle ='- update user: '.$first_name.' '.$last_name;
	$action='update';
	$checkpass=true;
	$nopass=(strlen($curuser['password'])) ? false : true;
}

if ($_POST[submit]) {
	foreach($_POST as $k=>$v)
		if ($k!='submit')
			$$k = $v;

	if ($nopass)
		$chpass=true;

		$priv = ($enable_admin) ? 2 : 0;
	if ($_POST['submit']=='add')
		$userId = $user->addUser($username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $mypass1, $mypass2, $priv);
	else if ($_POST['submit']=='update')
		$user->updateUser($userId, $username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $chpass, $mypass1, $mypass2, $priv);
		
#		header("location: user.php?uid=$userId");
} 
project_header("Projects $ptitle");
?>

<a href="javascript:history.back()">&laquo; back</a>
<p>
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
<?
$login_is_admin = (privilege() == 2);
include('inc/userform.inc.php');
project_footer();
?>
