Hi everybody,

I think we are close to gettting a working version of ACEMAN --- ACE for EMAN.

Scott - If you want to test it you can copy the directory ace_cvs and run

>aceman

from inside matlab. It basically reads in an imagic file and writes out another imagic file which has ctf information embedded in it. So all you need to do to check how good the fits are is do

>ctfit outputfilename.hed

A typical fit looks like this

>http://graphics.ucsd.edu/~spmallick/ctf/acemanfit.png

I have changed the way envelope is calculated. See for example

>http://graphics.ucsd.edu/~spmallick/ctf ... envfit.png

I have also gone through EMANs source code to figure out how exactly the parameters of ACE and EMAN are related. There is a few things though which I do not understand yet --- noise_const is off around 1% ( I have hardcoded a compensation ) . Secondly it is not clear to me if the we can embed the astigmatism parameter in the imagic files.

I will work on ACEMAN again today evening/night to find the story behind the 1% error.

Satya

Hello everybody,

I was wondering if people want to test an experimental version of ACEMAN --- ACE for EMAN. ACEMAN takes in a stack of picked particles in imagic ( hed/img ) format and embeds the ctf parameters into it. You could then use

>ctfit output_file.hed

to see how good the ctfits are. ACE and EMAN define the Envelope function in a slightly different way and so I had to make some changes in the core ace function.

Here are the steps for installation

1. Change to your ace directory.

>cd ace_directory

2. Download the above file in the ace directory.

>wget http://graphics.ucsd.edu/~spmallick/ctf/aceman.tgz

3. Untar unzip it

>tar -zxvf aceman.tgz

A few files will be extracted into the ace directory.

4. Start MATLAB

5. Inside MATLAB do

>aceman

There is not documentation yet but if you have used acedemo, it should be straight forward. Please let me know if you do get good/bad results.

Again, this is an experimental version, so I would not recommend it for real experiments yet.

Regards

Satya

[Ace Estimation ^](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/CTF_Estimation/Ace_Estimation)
