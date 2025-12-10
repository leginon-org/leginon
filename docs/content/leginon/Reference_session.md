reference images are now saved automatically to special sessions name containing "_ref" in the same base leginon directory defined in leginon.cfg as image_path. Every 90 days, a new session is automatically created so that the very old ones can be archived away eventually. Also, if a linux user has no write permission to the existing reference session, a new one will be created so that there is no delay in data collection. All users still need read-access to these directories in order to use them.

For example, on Jun 1st, 2012, a user starts the first time a Leginon session. His/her leginon.cfg has these lines:

    [Images]
    path: /your_disk/leginon


Therefore, Leginon creates a reference session with this path

    /your_disk/leginon/12jun01_ref_a
