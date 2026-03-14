# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# Thu thập dữ liệu cần thiết
datas = []
datas += collect_data_files('tkcalendar')
datas += collect_data_files('ttkwidgets')

# Hidden imports cần thiết
hiddenimports = [
    'PIL._tkinter_finder',
    # Google Generative AI modules
    'google.generativeai',
    'google.generativeai.caching',
    'google.generativeai.client',
    'google.generativeai.types',
    'google.generativeai.types.citation_types',
    'google.generativeai.types.content_types',
    'google.generativeai.string_utils',
    'google.generativeai.protos',
    'google.generativeai.generative_models',
    'google.generativeai.embedding',
    'google.generativeai.files',
    'google.ai.generativelanguage',
    'google.ai.generativelanguage_v1beta',
    'google.ai.generativelanguage_v1beta.services',
    'google.ai.generativelanguage_v1beta.services.cache_service',
    'google.ai.generativelanguage_v1beta.services.cache_service.async_client',
    # Google API Core modules
    'google.api_core',
    'google.api_core.exceptions',
    'google.api_core.retry',
    'google.api_core.gapic_v1',
    'google.auth',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google.auth.transport.grpc',
    # HTTP và Email modules
    'http',
    'http.client',
    'http.server',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.utils',
    # Network modules
    'urllib3',
    'urllib3.util',
    'certifi',
    'charset_normalizer',
    'idna',
    'requests',
    'requests.packages',
    # Protobuf
    'google.protobuf',
    'google.protobuf.message',
    'google.protobuf.descriptor',
    # UI modules
    'ttkwidgets.autocomplete',
    'tkcalendar',
]

# Loại bỏ các thư viện không cần thiết để giảm kích thước
# LƯU Ý: Không loại bỏ http, email, urllib3, certifi, charset_normalizer, idna, requests vì Google API cần chúng
excludes = [
    'numpy', 'matplotlib', 'IPython', 'tests', 'pytest', 'setuptools',
    'distutils', 'pandas', 'scipy', 'sklearn', 'tensorflow', 'torch',
    'jupyter', 'notebook', 'ipython', 'sphinx', 'docutils', 'pydoc',
]

a = Analysis(
    ['create_folder.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,  # Không optimize để tránh lỗi với Google API
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='create_folder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Tắt strip để tăng tốc khởi động (Windows không có strip)
    upx=False,  # Tắt UPX để tăng tốc khởi động (giải nén nhanh hơn)
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
