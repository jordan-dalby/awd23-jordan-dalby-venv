REM Win Start/Stop Instructions

call ./Scripts/activate.bat
call cd ./flask-server
call python restServer-mvc.py
call cd ..
call ./Scripts/deactivate.bat

@pause

