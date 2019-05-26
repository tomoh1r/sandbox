FROM microsoft/windowsservercore

LABEL Description="Python" Vendor="Python Software Foundation" Version="3.6.1"

ADD src /

RUN powershell.exe -Command \
    $ErrorActionPreference = 'Stop'; \
    Start-Process c:\python-3.6.1.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait ; \
    Remove-Item c:\python-3.6.1.exe -Force

CMD ["py", "c:/hello.py"]
