# Migraciones de base de datos

Alembic carga `DATABASE_URL` desde la configuración central. El archivo `alembic.ini` no contiene
credenciales ni una URL de conexión.

Comandos habituales desde la raíz del repositorio:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

La revisión inicial establece la base reproducible. `20260922_0002` crea `branches` para F3.2 y
`20260922_0003` crea el catálogo `products` para F3.3, con clave foránea obligatoria a sucursal,
unicidad de nombre por sucursal e índice para la consulta determinista del catálogo activo.
`20260922_0004` crea `prices` para F3.4 con `NUMERIC(12,2)`, unidad validada, importe no negativo,
unicidad por sucursal-producto-unidad y una clave foránea compuesta que impide mezclar un producto
con la sucursal de otra instalación.
`20260923_0005` agrega `price_import_audits` para F5.5: actor opaco, hora UTC, huella lógica
SHA-256, resultado, conteos y códigos de error. La tabla no almacena el nombre, ruta ni bytes
del Excel. Los registros se consultan siempre por la sucursal configurada.

En una instalación con datos, detener escrituras y obtener un respaldo SQLite verificado antes de
`upgrade head`. `python -m scripts.backup_sqlite --source <archivo.db> --destination <respaldo-nuevo.db>`
crea uno sin sobrescribir otro y comprueba su integridad. Revisar el
procedimiento completo de protección y recuperación en el README principal. Las pruebas recorren
`upgrade` y `downgrade` solo sobre bases temporales. Un `downgrade` productivo puede borrar tablas
y datos; no sustituye la restauración de un respaldo.

Después de `upgrade head`, cada instalación debe cargar únicamente el perfil cuyo código coincida
con su `ASSISTANT_BRANCH_CODE` mediante:

```powershell
python -m backend.app.cli.provision_assistant --profile .\tienda.assistant-profile.json
python -m backend.app.cli.provision_assistant --profile .\tienda.assistant-profile.json --apply
```
