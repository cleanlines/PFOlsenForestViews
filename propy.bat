REM @echo off
@CALL :normalizepath scripts_path "%~dp0"

@set /p esri_path=<"%scripts_path%proesripath.txt"
@set global_path="%scripts_path%proenv.txt"
@echo %global_path%

@set local_path="%localappdata%\ESRI\conda\envs\proenv.txt"

:: read the active environment name
if exist "%local_path%" (
    @set /p CONDA_NEW_ENV=<%local_path%
) else (
    @set /p CONDA_NEW_ENV=<%global_path%
)

@echo %CONDA_NEW_ENV%

@SET "activate_path="%esri_path%activate.bat" "%CONDA_NEW_ENV%"
@set "deactivate_path="%esri_path%deactivate.bat""
@set CONDA_SKIPCHECK=1
@call %activate_path%
python.exe --version
python.exe %*
@call %deactivate_path%
goto :eof

:normalizepath
    @set "%1=%~dpfn2"
    @exit /b
