[TOC]

The tables that will be affected are in the dbemdata database and the project database.
Migrate the user data from project to dbemdata because dbemdata is already in Sinedon format.

[dbemdata]{.underline}

-   GroupData
-   UserData (81 rows)

[project]{.underline}

-   users (233 rows)
-   login (187 rows)
-   pis (145 rows)
-   userdetails
-   projectowner

Future:
Eventually, we would like to have 3 databases, appion, leginon and project. The user related tables in dbemdata would be moved to project.
All the tables in project still need to be converted to Sinedon format.

## 1 Add new columns to UserData

Add:

-   username
-   fullname
-   firstname
-   lastname
-   password
-   email

Leave the existing columns as is. Use of "name" and "full name" (with a space) will be phased out.

## 2 Copy data to the UserData table

From users, copy username, firstname, lastname to UserData.

### Update existing dbemdata.UserData entries with information from project.users when the names match.

    UPDATE UserData, project.users, project.login
        SET UserData.username=project.users.username,
            UserData.firstname=project.users.firstname,
            UserData.lastname=project.users.lastname,
            UserData.email=project.users.email 
        WHERE UserData.`full name` like concat(project.users.firstname, ' ',project.users.lastname) 
              and project.login.userId = project.users.userId 
              and project.users.userId not in(63,211)
              and UserData.DEF_id != 54

### Some names did not match exactly. Update these seperatly.

    //Palida?
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 42
              AND UserData.DEF_id = 25

    //Gabe?
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 65
              AND UserData.DEF_id = 29

    //Edward Bridgnole
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 78
              AND UserData.DEF_id = 41

    //Pickwei
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 122
              AND UserData.DEF_id = 57

    //Mark Daniels
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 199
              AND UserData.DEF_id = 65

    //Chris Arthur
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 35
              AND UserData.DEF_id = 67

    //Fei Sun
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 233
              AND UserData.DEF_id = 76

    //Chi-yu Fu
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 245
              AND UserData.DEF_id = 78

    //Otomo Takanori    uId=79  puId=252
    UPDATE UserData, projectdata.users
        SET UserData.username=projectdata.users.username,
            UserData.firstname=projectdata.users.firstname,
            UserData.lastname=projectdata.users.lastname,
            UserData.email=projectdata.users.email 
        WHERE projectdata.users.userId = 252
              AND UserData.DEF_id = 79

### Insert the rest of the project.users entries into the dbemdata.UserData table.

This inserts users that have a corresponding project.login entry and have not already been merged into existing dbemdata.UserData entries.
NRAMM usernames with no login entry are not transferred.

    INSERT INTO dbemdata.UserData (username, firstname, lastname, email)
    SELECT projectdata.users.username,projectdata.users.firstname, projectdata.users.lastname,projectdata.users.email
    FROM projectdata.users
    WHERE projectdata.users.userId IN (SELECT projectdata.login.userId FROM projectdata.login)
    AND (projectdata.users.userId NOT IN 
    (
        SELECT projectdata.users.userId userId
        FROM dbemdata.UserData, projectdata.users, projectdata.login
        WHERE dbemdata.UserData.`full name` LIKE concat( projectdata.users.firstname, ' ', projectdata.users.lastname )
        AND projectdata.login.userId = projectdata.users.userId
    )
    AND projectdata.users.userId NOT IN ( 42, 65, 78, 122, 199, 35, 233, 245, 252, 63, 211 ))

### From project.login, copy user password to dbemdata.UserData.

    UPDATE dbemdata.UserData, projectdata.login
    SET dbemdata.UserData.password=projectdata.login.password
    WHERE dbemdata.UserData.username = projectdata.login.username

## 3 Modify userdetails table

Remove the email column from the userdetails table.
From users, copy all needed fields.

### Copy users from dbemdata.UserData to the project.userdetails table. inserts 188 rows

    INSERT INTO projectdata.userdetails 
      (`REF|leginondata|UserData|user`, 
       title, 
       institution, 
       dept, 
       address, 
       city, 
       statecountry, 
       zip, 
       phone, 
       fax, 
       url)
    SELECT dbemdata.UserData.DEF_id, projectdata.users.title, projectdata.users.institution, 
      projectdata.users.dept, projectdata.users.address, projectdata.users.city, 
      projectdata.users.statecountry, projectdata.users.zip, projectdata.users.phone, 
      projectdata.users.fax, projectdata.users.url
    FROM dbemdata.UserData, projectdata.users
    WHERE dbemdata.UserData.username = projectdata.users.username
    AND projectdata.users.userId NOT IN ( 216, 224, 107, 204, 219, 241, 261 )

ignore:
project.users.userId username
216 nramm_hetzer (dup w/less data)
224 nramm_hjing
107 nramm_jlanman
204 nramm_rkhayat
219 nramm_rkhayat
241 nramm_vinzenz.unger
261 nramm_vinzenz.unger

## 4 Create projectowner table

Move the data from pis table to a new projectowner table in the project database. This table will refer to users in the UserData table.
We will phase out use of the pis table.

**Insert users that are project owners and do not have login info and do not have a dbem user name.**
Set the passwords to the username.

Add the following project owners to dbemdata.UserData:
nramm_mbevans
nramm_erica
nramm_erwright
nramm_mgfinn
nramm_pucadyil
nramm_abaudoux
nramm_kuzman
nramm_my3r
nramm_liguo.wang
nramm_bbartholomew
nramm_cciferri
nramm_galushin
nramm_nachury
nramm_mfisher1
nramm_nicoles
nramm_gokhan_tolun
nramm_rkirchdo

    INSERT INTO dbemdata.UserData (username, firstname, lastname, email, password)
    SELECT projectdata.users.username,projectdata.users.firstname, projectdata.users.lastname, 
    projectdata.users.email, projectdata.users.username
    FROM projectdata.users
    WHERE projectdata.users.username IN ("nramm_mbevans", "nramm_erica", "nramm_erwright", "nramm_mgfinn", 
    "nramm_pucadyil", "nramm_abaudoux", "nramm_kuzman", "nramm_my3r", "nramm_liguo.wang", "nramm_bbartholomew", 
    "nramm_cciferri", "nramm_galushin", "nramm_nachury", "nramm_mfisher1", "nramm_nicoles", "nramm_gokhan_tolun", 
    "nramm_rkirchdo")

**Add their details into the userdetails table**

    INSERT INTO projectdata.userdetails (`REF|leginondata|UserData|user`, title, institution, 
    dept, address, city, statecountry, zip, phone, fax, url)
    SELECT dbemdata.UserData.DEF_id, projectdata.users.title, projectdata.users.institution, 
    projectdata.users.dept, projectdata.users.address, projectdata.users.city, projectdata.users.statecountry, 
    projectdata.users.zip, projectdata.users.phone, projectdata.users.fax, projectdata.users.url
    FROM dbemdata.UserData, projectdata.users
    WHERE dbemdata.UserData.username = projectdata.users.username
    AND projectdata.users.username IN ( "nramm_mbevans", "nramm_erica", "nramm_erwright", 
    "nramm_mgfinn", "nramm_pucadyil", "nramm_abaudoux", "nramm_kuzman", "nramm_my3r", "nramm_liguo.wang", 
    "nramm_bbartholomew", "nramm_cciferri", "nramm_galushin", "nramm_nachury", "nramm_mfisher1", "nramm_nicoles", 
    "nramm_gokhan_tolun", "nramm_rkirchdo")

**Update the pis table with the correct usernames.**
The correct usernames are the ones that the users actually use to login to the system.
They have been found by manual inspection.

    UPDATE projectdata.pis
    SET projectdata.pis.username="chappie"
    WHERE projectdata.pis.username="nramm_chappie"

    UPDATE projectdata.pis
    SET projectdata.pis.username="carthur"
    WHERE projectdata.pis.username="nramm_Christopher.Arthur"

    UPDATE projectdata.pis
    SET projectdata.pis.username="cpotter"
    WHERE projectdata.pis.username="nramm_cpotter"

    UPDATE projectdata.pis
    SET projectdata.pis.username="craigyk"
    WHERE projectdata.pis.username="nramm_craigyk"

    UPDATE projectdata.pis
    SET projectdata.pis.username="dfellman"
    WHERE projectdata.pis.username="nramm_dfellman"

    UPDATE projectdata.pis
    SET projectdata.pis.username="dlyumkis"
    WHERE projectdata.pis.username="nramm_dlyumkis"

    UPDATE projectdata.pis
    SET projectdata.pis.username="southworth"
    WHERE projectdata.pis.username="nramm_dsouthwo"

    UPDATE projectdata.pis
    SET projectdata.pis.username="fapalida"
    WHERE projectdata.pis.username="nramm_fapalida"

    UPDATE projectdata.pis
    SET projectdata.pis.username="feisun"
    WHERE projectdata.pis.username="nramm_feisun"

    UPDATE projectdata.pis
    SET projectdata.pis.username="glander"
    WHERE projectdata.pis.username="nramm_glander"

    UPDATE projectdata.pis
    SET projectdata.pis.username="haoyan"
    WHERE projectdata.pis.username="nramm_hao.yan"

    UPDATE projectdata.pis
    SET projectdata.pis.username="jaeger"
    WHERE projectdata.pis.username="nramm_jaeger"

    UPDATE projectdata.pis
    SET projectdata.pis.username="koehn"
    WHERE projectdata.pis.username="nramm_koehn"

    UPDATE projectdata.pis
    SET projectdata.pis.username="mmatho"
    WHERE projectdata.pis.username="nramm_mmatho"

    UPDATE projectdata.pis
    SET projectdata.pis.username="moeller"
    WHERE projectdata.pis.username="nramm_moeller"

    UPDATE projectdata.pis
    SET projectdata.pis.username="muldera"
    WHERE projectdata.pis.username="nramm_mulderam"

    UPDATE projectdata.pis
    SET projectdata.pis.username="paventer"
    WHERE projectdata.pis.username="nramm_paventer"

    UPDATE projectdata.pis
    SET projectdata.pis.username="rharshey"
    WHERE projectdata.pis.username="nramm_rasika"

    UPDATE projectdata.pis
    SET projectdata.pis.username="nramm_langlois"
    WHERE projectdata.pis.username="nramm_rl2528"

    UPDATE projectdata.pis
    SET projectdata.pis.username="rmglaeser"
    WHERE projectdata.pis.username="nramm_rmglaeser"

    UPDATE projectdata.pis
    SET projectdata.pis.username="rtaurog"
    WHERE projectdata.pis.username="nramm_rtaurog"

    UPDATE projectdata.pis
    SET projectdata.pis.username="sstagg"
    WHERE projectdata.pis.username="nramm_sstagg"

    UPDATE projectdata.pis
    SET projectdata.pis.username="tgonen"
    WHERE projectdata.pis.username="nramm_tgonen"

    UPDATE projectdata.pis
    SET projectdata.pis.username="vossman"
    WHERE projectdata.pis.username="nramm_vossman"

    UPDATE projectdata.pis
    SET projectdata.pis.username="ychaban"
    WHERE projectdata.pis.username="nramm_ychaban"

**Add project co-owners (the people who actually access the project).**
Many of the project owners do not actually access the data. Add the users who actually work with the project.

    INSERT INTO projectdata.pis (projectId, username)
    VALUES (200,"nramm_fazam"), (230,"glander"), (190,"jlee"), 
    (231,"glander"), (203,"Ranjan"), (181,"kubalek"), (84,"strable"), 
    (222,"nramm_barbie"), (199,"joelq")

**Insert rows into projectowners.**
All project owners now have usernames in dbemdata.UserData and all projects have an active owner in project.pis.

    INSERT INTO projectdata.projectowners (`REF|projects|project`, `REF|leginondata|UserData|user`)
    SELECT projectdata.pis.projectId, dbemdata.UserData.DEF_id
    FROM dbemdata.UserData, projectdata.pis
    WHERE dbemdata.UserData.username = projectdata.pis.username

## 5 Set groups and privileges

### Set all null groups to 4 (users)

    UPDATE dbemdata.UserData
    SET dbemdata.UserData.`REF|GroupData|group`= 4
    WHERE dbemdata.UserData.`REF|GroupData|group` IS NULL

### set all group privileges that are null to 3

    UPDATE dbemdata.GroupData
    SET dbemdata.GroupData.`REF|projectdata|privileges|privilege`=3
    WHERE dbemdata.GroupData.`REF|projectdata|privileges|privilege` IS NULL

## 6 Update any NULL values in dbemdata.UserData

**Set the full name in dbemdata.UserData.**

    UPDATE dbemdata.UserData
    SET dbemdata.UserData.`full name` = concat(dbemdata.UserData.firstname, ' ', dbemdata.UserData.lastname)
    WHERE dbemdata.UserData.`full name` IS NULL;

    UPDATE dbemdata.UserData
    SET dbemdata.UserData.username = dbemdata.UserData.name
    WHERE dbemdata.UserData.username IS NULL;

    UPDATE dbemdata.UserData
    SET dbemdata.UserData.password = dbemdata.UserData.username
    WHERE dbemdata.UserData.password IS NULL;

    UPDATE dbemdata.UserData
    SET dbemdata.UserData.firstname = ""
    WHERE dbemdata.UserData.firstname IS NULL;

**update shareexperiments**

    UPDATE project.shareexperiments
    SET project.shareexperiments.`REF|leginondata|SessionData|experiment` = project.shareexperiments.experimentId
    WHERE project.shareexperiments.`REF|leginondata|SessionData|experiment` IS NULL;

**add usernames where they are missing**

    UPDATE project.shareexperiments, project.users
    SET project.shareexperiments.username = project.users.username 
    WHERE project.users.userId = project.shareexperiments.userId 
    AND project.shareexperiments.username IS NULL

**update users who have a matching username in dbemdata**

    UPDATE project.shareexperiments, dbemdata.UserData 
    SET project.shareexperiments.`REF|leginondata|UserData|user` = dbemdata.UserData.DEF_id 
    WHERE dbemdata.UserData.username = project.shareexperiments.username 
    AND project.shareexperiments.`REF|leginondata|UserData|user` IS NULL 
