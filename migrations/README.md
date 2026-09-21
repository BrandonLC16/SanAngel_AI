# Migraciones de base de datos

Alembic carga `DATABASE_URL` desde la configuración central. El archivo `alembic.ini` no contiene
credenciales ni una URL de conexión.

Comandos habituales desde la raíz del repositorio:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic downgrade -1
```

La revisión inicial es deliberadamente vacía: establece una base reproducible sin anticipar las
tablas de negocio correspondientes a F3.2 y subfases posteriores.
