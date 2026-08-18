# Tier 1 — plan de ejecución

Detalle paso a paso de los 4 ítems de `PLAN.md` § Tier 1. Objetivo: cerrar la ruta completa cliente → dominio → proxy → firewall/NAT → servidor para al menos un cliente, y resolver los 3 vacíos/discrepancias puntuales que quedan en la capa cliente→WL→DB.

Al terminar cualquier ítem: actualizar `infra/inventory.json` (el campo correspondiente — `docker_detail`/NAT en la VM de firewall, `resolved` en el cliente, `matrix_detail`), y mover la entrada resuelta de `infra/findings.md` a "Resueltos" con fecha. Si el ítem 1 cambia el diagrama de topología, regenerar `infra/topology.md` §1 desde el JSON en vez de editar el Mermaid a mano (ver `CLAUDE.md` punto 2).

---

## 1. Mapa dominio → Nginx Proxy Manager → servidor/puerto interno

**Por qué primero:** es la única pieza que falta para que "este dominio tira error" se resuelva tan rápido como "la app de X está caída". Las otras tres son gaps puntuales de un solo cliente cada uno.

**Lo que ya sabemos** (`infra/inventory.json`, `infra/findings.md`):

| Host Docker | IP(s) relevantes | Nginx Proxy Manager |
|---|---|---|
| `DOCKER-DEB` | `192.1.1.37` | sí (+ MariaDB, Sarha Online detenido) |
| `OPENDOCKER04` | `10.77.7.5` | sí |
| `VM-DOCKER-Clientes` | `192.1.1.38` | sí (+ frontend/backend CEFAS, PostgreSQL, MariaDB) |
| `VM-DOCKER-Clientes (1)` | `172.18.5.123` / `10.10.1.43` / `192.1.3.4` | sí (mismo stack que arriba) |

Firewalls pfSense confirmados con acceso real por dashboard (7 de 9 — ver tabla completa en `inventory.json` → `vms[].confirmation`): `OPENVPNFW01`, `CliProFw01`, `DMFW01`, `FW`, `FWOPEN`, `OPENFWCLI001`, `OPENFWCLI10`.

**Pasos:**

1. **Entrar a cada una de las 4 instancias de Nginx Proxy Manager** (puerto de admin típico `81`, a veces detrás del propio proxy — revisar `docker ps` si no responde) y exportar/anotar, por cada Proxy Host configurado: dominio, destino interno (IP:puerto del contenedor/servicio real), y si tiene SSL/forzado HTTPS.
   - Empezar por `VM-DOCKER-Clientes` y `VM-DOCKER-Clientes (1)` — ya se sabe que sirven CEFAS, así que dan un caso de referencia para validar el método antes de generalizar.
   - Confirmado en vivo (18 ago 2026): `http://192.1.1.38:81/` (`VM-DOCKER-Clientes`) responde con la pantalla de login de NPM desde una sesión de TeamViewer a Piedras (`192.168.100.165`) sin necesitar un salto intermedio — ver `infra/findings.md`. Falta la credencial para entrar de verdad.
2. **Para cada dominio encontrado, ubicar la regla NAT/port-forward correspondiente en el pfSense que lo recibe.** No asumir cuál firewall es — cruzar por rango de IP: cada host Docker está detrás de un pfSense distinto según su segmento (`192.1.1.x` → probablemente `FWOPEN`/`FW`; `10.77.7.x` → posible `OPENFWCLI10`/`CliProFw01`, que tienen patas en `10.77.x`; confirmar en el dashboard, no adivinar).
   - En cada pfSense: Firewall → NAT → Port Forward. Anotar IP/puerto externo → IP:puerto interno del host Docker.
3. **Armar la tabla dominio → NPM host → destino interno → NAT/firewall** y guardarla en `inventory.json` (nuevo bloque, p.ej. `infra_docker.nginx_proxy_manager_routes` o dentro de cada `docker_detail` como `proxy_hosts`) más un resumen en `topology.md`.
4. **De paso, resolver la pregunta abierta del punto 6 de Tier 2** si aparece evidencia: si algún dominio apunta a `OPENPORTAL01`, `OPENPORTALCLI02` o `WEBSERVER`, eso confirma su rol real sin necesidad de una pasada aparte.

**Qué faltaría después de esto:** ninguno de los pasos de arriba cubre los 2 firewalls todavía sin confirmar (`OPENFWCLI02`, `VM_FW` — quedan en Tier 3). Si alguno de los dominios mapeados termina detrás de uno de esos dos, eso los confirmaría gratis — anotarlo si pasa.

---

## 2. Base de datos de Rex Argentina

**Estado actual** (`inventory.json` → `clients[]`, cliente "Rex Argentina", código `279`): cero recursos resueltos. La matriz solo dice `database.claimed_name = "REX Produccion"`, sin IP ni nombre de VM. No aparece por nombre en `Relevamiento CSV` ni en `ExportList.csv`. Cliente activo en PROD, usa Condor Work, ~15 usuarios / 4.600 legajos — no es un cliente de baja prioridad.

**Pasos:**

1. **Buscar por nombre en vCenter directamente** (no solo por el CSV export estático) — filtrar VMs por `rex`, `REX`, `279` en nombre o notas. El CSV export puede no tener el nombre exacto que usa vCenter.
2. Si no aparece por nombre: **revisar qué WebLogic/host quedó asignado en el proceso de alta reciente** — dado que la matriz dice "Hosting: Sí, Migrado: No, Patch: 1", es un cliente que se sumó *después* de que se armara el CSV de Relevamiento. Candidatos naturales: alguna de las ~31 VMs con patrón WL/DB sin código de cliente en el nombre (Tier 2, ítem 5) — puede ser que Rex ya esté ahí pero sin identificar todavía. Vale la pena adelantar la revisión de esas VMs específicamente para el patrón "PROD reciente, Condor Work" antes de hacer la pasada completa de Tier 2.
3. Si tampoco aparece ahí: **preguntar a alguien de Open con acceso al proceso de alta** dónde quedó provisionada la DB — puede ser candidato para `QUESTIONS.md` si no se resuelve por TeamViewer.
4. Al encontrarla: completar `clients[].database.resolved` en `inventory.json` (con `resolved_by: "name"` o `"ip"` según corresponda) y actualizar `weblogic.resolved` también si aparece en el mismo lugar.

---

## 3. Ruta completa de EBY

Ya tiene detalle paso a paso en `PLAN.md` § "Tier 1, ítem 3" — reproducido y ampliado acá.

**Las dos preguntas, mismo cliente, misma hoja Discrepancias:**
- DB: ¿`OPENDBPROD006` es realmente la base de EBY?
- WL: ¿ya migró a `10.77.7.201` (destino, según fuente funcional) o sigue en `192.1.2.54` (compartido, según inventario técnico)?

**Dato nuevo, a verificar con cuidado (18 ago 2026):** el cross-reference contra los exports nuevos encontró una tercera IP candidata, `10.77.8.201`, en la nota de `OPENWLCLI01` ("EBY PRODUCCION / 10.77.8.201 / ..."). No tratarla como un tercer candidato confiable sin más: esa misma nota mezcla varios clientes sueltos y termina con una frase idéntica palabra por palabra a la nota de una VM completamente distinta (`PiedrasWL01`, sitio Piedras) — fuerte indicio de que la columna `Notas` tiene contenido pegado entre celdas, no fiable por sí sola. Ver `infra/findings.md` § "Todavía abierto" ítem 4. Si al entrar a `10.77.7.201`/`192.1.2.54` (paso 2 de abajo) ninguno muestra actividad reciente, vale la pena probar `10.77.8.201` como tercera opción — pero confirmarlo en vivo, no por la nota sola.

**Pasos:**

1. **DB primero, es más rápido:** conectar a `OPENDBPROD006`, `sqlplus / as sysdba` → `SELECT name FROM v$database;` y `cat /etc/oratab` para ver todas las instancias del host. Comparar contra el SID esperado (`MBA` actual / `EBYPROD` destino según la matriz). Si no coincide ningún SID con EBY, buscar el SID real en `/etc/oratab` de los servidores DB conocidos de clientes vecinos.
2. **WL — el dato clave es cuál tiene actividad real, no cuál tiene el deployment presente** (puede estar desplegado en los dos por una migración a medio hacer):
   - Entrar a `10.77.7.201` (`OPENWLPROD01`, el mismo WL de GIAR) → consola de administración → ver si hay un dominio/aplicación de EBY desplegada, y si tiene sesiones o logs recientes.
   - Entrar a `192.1.2.54` (`WL12C-Desarrollo.2.54`) → mismo chequeo.
   - El que tenga sesiones/logs de usuarios de EBY *recientes* (no solo el deployment presente) es la ruta real hoy.
3. Actualizar `clients[].matrix_detail` de EBY en `inventory.json` con el valor confirmado de cada pregunta, y mover la fila EBY de la tabla de Discrepancias en `infra/findings.md` a "Resueltos" con fecha.

---

## 4. ABB — cuál DB es la productiva

Ya tiene detalle en `PLAN.md` § "Tier 1, ítem 4" — reproducido acá. Nota: ABB es uno de los dos clientes con la nota contradictoria "de baja" vs. "Mantenimiento solamente" (ver `findings.md` § "los 13 clientes son más bien 15, con bajas") — igual vale resolver cuál DB es la activa, independientemente de ese estado.

**Las dos candidatas:** `192.1.1.31` (`DBClientes-12C.31`) vs. `192.1.1.190` (`DBClientes.190`).

**Pasos:**

1. **Camino más directo — datasource JDBC:** consola de WebLogic en `WL12C-Desarrollo.2.54` (`192.1.2.54`) → Services → Data Sources → buscar el datasource de ABB → leer la URL JDBC. Ahí dice literalmente a cuál de las dos IPs se conecta la aplicación.
2. **Segundo chequeo, si el paso 1 no es concluyente (p.ej. datasource apunta a un hostname/VIP en vez de IP directa):** conectarse a cada una de las dos DBs y correr:
   ```sql
   SELECT sid, serial#, username, program FROM v$session WHERE username IS NOT NULL;
   ```
La que tenga sesiones activas de la aplicación de ABB es la productiva.
3. Actualizar `clients[].database.resolved` de ABB en `inventory.json` (marcar la IP no productiva como histórica/legacy si corresponde) y mover la fila ABB de Discrepancias a "Resueltos" en `findings.md`.
