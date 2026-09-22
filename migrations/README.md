# Migraciones de base de datos

Alembic carga `DATABASE_URL` desde la configuración central. El archivo `alembic.ini` no contiene
credenciales ni una URL de conexión.

Comandos habituales desde la raíz del repositorio:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic downgrade -1
```

La revisión inicial establece la base reproducible. `20260922_0002` crea `branches` para F3.2 y
`20260922_0003` crea el catálogo `products` para F3.3, con clave foránea obligatoria a sucursal,
unicidad de nombre por sucursal e índice para la consulta determinista del catálogo activo.
`20260922_0004` crea `prices` para F3.4 con `NUMERIC(12,2)`, unidad validada, importe no negativo,
unicidad por sucursal-producto-unidad y una clave foránea compuesta que impide mezclar un producto
con la sucursal de otra instalación.

Después de `upgrade head`, cada instalación debe cargar únicamente el perfil cuyo código coincida
con su `ASSISTANT_BRANCH_CODE` mediante:

```powershell
python -m backend.app.cli.provision_assistant --profile .\tienda.assistant-profile.json
python -m backend.app.cli.provision_assistant --profile .\tienda.assistant-profile.json --apply
```
