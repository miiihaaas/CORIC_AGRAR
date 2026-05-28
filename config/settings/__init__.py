"""Settings package marker for `config.settings`.

Per Story 1.2: ovaj __init__.py je NAMERNO PRAZAN — NE re-export-uje iz
`base`. Svaki environment modul (development.py / staging.py / production.py)
je sopstveni import target preko `DJANGO_SETTINGS_MODULE=config.settings.<env>`.
"""
