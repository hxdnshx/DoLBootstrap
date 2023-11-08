@echo off
REM 这行将调用python并传递所有的命令行参数给 main.py
python main.py %*

REM 当Python脚本结束时按任意键退出
pause