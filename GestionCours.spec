# -*- mode: python ; coding: utf-8 -*-
# Build on Windows:
#   pip install -r requirements.txt
#   build_exe.bat
# Result: dist\GestionCours.exe  (fenêtre bureau PySide6, pas de navigateur)

block_cipher = None

datas = [
    ('fichiers', 'fichiers'),
    ('templates', 'templates'),
    ('static', 'static'),
]

hiddenimports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'desktop',
    'desktop.theme',
    'desktop.main_window',
    'desktop.dialogs',
    'flask',
    'jinja2',
    'reportlab',
    'reportlab.pdfbase.ttfonts',
    'sqlite3',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GestionCours',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
