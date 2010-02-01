<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "config.php";
require_once "inc/authconfig.inc.php";

class authlib extends config_class {

	var $error = array (
				 "passwd_not_match"=>"Passwords do not match each other",
				 "passwd_short"=>"Password is too short. Minimum is 3 valid characters.",
				 "passwd_long"=>"Password is too long. Maximum is 20 valid characters.",
				 "passwd_invalid"=>"Password contains invalid characters.",
				 "username_exists"=>"Username already exists.",
				 "username_email_exists"=>"A user with that email already exists.",
				 "username_short"=>"Username is too short. Minimum is 3 valid characters.",
				 "username_long"=>"Username is too long. Maximum is 11 valid characters.",
				 "username_invalid"=>"Username contains invalid characters.",
				 "email_invalid"=>"Email address format is invalid.",
				 "name_invalid"=>"Name contains invalid characters.",
				 "hash_invalid"=>"Hash is not valid.",
				 "fields_empty"=>"Some fields were left empty.",
				 "temp_username_incorrect"=>"Temporary ID and Username combination incorrect, or account purged.",
				 "database_error"=>"Unknown database failure, please try later.",
				 "flushing"=>"The flushing process was unsuccessful.",
				 "username_email"=>"No username corresponding to that email.",
				 "no_email"=>"no such email address in our system. ",
				 "database_err1"=>"Your registration details could not be updated.",
				 "database_err2"=>"Your password could not be updated due to a database fault.",
				 "emails_not_match"=>"Your emails do not match.",
				 "emails_match"=>"I think your current email and the email you entered for modification are same hence I can't change anything."
				 );

	function register ($username, $password, $password2, $email, $lastname, $firstname) {
		if (!$username || !$password || !$password2 || !$email || !$lastname || !$firstname) {

			return $this->error['fields_empty'];

		}

		else {

			if (!eregi("^[a-z ]+$", $lastname)) {

				return $this->error['name_invalid'];

			}
			
			if(!eregi("^[a-z ]+$", $firstname)) {

				return $this->error['name_invalid'];

			}
			
			$this->filter_email($email);

			$this->filter_username($username);

			if ($password != $password2) {

				return $this->error['passwd_not_match'];

			}

			$this->filter_password($password);

			
			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);

			if (!get_magic_quotes_gpc()) {
				$username=addslashes($username);
			}

			$q="select DEF_id from `".$this->tbl_user."` where name = '$username'";
			$query = $dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);

			if ($result > 0) {

				return $this->error['username_exists'];

			}
			
			$q="select email from `".$this->tbl_user."` where email = '$email'";
			$query = $dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);

			if ($result > 0) {

				return $this->error['username_email_exists'];

			}
			
			$now=date('Y-m-d H:i:s', time());
			$hash = md5($username.$now);
			$data=array();
			$data['mdhash']=$hash;
			$data['username']=$username;
			$data['password']=md5($password);
			$data['firstname']=$firstname;
			$data['lastname']=$lastname;
			$data['email']=$email;
			$data['date']=$now;
			$is_success=$dbc->SQLInsertIfNotExists($this->tbl_confirm, $data);

			if (!$is_success) {

				return $this->error['database_error'];

			}

			@mail($email, $this->config_reg_subj, "Thank You, $name for registering. Here is the information we received :\n\n"
				."Name     : $lastname $firstname \n"
				."Email    : $email\n"
				."Username : $username\n"
				."Password : $password \n\n"
				."	You need to confirm the account by pointing your browser at \n"
				."/confirm.php?hash=$hash\n\n"
				."If you did not apply for the account please ignore this message.", "From: ".$this->webmaster);

			return 2;

		}

	}

	function updateUser($userId, $username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $chpass, $password, $password2) {

		if (!$username || !$lastname) {

			return $this->error['fields_empty'];

		}

		if (!eregi("^[a-z ]+$", $lastname)) {

			return $this->error['name_invalid'];

		}

		$this->filter_username($username);

		$this->filter_email($email);
		
		if ($chpass) {

		if ($password != $password2) {

			return $this->error['passwd_not_match'];

		}

		$this->filter_password($password);

		}


		$data=array();
		$data['username']=$username;
		$data['firstname']=$firstname;
		$data['lastname']=$lastname;
		$data['title']=$title;
		$data['institution']=$institution;
		$data['dept']=$dept;
		$data['address']=$address;
		$data['city']=$city;
		$data['statecountry']=$statecountry;
		$data['zip']=$zip;
		$data['phone']=$phone;
		$data['fax']=$fax;
		$data['email']=$email;
		$data['url']=$url;

		$where['userId']=$userId;

		if (!is_numeric($userId) && $userId) {
			return "userId not valid";
		}

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);
		$dbc->SQLUpdate($this->tbl_user, $data, $where);

		if ($chpass)
			$this->updatePassword($userId, $password);

		return 2;
	}

	function updatePassword($userID, $password) {
		
		$dbc = new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);

		$q = "update UserData set password = '$password' where DEF_id = $userID";
		
		if(!$dbc->SQLQuery($q))
			return false;
		return true;
	}

	function getInfo($username) {

			$this->filter_username($username);

			if (!get_magic_quotes_gpc()) {
					$username = addslashes($username);
			}

			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);
			$q="select "
				."u.userId, u.username, u.firstname, u.lastname,"
				."u.title, u.institution, u.dept, u.address, u.city,"
				."u.statecountry, u.zip, u.phone, u.fax, u.url "
				."from `".$this->tbl_user."` u "
				."where username = '$username'";

			list($r)=$dbc->getSQLResult($q);
			return $r;
	}

	function hasPassword($userId) {

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);
    $sqlwhere = (is_numeric($userId)) ? "userId=$userId" : "username='$userId'";
    $q='select *  '
      .'from login '
      .'where '.$sqlwhere;

		list($r)=$dbc->getSQLResult($q);
		return ($r['password']) ? true : false;
  }

	function login ($username, $password) {

		if (empty($username) || empty($password)) {

			return $this->error['fields_empty'];

		} else {
			$this->filter_username($username);

			$this->filter_password($password);

			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);

			if (!get_magic_quotes_gpc()) {
				$password=addslashes($password);
				$username=addslashes($username);
			}

			$q="select DEF_id from UserData where username = '$username' and password = '$password'";
			
			$query=$dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);
			
			if ($result != 1) {
				return false;
			}

			else {
				$hash = md5($username);
				$expire = (COOKIE_TIME) ? time()+COOKIE_TIME : 0;

				setcookie(PROJECT_NAME, "$username:$hash", COOKIE_TIME);
				return 2;

			}

		}
	}

	function is_logged () {

		global $_COOKIE;
		$cookie = $_COOKIE[PROJECT_NAME];

		$session_vars = explode(":", $cookie);
		$username = $session_vars[0];

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);

		$q="select u.DEF_id, g.privilege from UserData as u "
			."left join GroupData as g "
			."on u.`REF|GroupData|group` = g.`DEF_id` "
			."where u.username = '$username'";
		$query=$dbc->SQLQuery($q);
		
		$result = @mysql_num_rows($query);

		if ($result < 1) {

			return false;

		}

		list ($id, $privilege) = mysql_fetch_row($query);

		$hash = md5($session_vars[0]);

		if ($hash != $session_vars[1]) {

			return false;

		} else {

			return array($session_vars[0], $id, $privilege);

		}

	}

	function logout () {

		setcookie(PROJECT_NAME, "", time()-3600);
		
		header("Location: $this->logout_url");

	}

	function confirm ($hash) {

		if (!$hash || strlen($hash)!=32) {

			return $this->error['hash_invalid'];

		} else {

			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);
			$q="select username from `".$this->tbl_login."` where md5(concat(username, date))='$hash' ";
			list($r) = $dbc->getSQLResult($q);
			$username=$r['username'];

			$q="select userId from `".$this->tbl_login."` where username = '$username'";
			$query = $dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);

			if ($result > 0) {
				return $this->error['username_exists'];
			}

			$q="select username, password, firstname, lastname, email, date from "
				."`".$this->tbl_confirm."` "
				."where mdhash = '$hash'";
			$query = $dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);

			if ($result < 1) {

				return $this->error['database_err1'];

			}

			list($username,$password,$firstname,$lastname,$email,$date) = mysql_fetch_row($query);

			$data=array();
			$data['username']=$username;
			$data['firstname']=$firstname;
			$data['lastname']=$lastname;
			$data['email']=$email;
			$userId=$dbc->SQLInsertIfNotExists($this->tbl_user, $data, true);

			if ($userId) {

				$data=array();
				$data['userId']=$userId;
				$data['username']=$username;
				$data['password']=$password;
				$data['date']=$date;
				$is_success_second=$dbc->SQLInsertIfNotExists($this->tbl_login, $data, true);
				if ($is_success_second) {
					$is_success_third = $dbc->SQLDelete($this->tbl_confirm, array('username'=>$username));
				}

			}

			if (!$userId) {

				return $this->error['database_err1'];

			}

			if (!$is_success_second) {

				return $this->error['database_err1'];

			}

			if (!$is_success_third) {

				return $this->error['database_err1'];

			}

			$name="$firstname $lastname";
			@mail($email, "$this->wsname Confirmation", "Thank You, $name for registering. Here is the information we received :\n
					\nName     : $name
					\nEmail    : $email
					\nUsername : $username
					\nPassword : $password\n", "From: $this->webmaster");

			return 2;

		}

	}

	function conf_flush () {


		$q="delete from `".$this->tbl_confirm."` where date_add(date, interval 2 day) < now()";

		if (!$query) {

			return $this->error['flushing'];

		}

		return 2;

	}

	function lostpwd ($email) {

		// check input variable has value
		if (empty($email)) {
			return $this->error['fields_empty'];
		}

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);

		$q="select DEF_id, username, email from UserData where email = '$email'";

		$query = $dbc->SQLQuery($q);
		$result = @mysql_num_rows($query);

		// setup query result value and assign to those variables
		list($userID, $username, $email) = @mysql_fetch_row($query);

		if (!$email) {
			return $this->error['no_email'];
		}
		
		// generate new password for user
		$password=$this->generatePassword();
		
		// assign new password to this user
		$result = $this->updatePassword($userID, $password);

		// sent out email with necessary information.

		$subject = "Forget password: Account Infomation";
		$headers = "From: ". WEBMASTER;
		$message = "Dear User,\n\nAs per your request here is your account information:\n
				Username: $username
 				Password: $password
 				\nYou can use this password to login and update your password later.
				\nWe hope you remember your password next time ;-)"; 

		@mail($email, $subject, $message, $headers);
		return 2;

	}

	function chemail ($id, $email, $email2) {

		if ($email != $email2) {

			return $this->error[14];

		} else {

			if (!eregi("^([a-z0-9]+)([._-]([a-z0-9]+))*[@]([a-z0-9]+)([._-]([a-z0-9]+))*[.]([a-z0-9]){2}([a-z0-9])?$", $email)) {

				return $this->error[4];

		}

			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_DBEMDATA);

			$q="select id from `".$this->tbl_user."` where email = '$email'";
			$query = $dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);

			if ($result > 0) {

				list($id_from_db) = mysql_fetch_row($query);

				if ($id_from_db != $id) {

					return '$this->error[13]';

				}

				return '$this->error[23]';

			}

			$mdhash = md5($id.$email);

			$q="insert into `".$this->tbl_confirm_email."` values ('$id', '$email', '$mdhash', now())";
			$query = $dbc->SQLQuery($q);

			if (!$query) {

				'$this->error[20]';

			}

			@mail($email, "$this->wsname Email Change", "Dear User, You have requested an email change \n
						   in our database. We, to ensure authenticity of the email\n
						   expect you to goto $this->server_url/confirm_email.php?mdhash=$mdhash&id=$id&email=$email
						   \n Thank You!");

			return 2;

		}

	}

	function confirm_email($id, $email, $mdhash) {

		if (!$id || !$email || !$mdhash) {

			return '$this->error[14]';

		}

		else {

			mysql_connect(DB_HOST, DB_USER, DB_PASS);
			mysql_select_db(DB_DBEMDATA);

			$query = mysql_query("select * from `".$this->tbl_confirm_email."` where id = '$id' AND email = '$email' AND mdhash = '$mdhash'");
			$result = @mysql_num_rows($query);

			if ($result < 1) {

				mysql_close();

				return $this->error[15];

			}

			$update = mysql_query("update `".$this->tbl_user."` set email = '$email' where id = '$id'");
			$delete = mysql_query("delete from `".$this->tbl_confirm_email."` where email = '$email'");

			mysql_close();

			return 2;

		}

	}

	function email_flush () {

		mysql_connect(DB_HOST, DB_USER, DB_PASS);
		mysql_select_db(DB_DBEMDATA);

		$query = mysql_query("delete from `".$this->tbl_confirm_email."` where date_add(date, interval 2 day) < now()");

		mysql_close();

		if (!$query) {

			return $this->error[18];

		}

		return 2;

	}

	function chpass ($id, $password, $password2) {

		if ($password != $password2) {

			return $this->error[0];

		}

		else {

			if (strlen($password) < 5) {

				return $this->error[5];

			}

			if (strlen($password) > 20) {

				return $this->error[6];

			}

			if (!ereg("^[[:alnum:]_-]+$", $password)) {

				return $this->error[7];

			}

			mysql_connect(DB_HOST, $this->db_user, DB_PASS);
			mysql_select_db(DB_DBEMDATA);

			$query = mysql_query("update `".$this->tbl_login."` set password = '$password' where id = '$id'");

			mysql_close();

			if (!$query) {

				return $this->error[21];

			}

			return 2;

		}

	}

	function delete($id) {

		mysql_connect(DB_HOST, $this->db_user, DB_PASS);
		mysql_select_db(DB_DBEMDATA);

		$query = mysql_query("delete from `".$this->tbl_login."` where id = '$id'");
		$query = mysql_query("delete from `".$this->tbl_user."` where id = '$id'");

		mysql_close();

		return 2;

	}

	function filter_password($val) {

			if (strlen($val) < 3) {

				return $this->error['passwd_short'];

			}

			if (strlen($val) > 20) {

				return $this->error['passwd_long'];

			}

			if (!ereg("^[\*@[:alnum:]._-]+$", $val)) {

				return $this->error['passwd_invalid'];

			}
	}

	function filter_username($val) {

			if (strlen($val) < 3) {

				return $this->error['username_short'];

			}

			if (strlen($val) > 20) {

				return $this->error['username_long'];

			}

			if (!ereg("^[[:alnum:]_]+$", $val)) {

				return $this->error['username_invalid'];

			}

	}

	function filter_email($val) {

			if (!eregi("^([a-z0-9]+)([._-]([a-z0-9]+))*[@]([a-z0-9]+)([._-]([a-z0-9]+))*[.]([a-z0-9]){2}([a-z0-9])?$", $val)) {

				return $this->error['email_invalid'];

			}
	}

	function generatePassword($length=6) {

		$vowels = 'aeuy';
		$chars = 'bdghjmnpqrstvz'.'0123456789';
		$lvowels=strlen($vowels);
		$lchars=strlen($chars);
		$password = '';

		foreach(range(1,$length) as $k) {
			$strfunc=(rand()%2) ? 'strtolower' : 'strtoupper';
			$alt=(rand()%2) ? true: false;
			$c=($alt) ? $chars[(rand() % $lchars)] : $vowels[(rand() % $lvowels)];
			$password .= $strfunc($c);
		}

		return $password;

	}


}

function redirect($location = "index.php") {
        header("Location: $location");
        exit;
}

?>
