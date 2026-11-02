"""Minimize only Chrome windows owned by this command's process descendants."""
from __future__ import annotations

import sys
import threading


def descendant_ids(root: int, parents: dict[int, int]) -> set[int]:
    result = {root}
    while True:
        children = {pid for pid, parent in parents.items() if parent in result}
        if children <= result:
            return result
        result.update(children)


def minimize_flow_windows(root_pid: int, stopped: threading.Event) -> None:
    if sys.platform != 'win32':
        return
    import ctypes
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    user = ctypes.WinDLL('user32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    for name in ('Process32FirstW', 'Process32NextW'):
        getattr(kernel, name).argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        getattr(kernel, name).restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    user.IsIconic.argtypes = [wintypes.HWND]
    user.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
    known = {root_pid}
    while not stopped.is_set():
        snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            return
        parents, names = {}, {}
        try:
            entry = ProcessEntry()
            entry.dwSize = ctypes.sizeof(entry)
            present = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
            while present:
                parents[entry.th32ProcessID] = entry.th32ParentProcessID
                names[entry.th32ProcessID] = entry.szExeFile.lower()
                present = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            kernel.CloseHandle(snapshot)
        known.intersection_update(parents)
        known.add(root_pid)
        for parent in tuple(known):
            known.update(descendant_ids(parent, parents))
        targets = {pid for pid in known if names.get(pid) in ('chrome.exe', 'chromium.exe')}

        @callback_type
        def minimize(hwnd, _param):
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in targets and user.IsWindowVisible(hwnd) and not user.IsIconic(hwnd):
                user.ShowWindowAsync(hwnd, 7)  # SW_SHOWMINNOACTIVE: never focus Flow.
            return True

        user.EnumWindows(minimize, 0)
        stopped.wait(0.5)
