apt install python-numpy python-scipy
git clone http://emg.nysbc.org/git/myami
cd myami
./pysetup.sh install
make /etc/myami/redux.cfg, see Configuration Redux in [leginon:Using Redux to serve images on myamiweb](/appion/leginonUsing_Redux_to_serve_images_on_myamiweb)
apt-get install libfftw3-dev
pip install fs==0.5 PyFFTW
rm /etc/init.d/reduxd
cp redux/system/reduxd.service /lib/systemd/system
systemctl enable reduxd
systemctl start reduxd
