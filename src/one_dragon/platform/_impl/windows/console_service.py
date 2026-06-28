"""Windows 平台控制台：隐藏控制台 + JobObject 子进程清理。"""

from __future__ import annotations

import atexit
import ctypes
import os
from collections.abc import Callable
from ctypes import wintypes

from one_dragon.platform.console_service import ConsoleService
from one_dragon.utils.log_utils import log

_kernel32 = ctypes.windll.kernel32
_user32 = ctypes.windll.user32
_kernel32.GetConsoleWindow.argtypes = []
_kernel32.GetConsoleWindow.restype = wintypes.HWND
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.ShowWindow.restype = wintypes.BOOL


class WindowsConsoleService(ConsoleService):

    def hide_console(self) -> None:
        hwnd = _kernel32.GetConsoleWindow()
        if hwnd:
            _user32.ShowWindow(hwnd, 0)  # SW_HIDE

    def run_with_cleanup(self, fn: Callable[[], None]) -> None:
        if os.name != 'nt':
            return fn()
        try:
            self._run_with_job_object(fn)
        except Exception as e:
            log.warning('JobObject 不可用，回退到 atexit 清理: %s', e)
            fn()

    @staticmethod
    def _run_with_job_object(fn: Callable[[], None]) -> None:
        from ctypes import wintypes as wt

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
        JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
        JobObjectExtendedLimitInformation = 9

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('PerProcessUserTimeLimit', ctypes.c_longlong),
                ('PerJobUserTimeLimit', ctypes.c_longlong),
                ('LimitFlags', wt.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wt.DWORD),
                ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wt.DWORD),
                ('SchedulingClass', wt.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ('ReadOperationCount', ctypes.c_ulonglong),
                ('WriteOperationCount', ctypes.c_ulonglong),
                ('OtherOperationCount', ctypes.c_ulonglong),
                ('ReadTransferCount', ctypes.c_ulonglong),
                ('OtherTransferCount', ctypes.c_ulonglong),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t),
                ('PeakJobMemoryUsed', ctypes.c_size_t),
            ]

        job_handle = _kernel32.CreateJobObjectW(None, None)
        if not job_handle:
            raise OSError('CreateJobObjectW failed')
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_BREAKAWAY_OK
        if not _kernel32.SetInformationJobObject(
                job_handle, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)):
            _kernel32.CloseHandle(job_handle)
            raise OSError('SetInformationJobObject failed')

        atexit.register(lambda: _kernel32.CloseHandle(job_handle))
        fn()
