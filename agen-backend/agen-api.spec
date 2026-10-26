# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the bundled AGEN backend (desktop build).

Uses collect_all/collect_submodules for packages that rely on dynamic imports
(uvicorn, google-genai, passlib, etc.) which PyInstaller cannot detect on its own,
and bundles the alembic migrations + ini as data so the app has a complete tree.
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Packages with dynamic imports / data files that must be collected fully.
for pkg in (
    "uvicorn",
    "fastapi",
    "starlette",
    "pydantic",
    "pydantic_settings",
    "google.genai",
    "passlib",
    "jose",
    "slowapi",
    "sqlalchemy",
    "alembic",
    "email_validator",
):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Ensure our own application package (imported dynamically via routers/agents)
# is fully included.
hiddenimports += collect_submodules("app")

# Bundle alembic migration scripts + config alongside the executable so the
# same tree is available at runtime if migrations are ever run.
datas += [
    ("alembic", "alembic"),
    ("alembic.ini", "."),
]


a = Analysis(
    ["desktop_entry.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="agen-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="agen-api",
)
