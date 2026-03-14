# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# Thu thập dữ liệu cần thiết
datas = []
datas += collect_data_files('tkcalendar')
datas += collect_data_files('ttkwidgets')

# Hidden imports cần thiết
hiddenimports = [
    'PIL._tkinter_finder',
    'ttkwidgets.autocomplete',
    'tkcalendar',
]

# Loại bỏ các thư viện không cần thiết để giảm kích thước
excludes = [
    'numpy', 'matplotlib', 'IPython', 'tests', 'pytest', 'setuptools',
    'distutils', 'email', 'http', 'urllib3', 'certifi', 'charset_normalizer',
    'idna', 'requests', 'pandas', 'scipy', 'sklearn', 'tensorflow', 'torch',
    'jupyter', 'notebook', 'ipython', 'sphinx', 'docutils', 'pydoc',
    'google',  # Không cần Google API trong config_manager
]

a = Analysis(
    ['config_manager.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,  # Tối ưu code Python
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='config_manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Loại bỏ debug symbols
    upx=True,  # Nén với UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Không hiện console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['iconZ.ico'],
)
