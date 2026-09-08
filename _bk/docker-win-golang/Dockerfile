# WIP
#
# > docker build -t local/win-golang -f Dockerfile .
# > docker run --rm -it --isolation=hyperv local/win-golang powershell.exe
#
# vim:noet:

FROM microsoft/nanoserver

LABEL Description="Go" Vendor="Google" Version="1.8.1"

ENV MY_BASE_URI=https://storage.googleapis.com/golang \
    MY_VER=1.8.1

SHELL ["powershell.exe", "-Command", "$ExecutionPolicy = 'RemoteSigned'; $ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Invoke-WebRequest -Uri %MY_BASE_URI%/go%MY_VER%.windows-amd64.zip -Method Get -OutFile c:\go.zip ; \
# [Environment]::SetEnvironmentVariable('Path', 'c:\go\bin;%Path%', 'Machine')

Add go.zip c:\go.zip

RUN Expand-Archive -Path c:\go.zip -DestinationPath c:\; \
	Remove-Item -Path c:\go.zip -Force

RUN { $str = 'c:\go\bin;'; \
	$str += $Env:Path; \
	setx.exe -m Path $str }
