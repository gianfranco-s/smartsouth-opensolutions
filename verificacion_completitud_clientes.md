# Verificación de completitud del relevamiento — por cliente

**Fecha:** 2 sep 2026. Re-cálculo de la verificación general hecha al principio del proyecto, con los datos producidos en esta sesión (trazado de EBY capas 1-3/7 cerradas y 4/6 muy avanzadas vía `OPENWLPROD01`, corrección del cierre de JOBS/Enerflex, hallazgos del re-dump de NPM de `DOCKER-DEB` sobre ROMAN/GIAR/MAIPU/HEINLEIN/Rex).

## Método (igual que la primera vuelta, ahora con la regla explícita)

Se mide cada uno de los 15 clientes contra el mismo modelo de 7 capas que usan `plan_relevamiento_alta_cefas.md` / `plan_relevamiento_alta_jobs.md` / `plan_relevamiento_alta_eby.md`: dominio de entrada → NPM → firewall/NAT → app motor clásico → app Docker/reportes → base de datos → almacenamiento. Solo CEFAS, JOBS y EBY tienen ese trazado formal; el resto es una extrapolación con la misma vara.

Puntaje por capa:

| Puntaje | Significa |
|---|---|
| **1.0** | Verificado en vivo — sesión SSH/consola/`sqlplus`, o evidencia de red directa (`netstat` con tráfico real) |
| **0.6** | Evidencia de red fuerte pero sin verificación directa (ej. `netstat` confirma destino, `sqlplus` bloqueado por credencial) |
| **0.5** | Identificado por nombre/IP/dominio (CSV, matriz, o entrada de NPM) pero sin sesión que lo confirme |
| **0.3** | Señal débil, parcial o en disputa (dos fuentes no coinciden, dominio deshabilitado, IP sin VM) |
| **0** | Sin dato |

## Headline

**Global ponderado: ~49%** (subió de ~43% en la medición anterior). El salto viene sobre todo de tres cosas: EBY pasó de conjetura a trazado real (capas 1-3 y 7 cerradas, 4 y 6 muy avanzadas), y una corrección de scoring en JOBS/Enerflex — ya estaban resueltos antes de esta sesión, la medición anterior los había subestimado.

## Por cliente

| Cliente | % anterior | % ahora | Qué cambió |
|---|---|---|---|
| **CEFAS** | 100 | **100** | Sin cambios — trazado completo, verificado en vivo. |
| **JOBS** | ~90 | **100** *(corrección)* | Ya estaba cerrado (capas 4-7 confirmadas por PID/`netstat`/`tnsnames.ora` el 1 sep) antes de que arrancara esta sesión — la medición anterior lo calificó de "relevando" por error. |
| **ENERFLEX** | ~57 | **~73** *(corrección)* | Comparte `WL12C-PROD`/`CLIENTES-DB2` con JOBS — el mismo cierre de JOBS ya lo verificaba en vivo (`WLS_FORMS1` sirve `enerflex.condorwork.com.ar`, `ORDS-Enerflex` mapeado por PID a `.51`/`.32`/`.24`). Falta el charset propio (fila abierta en Discrepancias) y su capa 5, por eso no llega a 100. |
| **EBY** | ~36 | **~81** | El salto grande de la sesión. Capas 1, 2, 3 y 7 cerradas (rutas de entrada, NPM, firewall, sin storage dedicado). Capa 4: dos motores Forms productivos identificados y uno (`OPENWLPROD01`) con dominio/managed servers confirmados por sudo. Capa 6: evidencia de red limpia (100% del tráfico real a `OPENDBPROD005`) pero `sqlplus` bloqueado por credencial — no llega a verificación completa. Capa 5 sigue abierta pero con evidencia indirecta de que no aplica. |
| **GIAR** | ~50 | **~55** | Dominio propio nuevo, habilitado: `giarprod.condorenterprise.com.ar` → `200.55.243.117` (IP pública). Sigue "de baja" según la matriz — sin confirmar en vivo. |
| **ROMAN** | ~36 | **~38** | Candidato nuevo a WL real: `romanprod`/`romanqa.condor.solutions` → `OPENWLPROD01`, habilitados (el viejo `roman.condorwork.com.ar` quedó deshabilitado). Identificado por patrón de NPM, no verificado en vivo — nadie entró a `OPENWLPROD01` a confirmar sesiones/DB de ROMAN específicamente. |
| **MAIPU** | ~14 | **~20** | Primeros dominios conocidos: `qadmportal.condor.solutions` → `DASADBPROD01` (deshabilitado) y una redirección hacia `dmportal.condor.solutions` (no resuelto todavía). Sigue "solo infraestructura". |
| **HEINLEIN** | ~14 | **~20** | Primer dominio conocido: `heinleintest.condor.solutions` → `OL8LABWL01` — pero es un ambiente de test, no confirma producción. |
| **Rex Argentina (279)** | ~29 | **~33** | Candidato nuevo, sin confirmar identidad: `serzarex.condor.solutions` → `OL8LABWL01` (el WL de Heinlein), habilitado. Podría ser Rex (además de su Self Service ya conocido en `192.1.1.57`) o un nombre no relacionado — no asumir sin verificar. |
| DVAL | ~43 | 43 | Sin cambios esta sesión. |
| BOCA | ~43 | 43 | Sin cambios esta sesión — comparte `WL12C-Desarrollo`/`CLIENTES-DB` con ABB/EBY, ninguno de los tres verificado en vivo todavía en ese box. |
| ABB | ~33 | 33 | Sin cambios esta sesión. |
| DCVIAJES | ~36 | 36 | Sin cambios esta sesión. |
| ESYOP | ~29 | 29 | Sin cambios esta sesión. |
| Argocean | ~29 | 29 | Sin cambios esta sesión. |

## Por capa (los 15 clientes)

| Capa | Antes | Ahora | Por qué se movió |
|---|---|---|---|
| 1 · Dominio de entrada | ~70% | **~78%** | EBY (10 rutas), ROMAN, GIAR, MAIPU, HEINLEIN y Rex ganaron dominios nuevos del re-dump de `DOCKER-DEB` (101 proxy hosts). |
| 2 · Nginx Proxy Manager | ~35% | **~42%** | Mismo re-dump — EBY y ROMAN identificados con más confianza. Sigue faltando transcribir `OPENDOCKER04` y la réplica `VM-DOCKER-Clientes (1)`. |
| 3 · Firewall / NAT | ~55% | ~55% | Sin cambios — el único NAT nuevo revisado (EBY) confirmó el mismo patrón genérico ya conocido. |
| 4 · App (motor clásico) | ~55% | **~65%** | JOBS/Enerflex re-contados como verificados; EBY con dos motores identificados (uno con dominio/sudo confirmados). |
| 5 · App Docker / reportes | ~20% | ~22% | Casi sin cambio — EBY sumó evidencia indirecta de que no aplica, no una confirmación positiva de otro cliente. |
| 6 · Base de datos | ~50% | **~60%** | JOBS/Enerflex verificados por PID; EBY con evidencia de red fuerte (100% del tráfico real a una VM identificada) aunque sin `sqlplus`. |
| 7 · Almacenamiento | ~10% | **~17%** | EBY se suma a CEFAS como capa cerrada — en este caso confirmando que **no aplica** (sin mount NFS dedicado), no que exista. *Nota: la "capa 7" de JOBS no es storage sino "ambientes no productivos" — no son directamente comparables, ver los planes fuente.* |

## Caveats (se mantienen los de la primera vuelta)

- Solo CEFAS, JOBS y EBY tienen trazado formal de 7 capas — el resto es extrapolación con la misma vara, no medición directa.
- La diferencia de **confianza** sigue importando: EBY tiene capas cerradas por evidencia de red fuerte pero no siempre por `sqlplus`/consola directa (bloqueo de credencial activo, ver `QUESTIONS.md`). Si se cuenta solo lo verificado con acceso directo a la DB, EBY baja de ~81% a ~65%.
- Los clientes "planos" (ABB, DVAL, BOCA, DCVIAJES, ESYOP, Argocean) no tuvieron sesión nueva esta ronda — su score sigue siendo la extrapolación original, no una remedición.
- ROMAN, GIAR, MAIPU, HEINLEIN y Rex ganaron *evidencia de dominio*, no verificación en vivo — no tratar el dominio nuevo como "capa resuelta" sin más, es el mismo tipo de salto que ya corrigió el caso EBY (dominio conocido ≠ motor/DB confirmados).

## Próxima verificación sugerida

Por orden de impacto, siguiendo la misma lógica de "elegir el cliente que más destraba":

1. **Cerrar capa 4/6 de EBY** (los `.env`/`formsweb.cfg`/`tnsnames.ora` de `OPENWLPROD01`, en curso) — sube a EBY a ~90%+ y probablemente confirma/descarta a `Database .90` sin necesitar la credencial bloqueada.
2. **Sesión en `192.1.2.54` (`WL12C-Desarrollo`)** — nunca accedida, resuelve de un saque ABB (Tier 1 #4), BOCA y la porción de EBY que queda ahí (ORDS/tests).
3. **Confirmar si `serzarex` es Rex Argentina** — de serlo, cierra el ítem 2 de Tier 1 (Rex sin DB mapeada) casi gratis, aprovechando que `OL8LABWL01` ya está identificada.
4. **Verificar en vivo si ROMAN realmente migró a `OPENWLPROD01`** — mismo box donde ya hay sesión abierta para EBY, bajo costo marginal.
