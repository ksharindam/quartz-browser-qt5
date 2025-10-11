# -*- mode: python ; coding: utf-8 -*-
# Usage : pyinstaller quartz_browser.spec

a = Analysis(
    ['../quartz_browser/main.py'],
    pathex=['../quartz_browser'],
    binaries=[],
    datas=[("../quartz_browser/userContent.css", "."), ("../quartz_browser/home.html", "."), ("../quartz_browser/quartz-browser.jpg", "."), ("../quartz_browser/blocklist.txt", ".")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='quartz_browser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="../files/quartz-browser.ico",
    version='version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='quartz_browser',
)
