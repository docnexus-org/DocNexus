# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Code\\DocNexusCorp\\DocNexus\\docnexus\\cli.py'],
    pathex=['D:\\Code\\DocNexusCorp\\DocNexus'],
    binaries=[],
    datas=[('D:\\Code\\DocNexusCorp\\DocNexus\\docnexus\\templates', 'docnexus/templates'), ('D:\\Code\\DocNexusCorp\\DocNexus\\docnexus\\static', 'docnexus/static'), ('D:\\Code\\DocNexusCorp\\DocNexus\\docnexus\\plugins_dev', 'docnexus/plugins_dev')],
    hiddenimports=['docnexus.version_info', 'docnexus.features', 'docnexus.features.smart_convert', 'engineio.async_drivers.threading', 'pymdownx', 'pymdownx.betterem', 'pymdownx.superfences', 'pymdownx.tabbed', 'pymdownx.details', 'pymdownx.magiclink', 'pymdownx.tasklist', 'pymdownx.arithmatex', 'pymdownx.highlight', 'pymdownx.inlinehilite', 'pymdownx.keys', 'pymdownx.smartsymbols', 'pymdownx.snippets', 'pymdownx.tilde', 'pymdownx.caret', 'pymdownx.mark', 'pymdownx.emoji', 'pymdownx.saneheaders'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DocNexus_v1.2.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\Code\\DocNexusCorp\\DocNexus\\docnexus\\static\\logo.ico'],
)
