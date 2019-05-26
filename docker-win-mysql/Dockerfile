# WIP
#
# > docker build -t local/win-mysql -f Dockerfile .
# > docker run --rm -it --isolation=hyperv local/win-mysql powershell.exe
#
# vim:noet:
FROM microsoft/windowsservercore

LABEL Description="MySql" Vendor="Oracle" Version="5.6.29"

RUN powershell -Command \
	$ErrorActionPreference = 'Stop'; \
	Invoke-WebRequest -Method Get -Uri https://dev.mysql.com/get/Downloads/MySQL-5.6/mysql-5.6.36-winx64.zip -Timeoutsec 600 -OutFile c:\mysql.zip ; \
	Expand-Archive -Path c:\mysql.zip -DestinationPath c:\ ; \
	Remove-Item c:\mysql.zip -Force

RUN SETX /M Path %path%;C:\mysql-5.6.36-winx64\bin

RUN powershell -Command \
	$ErrorActionPreference = 'Stop'; \
	mysqld.exe --install ; \
	Start-Service mysql ; \
	Stop-Service mysql ; \
	Start-Service mysql

RUN mysql -u root -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '' WITH GRANT OPTION;"

CMD [ "ping localhost -t" ]
