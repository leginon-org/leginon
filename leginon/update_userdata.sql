## Add the new columns
ALTER TABLE UserData ADD COLUMN username text;
ALTER TABLE UserData ADD COLUMN firstname text;
ALTER TABLE UserData ADD COLUMN lastname text;

## Copy name -> username
UPDATE UserData SET username = name;

### You need to verify the results of the following to make sure
### full name was split up properly.

## Copy first word in `full name` to firstname
UPDATE UserData SET firstname = SUBSTRING_INDEX(`full name`, " ", 1);

## Copy remaining words in `full name` to lastname
UPDATE UserData SET lastname = SUBSTRING_INDEX(`full name`, " ", -1);
