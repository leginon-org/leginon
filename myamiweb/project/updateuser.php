<?
require("inc/project.inc.php");
require("inc/leginon.inc");
require("inc/user.inc.php");
login_header();
$user = new user();

$groups = $leginondata->getGroups('name');
$userId = ($_GET[id]) ? $_GET[id] : $_POST[userId];
$login_userId = getLoginUserId();
if (empty($userId) || !($user->checkUserExistsbyId($userId))) {
	if (privilege('users') < 4) redirect(BASE_URL.'accessdeny.php');
	$ptitle='- new user';
	$action='add';
	$f_date=date("j/n/Y");
} else {
	$curuser = $user->getUserInfo($userId);
	foreach($curuser as $k=>$f){
		$k = str_replace(' ','_', $k);
		$$k = $f;
  }
	$is_useradmin = ((privilege('users') > 3) || (privilege('users') >=2 && $login_userId==$userId));
	$ptitle ='- update user: '.$firstname.' '.$lastname;
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

$groupId = ($_POST['group'])? $_POST['group']:$groupId;
	if ($_POST['submit']=='add')
		$userId = $user->addUser($username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $groupId, $mypass1, $mypass2);
	else if ($_POST['submit']=='update')
		$user->updateUser($userId, $username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $groupId, $chpass, $mypass1, $mypass2);
		
#		header("location: user.php?uid=$userId");
} 
project_header("Projects $ptitle");
?>

<a href="javascript:history.back()">&laquo; back</a>
<p>
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
<?
$group_priv = privilege('groups');
$is_self = ($group_priv>=2 && $login_userId==$userId);
$login_is_groupadmin = (($group_priv == 4) || $is_self);
include('inc/userform.inc.php');
project_footer();
?>
