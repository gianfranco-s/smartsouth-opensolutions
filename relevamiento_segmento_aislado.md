# Relevamiento del segmento aislado — camino punta a punta (FW / 192.1.3.252)

**Objetivo:** a diferencia de los `relevamiento_alta_*.md` (que recorren un cliente), este plan recorre una **pieza de infraestructura compartida** — el segmento aislado detrás de `FW` (`192.1.3.1`), el tercer perímetro de red confirmado el 12-14 sep 2026 (ver `infra/topology.md` §4). Dos bloqueos concretos, ambos con ruta de acceso ya mapeada, sin necesitar descubrir nada nuevo — solo ejecutarlos:

1. **`WL-CLIENTES` (`172.18.5.40`) — atribuir la actividad real a Argocean o a ROMAN**, hoy bloqueado por falta de `sudo`.
2. **Segundo stack de CEFAS + cliente "SYT" — identificar qué es**, cinco IPs nuevas sin ningún rastro en `ExportList.csv`.

Todo lo de abajo son comandos listos para pegar en una sesión de TeamViewer — no hace falta volver a buscar puertos ni IPs.

## Antes de empezar — dos WAN distintas en el mismo firewall

`FW` tiene **dos IPs WAN**, y las reglas de NAT están repartidas entre ambas — confundirlas hace fallar la conexión sin motivo aparente:

- **`200.55.243.116`** ("WAN address" en el dashboard) — la mayoría de las reglas, incluida la de `WL-CLIENTES` y el grupo "SYT".
- **`200.55.243.117`** — reglas explícitas para el segundo stack de CEFAS (`10.10.1.x`).

Todas las reglas SSH de esta lista usan el alias `OPEN_REDES_PUBLICAS_2024` como origen permitido — si la sesión de TeamViewer no sale con una IP pública dentro de ese alias, la conexión puede rechazarse por el firewall antes de llegar a pedir credencial (no confundir con una credencial mala).

## 1. `WL-CLIENTES` — probar `root` por SSH directo

**Por qué:** ya se accedió por consola remota de vCenter (`soportesmart`) y se confirmó el host vivo (Apache/OHS en `:80`, managed servers en `:9001`/`:9002`, consola admin en `:7001`) — pero **sin `sudo`**, así que no se pudo leer `formsweb.cfg` ni los access logs para saber si el tráfico reciente es de Argocean o de ROMAN. La consola de vCenter nunca pidió una credencial `root` — sigue sin probarse.

```bash
ssh -p 215 root@200.55.243.116
# si pide host key algorithm viejo (mismo patrón que otros hosts del proyecto):
ssh -o HostKeyAlgorithms=+ssh-rsa -p 215 root@200.55.243.116
```

Probar la **misma contraseña de `root`** que funcionó en `192.1.1.31` (ABB), `192.1.1.32` (CLIENTES-DB) y `192.1.1.90`.

**Si entra:**
```bash
find / -iname formsweb.cfg 2>/dev/null   # ruta real, puede no ser la obvia
grep -iE 'argocean|roman' <ruta_encontrada>/formsweb.cfg
# después, acceso logs de OHS (ruta típica ~/config/OHS/ohs1/access_log* o similar):
grep -iE 'config=argocean|config=roman' <access_log> | tail -50
```
Un `[argocean]`/`config=argocean` real en los logs cierra capa 4 de `relevamiento_alta_argocean.md`; si solo aparece `roman`, confirma que la actividad reciente es de ROMAN y Argocean sigue sin tráfico propio (coherente con su ruta de dominio deshabilitada).

**Si `root` es rechazado:** anotar en `infra/findings.md` junto al resto de "sin credencial universal, ni siquiera por segmento" — pasa a la lista de accesos pendientes sin equipo saliente a quien preguntar.

## 2. Segundo stack CEFAS + cliente "SYT" — identificar qué es

Cinco IPs nuevas, todas sin ExportList.csv, todas con ruta SSH ya mapeada. Empezar por las dos más baratas (banner sin credencial), después SSH.

### 2a. Sin credencial — mirar el banner de login de WebLogic (mismo truco ya usado con GIAR)

```
http://200.55.243.117:2144/console/login/LoginForm.jsp   # -> 10.10.1.100:7001, "CEFAS WL admin"
http://200.55.243.116:2234/console/login/LoginForm.jsp   # -> 172.18.5.111:7001, "wl12-cl-syt-CONSOLE"
```
La pantalla de login (sin loguearse) ya dice versión de WebLogic y a veces el nombre del dominio — suficiente para saber si dice "CEFAS" o algo de "SYT" en algún lado visible.

### 2b. SSH a cada host — `hostname` + `ps -ef` alcanza para clasificar

| Rol (nombre de la regla) | IP interna | Comando SSH |
|---|---|---|
| CEFAS WL (2º stack) | `10.10.1.100` | `ssh -p 214 root@200.55.243.117` |
| CEFAS DB (2º stack) | `10.10.1.8` | `ssh -p 213 root@200.55.243.117` (rango 213-218, probar 213 primero) |
| CEFAS Docker/CondorLink | `10.10.1.43` | `ssh -p 2222 root@200.55.243.117` |
| Docker "SYT" | `172.18.5.243` | `ssh -p 2222 root@200.55.243.116` |
| WL12-CLI-SYT | `172.18.5.111` | `ssh -p 2232 root@200.55.243.116` |
| DB-CLI-SYT | `172.18.5.112` | `ssh -p 2233 root@200.55.243.116` |
| "DB-PROD" (genérico, sin cliente) | `172.18.5.6` | `ssh -p 2333 root@200.55.243.116` |

**Ojo:** `10.10.1.43` y `172.18.5.243` usan el **mismo puerto WAN (2222) en WAN distintas** — no es un error, son reglas separadas en `200.55.243.117` y `200.55.243.116` respectivamente.

Con cualquiera de estos, una vez adentro:
```bash
hostname
ps -ef | grep -iE 'java|weblogic|postgres|oracle'
docker ps -a 2>/dev/null
cat /etc/hostname /etc/hosts 2>/dev/null
```

**Qué buscar para clasificar (según la hipótesis abierta en `infra/findings.md`):**
- (a) **CEFAS legado abandonado** — si aparece config/paths con "cefas" pero sin actividad reciente (`ps` sin procesos vivos, o logs viejos).
- (b) **Cliente real sin rastro** — si "SYT" aparece como nombre propio en algún archivo de config, dominio, o base de datos, y hay actividad reciente.
- (c) **Infraestructura interna con nombre en clave** — si no hay nada que apunte a un cliente ni a CEFAS, y el contenido parece genérico/administrativo.

## Al terminar

1. Actualizar el `blind_spot` correspondiente en `infra/inventory.json` (`topic: "Segundo stack de CEFAS y un cliente 'SYT'..."`) con la conclusión, o eliminarlo si se resuelve.
2. Mover el hallazgo a la sección "Resueltos / confirmados" de `infra/findings.md`, con fecha.
3. Si `WL-CLIENTES` se resuelve: actualizar `clients[Argocean].weblogic.resolved` y/o el equivalente de ROMAN en `infra/inventory.json`, y cerrar capa 4 en `relevamiento_alta_argocean.md` (tabla del camino, fila 4).
4. Si aparece un cliente nuevo real ("SYT" u otro nombre): agregarlo a la lista de clientes de `infra/topology.md` §1 y al conteo de `informe_ejecutivo_infraestructura_03.md`.
5. Si ninguno de los dos bloqueos se resuelve (credenciales rechazadas): no hay nada más que intentar por este camino — pasa a la lista de "accesos pendientes sin equipo saliente a quien consultar" de `informe_ejecutivo_infraestructura_03.md`, sin inventar un tercer intento.
6. El esquema de red (`esquema-red-topologia.png` / artifact) **no necesita cambios** por esto — ya muestra el segmento aislado como zona con blind spots pendientes; lo que cambia acá es el detalle en `topology.md`/`findings.md`, no la forma de la red.
