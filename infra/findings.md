# Hallazgos y preguntas abiertas

**Alcance: solo infraestructura on-premise.** La infraestructura en proveedores cloud (Azure/AWS) se estacionó fuera de este relevamiento — ver [`../cloud-infra/findings-cloud.md`](../cloud-infra/findings-cloud.md) para lo que ya se había encontrado ahí (incluye un hallazgo importante, una VM de Azure sin inventariar, por si se retoma).

Fuentes: ExportList.csv (export de vCenter, verdad de base para "qué VM existe"), CSV de Relevamiento (manual, 13 clientes, solo WL+DB), y — agregado después — dos emails internos más su adjunto RAR (`source-files/extracted/`), que contiene una matriz de servicios por cliente más completa y un relevamiento de infraestructura Docker. **Todo el material derivado de Relevamiento y de los emails es documentación interna de trabajo, no verdad verificada — tratar cada hallazgo de abajo con las mismas pinzas que aplican los propios documentos fuente** (la hoja "Discrepancias" de la matriz existe justamente porque el propio equipo de Open encontró que sus dos fuentes de datos no coincidían).

## Nuevo: infraestructura on-premise real que no está en nuestro inventario

Buscamos todas las IPs mencionadas en el material fuente y las cruzamos contra `inventory.json`. Del lado on-premise, encontramos una sola cosa sin identificar:

- **Servidor(es) NFS.** `OPENDOCKER.57` y `VM-DOCKER-Clientes` montan recursos NFS externos (uno con "montaje con error" y otro "con alta ocupación", según el relevamiento de Docker) pero el host NFS nunca se nombra. Fácil de resolver nosotros mismos: entrar por TeamViewer a esos dos hosts y correr `mount`/revisar `/etc/fstab`.

(El mismo cruce encontró dos cosas del lado cloud — una VM de Azure sin inventariar y una mención sin detalle de AWS — documentadas en `cloud-infra/findings-cloud.md` en vez de acá.)

## Resueltos / confirmados

**nginx — resuelto.** `Relevamiento_general_infraestructura_Docker_actualizado.docx` confirma que Nginx Proxy Manager corre como contenedor en 4 de los 9 hosts docker: `DOCKER-DEB`, `OPENDOCKER04`, `VM-DOCKER-Clientes`, y `VM-DOCKER-Clientes (1)`. No es una categoría de host dedicado — es un servicio containerizado. La conjetura anterior `web_frontend_nginx_candidate` (`OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER`) estaba equivocada; el rol real de esas VMs sigue sin confirmar.

**pfsense — confirmado para 7 de 9 hosts.** `Analisis Azure.docx` (ver `cloud-infra/source/`) ya había confirmado `OPENVPNFW01` (VPN Site-to-Site de Azure, peer "pfSense" en `200.55.243.92`). `source-files/Relevamiento (sin claves) - Pfsense.csv` — un relevamiento manual con acceso real al dashboard de cada firewall — confirma 6 más: `CliProFw01`, `DMFW01`, `FW`, `FWOPEN`, `OPENFWCLI001`, `OPENFWCLI10`. Cada uno tiene su IP de dashboard, credencial de acceso (usuario `smartsouth`, sin contraseña en el archivo) y una etiqueta de destino — por ejemplo `DMFW01` aparece etiquetado "Open - Maipu", consistente con ser el firewall dedicado de ese cliente. Solo quedan sin confirmar `OPENFWCLI02` y `VM_FW`. Detalle completo en `inventory.json` → `vms[].confirmation`.

**Hallazgo positivo: exposición a Internet mínima.** El mismo relevamiento de firewalls anota: "No hay puertos TCP expuestos (SSH 22, HTTP 80, HTTPS 443, o la administración de pfSense). El único servicio escuchando conexiones desde Internet es OpenVPN en el puerto 2190 (UDP)." A diferencia del hallazgo de Azure (red plana, sin NSGs — ver `cloud-infra/`), esto es una superficie de exposición chica del lado on-premise: el acceso externo pasa por un único punto.

**`DB-ARGOCEAN` — resuelto.** Es la base de datos de un cliente llamado **Argocean**, según la hoja Discrepancias de la matriz ("DB 172.18.5.60 / SID MBA — No figura [en tabla funcional]"). Argocean no está en la lista original de 13 clientes en absoluto — apareció solo en las notas de discrepancias. La VM está actualmente apagada en ExportList.csv, y todavía no se identificó ningún servidor WebLogic para ella.

**GIAR — versión de WebLogic resuelta (16 ago 2026).** Verificado por TeamViewer entrando a `http://10.77.7.201:7001/console/login/LoginForm.jsp` (`OPENWLPROD01`): la página de login muestra "Versión de WebLogic Server: **12.2.1.4.0**". Confirma el valor del inventario técnico (`12.2`); el valor funcional ("WL 11") era el desactualizado. No se pudo entrar a la consola en sí — la cuenta compartida (`soportesmart`) fue rechazada, así que solo se confirmó la versión desde la pantalla de login, no el resto del dominio. **Gotcha a tener en cuenta:** `10.77.7.201` (GIAR) y `10.77.10.101` (Maipú) se confunden fácil al leerlas rápido — casi se registra este dato contra el cliente equivocado.

## Nuevo: los "13 clientes" son más bien 15, con bajas

La matriz (`Matriz_servicios_por_cliente_Hosting_V2.xlsx`) agrega dos clientes que no estaban en el CSV de Relevamiento:

- **Rex Argentina** (código `279`) — "incorporado recientemente al hosting", entorno PROD, usa Condor Work, DB referenciada solo como "REX Producción" (todavía sin resolver a una VM específica — necesita una búsqueda por TeamViewer, ~15 usuarios / 4.600 legajos según las notas de la matriz).
- **Argocean** — ver arriba, por ahora solo con DB, sin WebLogic identificado.

Más importante todavía, aunque con una fuente más floja de lo que parece a primera vista: **una nota suelta en la matriz dice que ABB S.A. y Arris de Argentina S.A. (GIAR) ya son clientes dados de baja**, con sus bases de datos retenidas solo temporalmente. Esa nota está pegada debajo de la tabla principal del Excel (no es un campo formal), y dice textual "Estos dos clientes estan de baja pero por el momento se mantiene sus bases". El problema: el campo formal `Estado / migración` de esos mismos dos clientes, en la misma planilla, dice **"Mantenimiento solamente"** — no "de baja". No son necesariamente contradictorios (podría estar en mantenimiento mientras se lo da de baja), pero es una nota informal contradiciendo, o al menos matizando, un campo estructurado — no algo para dar por hecho. Confirmar con el equipo saliente antes de tratar a cualquiera de los dos como cliente de baja prioridad. (Ambos siguen apareciendo en `used_by_clients` en inventory.json de todas formas, ya que sus VMs todavía existen y están encendidas.)

## Nuevo: la matriz documenta sus propias discrepancias sin resolver

La hoja "Discrepancias" de la matriz es el propio equipo de Open detectando conflictos entre una fuente "funcional" (de una persona llamada Fran) y el inventario "técnico" — vale la pena llevarla adelante tal cual en vez de re-derivarla:

| Cliente | Tema | Dice la fuente funcional | Dice el inventario técnico |
|---|---|---|---|
| ROMAN (CSM) | Versión de WebLogic | WL 11 | 10 |
| JOBS | Versión de WebLogic | WL 12 | 11 |
| ABB | DB actual | `192.1.1.31` / SID ABB | `192.1.1.31` y `192.1.1.190` (dos IPs) |
| CEFAS | SID | CEFASPDB | CEFAS |
| BOCA | SID | BOCAPDB | BOCA |
| EBY | Servidor WebLogic | destino `10.77.7.201` | actual, compartido: `192.1.2.54` |
| Enerflex | Charset | `WE8ISO8859P15` | sin verificar — marcado como posible error de tipeo |

El documento explícitamente **no** eligió un valor por sobre el otro cuando las fuentes no coincidían — la misma política que debería seguir este proyecto. Ver `clients[].matrix_detail` en inventory.json para el detalle completo por cliente (SID, versión/edición/tamaño/charset de DB, destino de migración, qué productos Condor usa cada cliente).

## Todavía abierto

### 1. El alcance de Relevamiento (solo WL+DB) implica que ausencia ≠ cliente nuevo

(Ver análisis previo, sigue vigente.) Solo 2 de los 13 clientes originales muestran una coincidencia de nombre para infraestructura adicional sin documentar: **GIAR** tiene una instancia extra `WL-GIAR` además de su `OPENWLPROD01`/`DB-GIAR` mapeados, y **ROMAN** tiene un `WL-ROMAN` y un `DB-ROMAN-HISTORICO` extra además de su `WL-CLIENTES`/`DB-ROMAN` mapeados. Otras ~31 VMs con patrón WL/DB no llevan ningún código de cliente en el nombre y todavía necesitan una pasada por TeamViewer para clasificarlas como: otro componente de un cliente conocido, una copia de dev/QA/test, o un cliente genuinamente separado (como resultó ser Argocean).

### 2. Dos filas sin resolver de Relevamiento fuera de los 13 clientes — una ya explicada

La IP que Relevamiento le atribuye a `opendocker03` (`192.1.1.113`) no aparece en ExportList.csv — pero eso ya tiene explicación: `OPENDOCKER03` está apagada ("Apagado") en el export, y vCenter solo reporta las IPs de un invitado cuando VMware Tools está corriendo. El documento de relevamiento de Docker confirma de forma independiente que `OPENDOCKER03` está en `192.1.1.113` (Ubuntu 22.04, 1 contenedor activo — Portainer), así que la entrada de Relevamiento es correcta; ExportList.csv simplemente no pudo verla en el momento de la captura porque la VM estaba apagada. `portalDM` (IP `10.77.10.5`) probablemente sea = `OPENPORTAL01` (misma IP) pero sigue sin confirmar.

### 3. Segundo host ESXi (`192.1.3.252`) — probablemente un sitio separado

Todavía sin confirmar si es una segunda ubicación física o una máquina standalone; aloja la infraestructura de GIAR y ROMAN que no está en el rango `192.1.1.x`.

### 4. "Piedras" — más evidencia de que es real, pero todavía sin confirmar

Se nos había mencionado verbalmente que existiría un sitio llamado "Piedras". Dos rastros técnicos independientes, y ninguno cierra la pregunta:

- El nombre de una VM, `VEEAM-PIEDRAS` (backup, Windows Server 2016), que corre en `192.1.1.221` — **dentro del cluster principal**, no en `192.1.3.252`.
- Una fila en `Relevamiento (sin claves) - Pfsense.csv` etiquetada explícitamente **"Open - Piedras"**, apuntando a un dashboard de firewall en `https://192.168.100.1/` — un rango de IP que no aparece en ningún otro documento ni en ExportList.csv, lo que sí apoya que sea un sitio físico separado. Pero la observación del relevamiento dice **"no responde"** — no se pudo entrar ni confirmar nada más.

Sube la confianza en que "Piedras" es un sitio real (dos fuentes independientes lo nombran), pero seguimos sin poder confirmar qué es ni por qué no responde. Ver `QUESTIONS.md` y el paso 7 de la próxima pasada, abajo.

## Próxima pasada sugerida por TeamViewer (en orden de prioridad)

1. Confirmar el estado real de ABB y GIAR (¿de baja, o solo "mantenimiento"? la fuente se contradice, ver arriba) antes de bajarles prioridad a sus entornos.
2. Resolver la identidad de la VM de base de datos de Rex Argentina — es un cliente PROD actual sin VM mapeada todavía.
3. Confirmar o descartar pfsense en las 2 VMs `firewall_candidate_pfsense` que quedan (`OPENFWCLI02`, `VM_FW`) — las otras 7 ya están confirmadas.
4. Recorrer las 12 VMs `infra_generic_unclear` (`OPENINFRxx`) — sin ninguna señal en el nombre.
5. Para las ~31 VMs con patrón WL/DB todavía sin mapear, clasificar cada una como producción-de-un-cliente-sin-documentar vs. dev/QA/test/histórico vs. componente de un cliente conocido.
6. Confirmar el rol real de `OPENPORTAL01`, `OPENPORTALCLI02`, `WEBSERVER` ahora que se sabe que la conjetura de nginx para ellos era incorrecta.
7. Entrar a `VEEAM-PIEDRAS` y revisar la configuración de sus jobs de backup (repositorios, destinos de replicación) — si replica hacia una IP/rango fuera de los que ya conocemos, eso confirmaría un sitio adicional real detrás del nombre "Piedras".
