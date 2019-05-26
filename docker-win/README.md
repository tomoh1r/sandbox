docker-win
==========

# Prerequirements

## Use Windows 10 Pro.

Windows server containers run on Windows 10 Pro.

## Install Docker and enable to use Windows server containers.

See [Windows Containers on Windows 10](https://docs.microsoft.com/en-us/virtualization/windowscontainers/quick-start/quick-start-windows-10).

## Download Python 3.6.1.

```ps1
> Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.6.1/python-3.6.1.exe -OutFile .\src\python-3.6.1.exe
```

# Build and run.

```ps1
> docker build -t local/sandbox -f Dockerfile .
> docker run --rm local/sandbox
```
