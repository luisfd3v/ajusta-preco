# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Coletar dados do módulo barcode
barcode_datas = collect_data_files('barcode')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.ini', '.'), 
        ('icon/money-management.ico', 'icon'),
        ('icon/splash.png', 'icon'),
        ('notas_processadas.json', '.'),
    ] + barcode_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.utils',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.pdfbase.ttfonts',
        'barcode',
        'barcode.writer',
        'barcode.codex',
        'barcode.ean',
        'barcode.upc',
        'barcode.isxn',
        'barcode.itf',
        'barcode.codabar',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
    ],
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
    [],  # <-- REMOVIDO: a.binaries, a.zipfiles, a.datas (modo onedir)
    exclude_binaries=True,  # <-- ADICIONADO: arquivos binários vão para pasta separada
    name='AjustaPreco',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Desativa console (aplicativo GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/money-management.ico',  # Ícone do executável
)

# ADICIONADO: Seção COLLECT para modo onedir
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AjustaPreco',
)
