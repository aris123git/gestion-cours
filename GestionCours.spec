# -*- mode: python ; coding: utf-8 -*-
# Build on Windows:
#   pip install -r requirements.txt pyinstaller
#   pyinstaller GestionCours.spec
# Result: dist\GestionCours.exe

block_cipher = None

datas = [
    ('fichiers', 'fichiers'),
    ('templates', 'templates'),
    ('static', 'static'),
]

hiddenimports = [
    'flask',
    'jinja2',
    'jinja2.ext',
    'reportlab',
    'reportlab.pdfbase.ttfonts',
    'reportlab.graphics',
    'sqlite3',
    'webbrowser',
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
    upx=False,  # UPX often breaks / triggers antivirus on Windows
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # no black terminal — browser + small status window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
