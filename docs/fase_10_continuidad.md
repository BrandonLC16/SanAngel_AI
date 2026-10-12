# F10.7 — Respaldo, restauración y continuidad

## Objetivos iniciales por sucursal

- **RPO objetivo: 24 horas.** Crear y verificar un respaldo al menos cada 24 horas y antes de
  cada migración. Alertar si el último respaldo verificado supera 24 horas. La pérdida real puede
  alcanzar el tiempo desde el último respaldo; registrar la hora de corte en cada incidente.
- **RTO objetivo: 4 horas.** Medir desde la declaración del incidente hasta reanudar el servicio
  de la sucursal después de restaurar, comprobar y conciliar. Es un objetivo inicial, no una
  garantía: repetir un ensayo mensual y ajustar capacidad y objetivo con sus tiempos medidos.

Un trabajo externo del operador debe programar el respaldo diario, comprobar su salida y
transferirlo a almacenamiento cifrado y separado del host. Este repositorio no configura un
servicio de copias remotas ni demuestra los objetivos en una instalación real.

## Protección y retención

Mantener un directorio de respaldo **fuera del repositorio y del volumen de datos activo**, por
sucursal, propiedad del usuario que ejecuta el proceso y con permisos `0700` en Linux. El
comando crea cada archivo nuevo con `0600`, rechaza sobrescrituras y comprueba la integridad y
las claves foráneas. Con `--branch-code` comprueba además la sucursal y la revisión Alembic de
esta imagen. En Windows, conceder acceso solamente a la identidad del trabajo de respaldo y a
los operadores autorizados mediante ACL; los bits POSIX no verifican esas ACL. No colocar
copias en el contexto Docker, en Git, en el panel ni en logs.

Cifrar las copias fuera del host con claves administradas por un gestor de secretos, restringir
lectura y borrado, separar las credenciales de producción y de respaldo y conservar al menos
una copia inmutable o con protección contra borrado. Retener 7 copias diarias como punto de
partida, sujeto a la política de retención y borrado de datos de
[F7](fase_7_privacidad.md); aplicar los borrados programados también a las copias cuando
venzan, y registrar cada acceso/restauración. La base contiene datos personales seudónimos.
Conservar `CONVERSATION_IDENTITY_KEY` en el gestor de secretos **por separado**: se necesita
la misma clave para correlacionar los HMAC restaurados. No incluirla en el respaldo de SQLite.

Un volumen Docker o una copia local en el mismo host no constituye la copia externa requerida.
El trabajo debe avisar al operador ante cualquier error de respaldo, transferencia, cifrado o
verificación de antigüedad. No registrar rutas que incorporen secretos, contenido de mensajes,
tokens ni volcados de la base.

## Respaldo de una instalación

1. Identificar la sucursal configurada y su archivo `DATABASE_URL`. Crear un directorio protegido
   y una ruta de archivo única fuera del repositorio. El backup online de SQLite captura una
   instantánea consistente, incluso con WAL activo; para un respaldo previo a migración, detener
   primero webhooks, workers y otras escrituras de **esa** sucursal.
2. Ejecutar con el mismo código e imagen que usa la instalación:

   ```powershell
   $branchCode = "sucursal-1"
   $sourceDb = "C:\datos\sucursal-1.db"
   $backupDb = "D:\respaldos-protegidos\sucursal-1-$(Get-Date -Format yyyyMMdd-HHmmss).db"
   python -m scripts.backup_sqlite --source $sourceDb --destination $backupDb --branch-code $branchCode
   ```

3. Confirmar código de salida cero y mensaje de verificación. Registrar sucursal, hora UTC,
   revisión, tamaño y tiempo de ejecución sin nombres de clientes ni secretos. Cifrar, transferir
   y comprobar la copia remota mediante descarga, descifrado y comparación de hash antes de
   considerarla recuperable. Verificar diariamente que la última copia recuperable tenga menos
   de 24 horas.

Para un trabajo Docker, montar el volumen de datos de la sucursal y un volumen de respaldo
**independiente**, ambos accesibles por UID 10001; ejecutar la imagen backend con `--network none`
y el filesystem raíz de solo lectura. No montar `/run/secrets` en ese trabajo: las herramientas
SQLite no necesitan credenciales de proveedores. Al usar un volumen nombrado nuevo, asegurar
que su raíz de respaldo pertenezca a UID 10001 y tenga modo `0700` antes de ejecutar el comando.
Los volúmenes `/data` creados antes de F10.7 pueden tener modo `0755`; ajustar su ACL/modo de
forma controlada antes de usar la restauración, sin cambiar propiedad de datos de otra sucursal.

## Ensayo mensual y restauración por incidente

1. Elegir una copia y recuperar su **archivo cifrado** en un directorio aislado y protegido.
   Comprobar que la clave de identidad de la sucursal estará disponible. Registrar hora de
   inicio, punto de recuperación y responsables. Detener webhooks, workers y escrituras de esa
   instalación antes del cambio de base. Revisar recibos `claimed` y envíos ambiguos: SQLite y
   GreenAPI no comparten una transacción.
2. Restaurar a una ruta **nueva** en el volumen de datos de esa misma sucursal o en un volumen
   aislado para el ensayo. El comando no reemplaza un archivo existente ni modifica el respaldo:

   ```powershell
   $restoredDb = "C:\datos\sucursal-1-restaurada-$(Get-Date -Format yyyyMMdd-HHmmss).db"
   python -m scripts.restore_sqlite --backup $backupDb --destination $restoredDb --branch-code $branchCode
   ```

3. El comando debe confirmar `integrity_check`, `foreign_key_check`, sucursal única y revisión
   Alembic. Contra la **copia restaurada y aislada**, ejecutar además `alembic current` y
   `alembic check`, y comprobar registros y consultas representativas sin imprimir PII. Por
   ejemplo, en un ensayo local:

   ```powershell
   $env:DATABASE_URL = "sqlite+pysqlite:///" + ($restoredDb -replace '\\', '/')
   python -m alembic current
   python -m alembic check
   ```

   Si algo falla, conservar la base activa y no reanudar el servicio desde esa copia. No usar
   `alembic downgrade` como restauración.
4. Para un incidente real, establecer `DATABASE_URL=sqlite+pysqlite:////data/<restaurada-nueva.db>`
   en la configuración externa de **esa** instalación, mantener la base anterior intacta y
   reiniciar solo su backend. `deploy/compose.branch.yml` admite esa variable. Confirmar health,
   versión, sucursal, consultas y envío controlado. No reutilizar el volumen en otra sucursal.
5. Conciliar eventos posteriores al punto restaurado con GreenAPI y los registros operativos,
   especialmente recibos `claimed` y envíos de resultado incierto. No reentregar a ciegas:
   podrían duplicarse respuestas. Aplicar la política de borrado/retención a los datos
   restaurados, registrar la hora real de recuperación y reanudar webhooks y workers solo al
   terminar esa conciliación.

Un ensayo debe usar datos sintéticos o un acceso restringido equivalente al de producción.
Registrar el resultado, los tiempos observados, el punto recuperado y cualquier brecha frente a
RPO/RTO. Si la copia más reciente falla, probar la anterior y escalar la pérdida potencial.
