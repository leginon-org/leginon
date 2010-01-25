<?
require "inc/authconfig.inc.php";

class authlib extends config_class {


	function register ($username, $password, $password2, $email, $lastname, $firstname="") {

		if (!$username || !$password || !$password2 || !$email || !$lastname) {

			return $this->error['fields_empty'];

		}

		else {

			if (!eregi("^[a-z ]+$", $lastname)) {

				return $this->error['name_invalid'];

			}

			$this->filter_email($email);

			$this->filter_username($username);

			if ($password != $password2) {

				return $this->error['passwd_not_match'];

			}

			$this->filter_password($password);


			$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);

			if (!get_magic_quotes_gpc()) {
				$username=addslashes($username);
			}

			$q="select id from `".$this->tbl_login."` where username = '$username'";
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
			$hash = md5($this->secret.$username.$now);
			$data=array();
			$data['mdhash']=$hash;
			$data['username']=$username;
			$data['password']=$password;
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
				.$this->server_url."/confirm.php?hash=$hash\n\n"
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

		$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);
		$dbc->SQLUpdate($this->tbl_user, $data, $where);

		if ($chpass)
			$this->updatePassword($userId, $password);

		return 2;
	}

	function updatePassword($userId, $password) {
		$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);
		$data['password']=$password;
		$where['userId']=$userId;
		return $dbc->SQLUpdate($this->tbl_login, $data, $where);
	}

	function getInfo($username) {

			$this->filter_username($username);

			if (!get_magic_quotes_gpc()) {
					$username = addslashes($username);
			}

			$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);
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

		$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);
    $sqlwhere = (is_numeric($userId)) ? "userId=$userId" : "username='$userId'";
    $q='select *  '
      .'from login '
      .'where '.$sqlwhere;

		list($r)=$dbc->getSQLResult($q);
		return ($r['password']) ? true : false;
  }

	function login ($username, $password) {

		if (!$username || !$password) {

			return $this->error['fields_empty'];

		} else {

			$this->filter_username($username);

			$this->filter_password($password);

			$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);


			if (!get_magic_quotes_gpc()) {
				$password=addslashes($password);
				$username=addslashes($username);
			}

			$q="select id, privilege from `".$this->tbl_login."` where username = '$username' and password = '$password'";
			$query=$dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);

			if ($result < 1) {

				return false;

			}

			else {

				list ($id, $privilege) = mysql_fetch_row($query);

				$hash = md5($username.$id.$privilege.$this->secret);
				$expire = ($this->cookie_expire) ? time()+$this->cookie_expire : 0;

				setcookie($this->authcook, "$username:$hash", $expire);

				return 2;

			}

		}

	}

	function is_logged () {

		global $_COOKIE;
		$cookie = $_COOKIE[$this->authcook];

		$session_vars = explode(":", $cookie);
		$username = $session_vars[0];

		$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);

		$q="select id, privilege from `".$this->tbl_login."` where username = '$username'";
		$query=$dbc->SQLQuery($q);
		$result = @mysql_num_rows($query);

		if ($result < 1) {

			return false;

		}


		list ($id, $privilege) = mysql_fetch_row($query);

		$hash = md5($session_vars[0].$id.$privilege.$this->secret);

		if ($hash != $session_vars[1]) {

			return false;

		} else {

			return array($session_vars[0], $id, $privilege);

		}

	}

	function logout () {

		setcookie($this->authcook, "", time()-3600);

		header("Location: $this->logout_url");

	}

	function confirm ($hash) {

		if (!$hash || strlen($hash)!=32) {

			return $this->error['hash_invalid'];

		} else {

			$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);
			$q="select username from `".$this->tbl_login."` where md5(concat('".$this->secret."', username, date))='$hash' ";
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

	function lostpwd ($emailorlogin) {

		if (!$emailorlogin) {

			return $this->error['fields_empty'];

		}

		$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);

		$q="select l.userid, l.password, l.username, d.email from `".$this->tbl_login."` l,"
			."`".$this->tbl_user."` d where (d.email='$emailorlogin' or l.username='$emailorlogin') and l.userId = d.userId ";
		$query = $dbc->SQLQuery($q);
		$result = @mysql_num_rows($query);

		$insertpasswordentry=false;
		if ($result < 1) {
				$q="select l.userid, l.password, l.username, l.email from "
					."`".$this->tbl_user."` l "
					."where (l.email='$emailorlogin' or l.username='$emailorlogin') ";
				$query = $dbc->SQLQuery($q);
				$result = @mysql_num_rows($query);

				if ($result < 1) {
					return $this->error['username_email'];
				}
				$insertpasswordentry=true;
		}

		list($userId, $password, $username, $email) = mysql_fetch_row($query);
		if (!$email) {
			return $this->error['no_email'];
		}

		if (!$password) {
			$password=$this->generatePassword();
			if($insertpasswordentry) {
				$data=array();
				$data['userId']=$userId;
				$data['username']=$username;
				$data['password']=$password;
				$dbc->SQLInsertIfNotExists($this->tbl_login, $data, true);
			} else {
				$this->updatePassword($userId, $password);
			}
		}

		@mail($email, "Account Info", "Dear User,\n\nAs per your request here is your account information:\n
 Username: $username
 Password: $password
				\nWe hope you remember your password next time ;-)", "From: $this->webmaster");

		return 2;

	}

	function chemail ($id, $email, $email2) {

		if ($email != $email2) {

			return $this->error[14];

		} else {

			if (!eregi("^([a-z0-9]+)([._-]([a-z0-9]+))*[@]([a-z0-9]+)([._-]([a-z0-9]+))*[.]([a-z0-9]){2}([a-z0-9])?$", $email)) {

				return $this->error[4];

		}

			$dbc=new mysql($this->server, $this->db_user, $this->db_pass, $this->database);

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

			$mdhash = md5($id.$email.$this->secret);

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

			mysql_connect($this->server, $this->db_user, $this->db_pass);
			mysql_select_db($this->database);

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

		mysql_connect($this->server, $this->db_user, $this->db_pass);
		mysql_select_db($this->database);

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

			mysql_connect($this->server, $this->db_user, $this->db_pass);
			mysql_select_db($this->database);

			$query = mysql_query("update `".$this->tbl_login."` set password = '$password' where id = '$id'");

			mysql_close();

			if (!$query) {

				return $this->error[21];

			}

			return 2;

		}

	}

	function delete($id) {

		mysql_connect($this->server, $this->db_user, $this->db_pass);
		mysql_select_db($this->database);

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
