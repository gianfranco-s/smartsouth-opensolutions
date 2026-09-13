# Informe infraestructura Open Solutions — entrega 02

Esta segunda entrega complementa el informe 01 (mapa on-premise, sitios, clientes y candidatos a baja). Incorpora tres cosas nuevas: lo que aclaró la reunión con el equipo saliente sobre el modelo de producto y de cliente, la arquitectura de aplicación punta a punta incluyendo la capa cloud (los ORDS que conectan los portales de Azure con las bases Oracle on-premise), y el avance del trazado detallado por cliente (ABB, BOCA, EBY, JOBS, ROMAN). Fuentes: notas de la reunión (`Documentación general de sistemas TI`), `plan_relevamiento_azure.md`, `infra/findings.md` e `infra/inventory.json`.

## Modelo de producto y de cliente

- **Producto principal: ecosistema CONDOR**, sobre dos tecnologías: **Condor** (desarrollo in-house, base Oracle propia) y **Aplicaciones Oracle** (Forms & Reports sobre WebLogic, con otra base Oracle). Existen además productos basados en Docker (Self Service, JasperReports) que van por fuera de ese núcleo.
- **Arquitectura objetivo: un cliente = dos VMs** — una VM Condor (servicio + Oracle) y una VM Aplicaciones (aplicaciones Oracle + Oracle). El Especialista Oracle (Francisco Ramasco) declara estar **en proceso de desacoplar clientes** para converger a ese modelo; hoy varias VMs son multi-cliente (`WebLogic.191` sirve a 8 clientes).
- **Conexión de cada cliente, a medida**: VPN, punto a punto, Internet libre, o Internet con whitelist. Heinlein es punto a punto. Último cliente dado de alta: **Heinlein**; el anterior, **Serza**.
- **Proceso de alta formal de 6 etapas**, repartido entre Especialista Oracle (dimensionamiento, solicitud de VMs, configuración del servicio con template DB) e Infraestructura (alta de VMs con nomenclatura tipo `OL8-HEINLEIN-PROD` sobre ISO Oracle Linux, backups, accesos).
- **Traspaso de responsabilidades a Smart South**: Alta de VMs (Lucas Reta toma el conocimiento) y Conectividad de clientes (la venía haciendo InfoLogic / antes Diego Sosa). El propio equipo marca la conexión con clientes como **punto frágil** — Open no tiene experiencia en esa función y no hay traspaso de know-how documentado.
- **`object store`**: se usa principalmente para backups, no como almacenamiento de aplicación.

## Arquitectura de aplicación punta a punta

**On-premise (motor clásico):** Internet → pfSense de borde (`OPENVPNFW01`, solo OpenVPN publicado) → pfSense interno (`FWOPEN`, NAT hacia los NPM) → Nginx Proxy Manager (ruteo por dominio / Host header) → motor WebLogic / Oracle Forms & Reports **o** contenedores Docker → base Oracle del cliente. Uploads por mount NFS servido por el propio WebLogic, sin object store centralizado.

**Cloud (Azure) — cómo entra:** los portales Angular de CONDOR (Work / Enterprise / ProvIA) corren en AKS con backend .NET. Para leer o escribir datos de un cliente, el backend pregunta a la **base Core** qué ORDS corresponde a esa organización y luego pega por HTTPS a `ords-<cliente>.open.com.ar` — un endpoint publicado por el NPM on-premise cuyo destino real es un ORDS (Oracle REST Data Services) **pegado a la base Oracle del cliente, on-premise**. Autenticación por `apikey` + `producto` en el header, validada en la base del cliente. **El grueso del tráfico app→datos va por estos ORDS, por Internet** — la VPN S2S Azure↔datacenter lleva tráfico casi nulo (~487 MiB/30d).

**Hallazgo cloud principal:** **no existe ninguna "VM Core" standalone.** El segmento `10.66.66.0/24` es la VNet del cluster `aks-provia-prod01` (Brazil South), hoy **detenido y con aprovisionamiento fallido**. Queda por aclarar con el equipo saliente qué resuelve hoy el login de ProvIA y si ese cluster se apagó a propósito. Verificado contra el portal con acceso `Reader` real (9 sep 2026): 5 clusters AKS (solo 2 corriendo), 3 PostgreSQL flexibles, 2 container registries, 4 directorios Entra ID B2C, sin NSGs en ninguna subred.

**Clientes que pasan por Azure** (tienen `ords-<cliente>` propio publicado): Balanz, BOCA, CEFAS, EBY, JOBS, ROMAN.

## Avance del trazado por cliente

Trazado = seguir el circuito de un cliente capa por capa (entrada → firewall → NPM → motor → Docker → base de datos → storage), confirmando cada capa contra el sistema real, no contra la documentación.

| Cliente | Estado | Observación clave |
|---|---|---|
| **ABB** | 7/7 completo | DB productiva = `192.1.1.31` (instancia `ABB`, schema de app `CONDOR`). **Sin una sola sesión ni DML desde el 1-jul-2026**, con la infraestructura igual encendida — apagado de hecho. Apoya (no prueba) la nota de baja de la matriz. |
| **JOBS** | 7/7 completo | Forms & Reports 12.2.1.4.0 en `WL12C-PROD` (`192.1.1.1`), pese a figurar como "WebLogic 11". DB de negocio = `CLIENTES-DB2` (`.51`); el dominio usa además `.32` y `.24` según el rol. **Dos rutas de entrada vivas en simultáneo** (dedicada + compartida con ABB/BOCA), ninguna es legacy. Sin capa web/Docker propia (solo JasperReports). |
| **EBY** | 6/7 | Corre en **dos motores en paralelo y concurrente** (`WebLogic.191` + `OPENWLPROD01` / `10.77.7.201`), no una migración a medio hacer. DB nueva confirmada por `tnsnames.ora`: `OPENDBPROD005` (`10.77.7.15`). |
| **BOCA** | 6/7 | El Forms productivo real corre en `WL12C-Desarrollo` (`192.1.2.54`) **pese al nombre "Desarrollo"**: `cabj.condorwork.com.ar` acumula 3,84M `POST /forms/lservlet` con tráfico vivo. Sin capa Docker. Pendiente: `sqlplus` a `CLIENTES-DB` para cerrar el SID. |
| **ROMAN (CSM)** | 4/6/7 a nivel config | WL `12.2.1.4.0` en `OPENWLPROD01` (compartido con EBY/GIAR, sin managed server propio); DB `OPENDBPROD03` (`10.77.7.30:1525`). **Configurado como producción pero sin tráfico Forms en vivo observado** — posible entorno dormido. |
| **Rex Argentina** | WL+DB en vivo (1ª vez) | Motor `OL8LABWL01`, DB `OPENDBPROD001` / PDB `PRODREX01`, con usuarios nominales en `v$session`. Antes no tenía ningún recurso confirmado. |

**Patrón transversal:** el inventario técnico declaraba "WebLogic 11" para GIAR, JOBS, BOCA y ROMAN; en los cuatro casos la versión real es **12.2.1.4.0**. La documentación interna no sigue el ritmo de la realidad — cada dato hay que verificarlo contra el sistema.

**Estado de la hoja "Discrepancias" de la matriz:** resueltas ABB (DB `192.1.1.31`), CEFAS (SID `CEFAS`), JOBS (WL 12.2.1.4), EBY (dos motores, no uno); ROMAN resuelta a medias (versión sí, "test vs. producción" no). Pendientes: SID de BOCA y charset de Enerflex.

## Riesgos y puntos frágiles

- **No existe estrategia de Disaster Recovery** ni gestión formal de backups (rotación, restauración, pruebas). Confirmado por el equipo saliente. Hay que redactarla — con matriz RACI — una vez mapeada toda la infraestructura.
- **Capacidad física de los servidores**: algunos están sobrecargados porque otros no soportan el SO adecuado. Pendiente comparar, servidor por servidor, capacidad física contra licencias Oracle/WebLogic entregadas.
- **Exposición a Internet**: la consola de administración de vCenter (`192.1.1.29:443`) y el panel de `FWOPEN` están publicados por NAT en el firewall de borde; varios puertos Forms de clientes se exponen directo sin pasar por NPM; los dominios `*.condor.solutions` son enumerables y ya reciben escaneo automatizado.
- **Dependencia de personas clave**: el conocimiento de configuración de clientes está concentrado en el Especialista Oracle.
- **VMs multi-cliente**: cualquier cambio sobre `WebLogic.191` (8 clientes), `WL12C-Desarrollo` o `OPENWLPROD01` (3 clientes) tiene radio de impacto multi-cliente.
- **Doble plano app↔datos por Internet**: el circuito cloud→ORDS depende de endpoints publicados a Internet con Let's Encrypt, no de la VPN S2S.

## Preguntas abiertas para el equipo saliente

- Si no hay "VM Core", ¿qué resuelve hoy el login de ProvIA? ¿`aks-provia-prod01` se apagó a propósito?
- Base Core: ¿Oracle o PostgreSQL? Expone ORDS (Oracle) pero existen instancias `psql-core-*`.
- Estado real de **ABB y GIAR**: ¿baja formal o "mantenimiento"? ¿Se retienen las bases solo como backup?
- ¿Existe cuenta AWS? ¿Qué corre en `34.198.2.32` / `34.202.29.65`?
- Listado del método de conexión de cada cliente (VPN / punto a punto / whitelist).
- ¿Dónde se almacenan las ISO de Oracle Linux? ¿Cómo se gestionan las licencias de Oracle y WebLogic?
- Acceso a Azure DevOps (`OpenArg`) y credencial de lectura a `psql-core-*` para cerrar el relevamiento cloud.
- ¿Tenemos acceso al código fuente de la aplicación principal y a los archivos de configuración de alta de un cliente (docker-compose, `.env`, templates)?
