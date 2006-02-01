<?php
require_once('inc/mysql.inc');

function insertlog($ip, $host, $url, $sessionId) {
	$db = &new mysql(DB_HOST, DB_USER, DB_PASS, DB);
	$q = "insert into viewer_log (ip, host, url, sessionId) values "
		."('".$ip."', " ." '".$host."', " ." '".$url."', " ." '".$sessionId."') ";
	$db->sqlQuery($q);
	return true;
}
insertlog($_SERVER[REMOTE_ADDR], $_SERVER[REMOTE_HOST], $_SERVER[REQUEST_URI], $sessionId);

require("inc/authconfig.inc.php");

class authlib extends config_class {

	var $tbl_login = "login";
	var $tbl_user = "users";
	var $tbl_confirm = "";

	function register ($username, $password, $password2, $name, $email, $age, $sex, $school) {

		if (!$username || !$password || !$password2 || !$name || !$email || !$age || !$sex || !$school) {

			return $this->error[14];

		}

		else {

			if (!eregi("^[a-z ]+$", $name)) {

				return $this->error[8];

			}

			if (!eregi("^([a-z0-9]+)([._-]([a-z0-9]+))*[@]([a-z0-9]+)([._-]([a-z0-9]+))*[.]([a-z0-9]){2}([a-z0-9])?$", $email)) {

				return $this->error[4];

			}

			if (ereg("[^0-9]", $age)) {

				return $this->error[10];

			}

			if ($sex != "Male" && $sex != "Female") {

				return $this->error[11];

			}

			if (!eregi("^[a-z0-9 ]+$", $school)) {

				return $this->error[9];

			}

			if (strlen($username) < 3) {

				return $this->error[1];

			}

			if (strlen($username) > 20) {

				return $this->error[2];

			}

			if (!ereg("^[[:alnum:]_-]+$", $username)) {

				return $this->error[3];

			}

			if ($password != $password2) {

				return $this->error[0];

			}

			if (strlen($password) < 3) {

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

			$query = mysql_query("select id from `".$this->tbl_login."` where username = '$username'");
			$result = @mysql_num_rows($query);

			if ($result > 0) {

				mysql_close();

				return $this->error[12];

			}

			$query = mysql_query("select id from `".$this->tbl_user."` where email = '$email'");
			$result = @mysql_num_rows($query);

			if ($result > 0) {

				mysql_close();

				return $this->error[13];

			}

			$hash = md5($this->secret.$username);

			$is_success = mysql_query("insert into `".$this->tbl_confirm."` values ('$hash', '$username', '$password', '$name', '$email', '$age', '$sex', '$school', now())");

			mysql_close();

			if (!$is_success) {

				return $this->error[16];

			}

			@mail($email, $this->config_reg_subj, "Thank You, $name for registering. Here is the information we recieved :\n
				\nName     : $name
				\nEmail    : $email
				\nAge      : $age
				\nSex      : $sex
				\nSchool   : $school
				\nUsername : $username
				\nPassword : $password

				You need to confirm the account by pointing your browser at \n
				$this->server_url/confirm.php?hash=$hash&username=$username\n

				If you did not apply for the account please ignore this message.", "From: $this->webmaster");

			return 2;

		}

	}

	function login ($username, $password) {

		if (!$username || !$password) {

                        return $this->error[14];

		}

		else {

			if (!eregi("^[[:alnum:]_-]+$", $username)) {

				return $this->error[3];

			}

			if (!eregi("^[\*[:alnum:]_-]+$", $password)) {

				return $this->error[7];

			}

			mysql_connect($this->server, $this->db_user, $this->db_pass);
			mysql_select_db($this->database);

			$query = mysql_query("select id, privilege from `".$this->tbl_login."` where username = '$username' and password = '$password'");
			$result = @mysql_num_rows($query);

			mysql_close();

			if ($result < 1) {

				return false;

			}

			else {

				list ($id, $privilege) = mysql_fetch_row($query);

				$hash = md5($username.$this->secret);

				setcookie("authlib_basic", "$username:$hash:$id:$privilege", time()+3600, "/");

				return 2;

			}

		}

	}

	function is_logged () {

		global $HTTP_COOKIE_VARS;

		$session_vars = explode(":", $HTTP_COOKIE_VARS['authlib_basic']);

		$hash = md5($session_vars[0].$this->secret);

		if ($hash != $session_vars[1]) {

			return false;

		}

		else {

			return array($session_vars[0], $session_vars[2], $session_vars[3]);

		}

	}

	function logout () {

		setcookie("authlib_basic", "", time()-3600, "/");

		header("Location: $this->logout_url");

	}

        function edit_retrieve ($id) {

		mysql_connect($this->server, $this->db_user, $this->db_pass);
		mysql_select_db($this->database);

		$query = mysql_query("select * from `".$this->tbl_user."` where id = '$id'");

		mysql_close();

		list ($id, $name, $email, $age, $sex, $school) = mysql_fetch_row($query);

		return array($name, $age, $sex, $school, $email);

	}

	function edit ($id, $name, $age, $sex, $school) {

		if (!$name || !$age || !$sex || !$school) {

			return $this->error[14];

		}

		else {

			if (!eregi("^[a-z ]+$", $name)) {

				return $this->error[8];

			}

			if (!eregi("^[a-z0-9 ]+$", $school)) {
	
				return $this->error[9];

			}

			if (ereg("[^0-9]", $age)) {

				return $this->error[10];

			}

			if ($sex != "Male" && $sex != "Female") {

				return $this->error[11];

			}

        	        mysql_connect($this->server, $this->db_user, $this->db_pass);
			mysql_select_db($this->database);

			$query = mysql_query("update `".$this->tbl_user."` set name = '$name', age = '$age', sex = '$sex', school = '$school' where id = '$id'");

			mysql_close();

			if (!$query) {

				$this->error[20];

			}

			return 2;

		}

	}

	function confirm ($hash, $username) {

		if (!$hash || !$username) {

			return $this->error[14];

		}

		else {

			mysql_connect($this->server, $this->db_user, $this->db_pass);
			mysql_select_db($this->database);

			$query = mysql_query("select * from `".$this->tbl_confirm."` where mdhash = '$hash' AND username = '$username'");
			$result = @mysql_num_rows($query);

			if ($result < 1) {

				mysql_close();

				return $this->error[15];

			}

			list($hd,$username,$password,$name,$email,$age,$sex,$school) = mysql_fetch_row($query);

			$is_success_first = mysql_query("insert into `".$this->tbl_login."` (username, password) values ('$username', '$password')");

			if ($is_success_first) {

				$is_success_second = mysql_query("insert into `".$this->tbl_user."` (name, email, age, sex, school) values ('$name', '$email', '$age', '$sex', '$school')");

				if ($is_success_second) {

					$is_success_third = mysql_query("delete from `".$this->tbl_confirm."` where username = '$username'");

				}

			}

			mysql_close();

			if (!$is_success_first) {

				return $this->error[16];

			}

			if (!$is_success_second) {

				@mail($email, "Registration Error", "Thank You, $name for (trying to) register. Unfortunately due to an unknown database fault\n
			       	we were unable to add your complete information to the database. So please login to your account and \n
				click on remove account. And then re-register for the account.", "From: $this->webmaster");

				return $this->error[17];

			}

			if (!$is_success_third) {

				@mail($this->webmaster, "Alert, Purge Account!!!", "Hey man, looks like your database sucked at the wrong moment, luckily he was able to stuff in his 
				      info at the right time and place, but something happened and I wasn't able to remove his entry from 
				      the confirmation table.", "From: $this->webmaster");

				return 2;

			}

			@mail($email, "$this->wsname Confirmation", "Thank You, $name for registering. Here is the information we recieved :\n
					\nName     : $name
					\nEmail    : $email
					\nAge      : $age
					\nSex      : $sex
					\nSchool   : $school
					\nUsername : $username
					\nPassword : $password", "From: $this->webmaster");

			return 2;

		}

	}

	function conf_flush () {

		mysql_connect($this->server, $this->db_user, $this->db_pass);
		mysql_select_db($this->database);

		$query = mysql_query("delete from `".$this->tbl_confirm."` where date_add(date, interval 2 day) < now()");

		mysql_close();

		if (!$query) {

			return $this->error[18];

		}

		return 2;

	}

	function lostpwd ($email) {

		if (!$email) {

			return $this->error[14];

		}

		mysql_connect($this->server, $this->db_user, $this->db_pass);
		mysql_select_db($this->database);

		$query = mysql_query("select authlib_login.password, authlib_login.username from authlib_login,`".$tbl_user."` where authlib_data.email = '$email' and authlib_login.id = authlib_data.id");
		$result = @mysql_num_rows($query);

		mysql_close();

		if ($result < 1) {

			return $this->error[19];

		}

		list($password, $username) = mysql_fetch_row($query);

		@mail($email, "Account Info", "Dear User,\nAs per your request here is your account information:\n
				\nUsername: $username
				\nPassword: $password
				\nWe hope you remember your password next time!", "From: $this->webmaster");

		return 2;

	}

	function chemail ($id, $email, $email2) {

		if ($email != $email2) {

			return $this->error[14];

		}

		else {

			if (!eregi("^([a-z0-9]+)([._-]([a-z0-9]+))*[@]([a-z0-9]+)([._-]([a-z0-9]+))*[.]([a-z0-9]){2}([a-z0-9])?$", $email)) {

				return $this->error[4];

			}

			mysql_connect($this->server, $this->db_user, $this->db_pass);
			mysql_select_db($this->database);

			$query = mysql_query("select id from `".$this->tbl_user."` where email = '$email'");
			$result = @mysql_num_rows($query);

			if ($result > 0) {

				list($id_from_db) = mysql_fetch_row($query);

				if ($id_from_db != $id) {

					mysql_close();

					return $this->error[13];

				}

				return $this->error[23];

			}

			$mdhash = md5($id.$email.$this->secret);

			$query = mysql_query("insert into `".$this->tbl_confirm_email."` values ('$id', '$email', '$mdhash', now())");

			if (!$query) {

				mysql_close();

				$this->error[20];

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

			return $this->error[14];

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

}

function redirect($location = "index.php") {
        header("Location: $location");
        exit;
}

$authlib = new authlib;
$cfgx = new config_class;

?>
