chmod 777 ./Scripts/activate
chmod 777 ./Scripts/deactivate.bat

./Scripts/activate
cd flask-server
/usr/bin/python3 restServer-mvc.py
cd ..
./Scripts/deactivate.bat