# Hallazgos cloud (Azure/AWS)

Sacado de `infra/findings.md` cuando se acotó el alcance a on-premise. Ver `cloud-infra/README.md`.

**El 9 sep 2026 se reabrió la investigación cloud** con acceso `Reader` real al portal (identidad `gsalomone_ext@open.com.ar`, rol `Reader` a nivel suscripción en `Open Prod Subscription` y `Open Operations Subscription`). Crudo de la enumeración en `cloud-infra/raw/`. El plan vive en `relevamiento_azure.md`.

---

## Verificado contra el portal — 9 sep 2026

### Acceso / suscripciones (bloque 0-1 del plan — cerrado)

- `Reader` confirmado en **`Open Prod Subscription`** (`c094020b-7309-4dfa-a442-33577527de05`) y **`Open Operations Subscription`** (`f025820f-7b1a-4007-b1fb-ca9bd1cd709d`). Un solo tenant: `16c899e1-4c84-4342-9da7-0c63cd01f536`.
- **`Azure Subscription 1` no es visible** — o no existe o no nos dieron acceso. El doc la daba como "sin uso"; asumir que no está.
- **Azure DevOps confirmado: `https://dev.azure.com/OpenArg/`** (recurso `microsoft.visualstudio/account` "OpenArg" en RG `VisualStudioOnline-…`, sub Operations). Falta acceso a la org en sí (bloque 7 sigue abierto).

### La "VM Core `10.66.66.33`" — NO es una VM standalone

El hallazgo más importante de esta pasada. `10.66.66.0/24` **es la VNet `vnet-provia-prod01`** (región **Brazil South**, RG `rg-provia-prod01`, sub Operations), no una red desconocida:

- Subred `subnet-provia-prod01` = `10.66.66.0/25`; service CIDR de Kubernetes = `10.66.66.128/27`. La IP `.33` cae en el rango de nodos/pods del cluster.
- **No hay ninguna `Microsoft.Compute/virtualMachines` en ninguna de las dos suscripciones** (solo VMSS, que son los node pools de AKS). Cero NICs, cero ipConfigurations en esa subred.
- **El cluster `aks-provia-prod01` está DETENIDO** (`powerState: Stopped`) y su último aprovisionamiento **falló** (`provisioningState: Failed`). Node pool `npproviapr01`, 2× `Standard_DS2_v2`, k8s 1.32.7.
- Tiene un `provia-pfsense-localgw` (local network gateway hacia el pfSense on-prem) pero **no hay virtual network gateway ni connection** en ese RG — la VPN S2S de provia-prod quedó a medio configurar, consistente con el cluster caído.

**Conclusión:** el "Core en `10.66.66.33`" que describen los documentos del equipo saliente, o corría como workload de Kubernetes dentro de `aks-provia-prod01` (y hoy está caído), o siempre fue el `ords-tcore → 192.1.1.80` **on-premise** (mismo esquema de puertos 8090/8050/8040) mal rotulado como "VM de Azure". **No existe una VM SPOF llamada Core en el Azure que vemos.** Pendiente: confirmar con el equipo saliente qué resuelve hoy el login de ProvIA, y si `aks-provia-prod01` se apagó a propósito o se cayó.

### AKS — 5 clusters, solo 2 corriendo

| Cluster | Sub / RG | Región | k8s | Estado | Nodos |
|---|---|---|---|---|---|
| **`aks-open-prod`** | Prod / `rg-open-prod` | East US | 1.33.5 | **Running** | 2× DS2_v2 (`nodepool1`, System) |
| **`aks-open-devtest-v2`** | Ops / `rg-open-devtest` | East US | 1.34.8 | **Running** | 2× DS2_v2 + 2× D2s_v6 (`nodepoolamd` System, `nodepoolv6` User) |
| `aks-open-devtest` | Ops / `rg-open-devtest` | East US | 1.33.5 | Stopped | 3× DS2_v2 — superado por v2 |
| `OpenDevAKS` | Ops / `OpenDevAKSRG` | East US | 1.31.7 | Stopped | 1× DS2_v2 — RG + ACR propios, retirado |
| `aks-provia-prod01` | Ops / `rg-provia-prod01` | Brazil South | 1.32.7 | Stopped / **Failed** | 2× DS2_v2 |

Todos con RBAC habilitado, ninguno private cluster, Azure CNI. **El footprint vivo de AKS es mucho más chico que lo que sugieren los documentos.**

### Red

- **Peerings:** `vnet-provia-prod01` ↔ `vnet-open-prod` y `vnet-provia-prod01` ↔ `vnet-open-devtest` (todos `Connected`). `vnet-open-prod` y `vnet-open-devtest` **no** están peereadas entre sí.
- **VPN S2S a on-prem — ambas `Connected`** (contra el pfSense `OPENVPNFW01`, `200.55.243.92`):
  - `open-pfsense-connection` (prod): IPsec, ingress ~540 MB / egress ~18 MB — coincide con "tráfico casi nulo, mayormente OnPrem→Azure" del doc.
  - `open-pfsense-connection-devtest`: IPsec, ingress ~65 MB / egress ~7 MB.
- **Route tables (revelan qué on-prem toca cada lado):**
  - `rt-aks-prod-cefas` → adosada a `subnet-aks-prod`. **Una sola ruta:** `192.1.1.32/32` (`cefas-oracle`) vía VPN gateway. El prod AKS tiene cableado exactamente un destino on-prem directo: **el Oracle de CEFAS**. El resto de la data va por los ORDS por internet (ver diagrama del plan).
  - `rt-aks-to-pfsense` → adosada a `subnet-aks-devtest`. Ruta `10.77.0.0/16` vía VPN gateway.
  - `rt-aks-to-pfsense-dev` → **sin adosar a ninguna subred hoy**. Lista de prefijos on-prem que devtest debía alcanzar: `10.2.11.0/24`, `10.77.6/7/8/10.0/24`, `192.1.0.0/22`, `192.168.100.0/24` y **`192.168.222.0/24`** — la subred de la DB de Balanz (pregunta abierta #4 del plan). Queda ligada al espacio ruteado on-prem vía el S2S del pfSense; falta saber qué sitio físico es.
- **Sin NSGs** en ninguna subred de ninguna VNet (`networkSecurityGroup: null` en todas). Confirma el hallazgo de seguridad previo — la red sigue plana.
- Subredes nuevas no documentadas: `vnet-open-devtest` tiene `subnet-aks-expansion` (`10.200.4.0/22`, la usa `aks-open-devtest-v2`) además de `subnet-aks-devtest` y `GatewaySubnet`.

### Datos

- **PostgreSQL flexible servers: 3** (el doc conocía 2). `psql-core-prod-eus`, **`psql-core-test-eus`** (nuevo, RG `rg-open-prod`), `psql-core-nonprod-eus` (RG `rg-open-devtest`). Los tres: PG **17**, `Standard_B1ms` Burstable, 32 GB, **HA deshabilitada**, **acceso de red público habilitado** (nota de seguridad). Todos `-eus` pero la región del recurso figura `eastus2`.
- **ACR: son dos de verdad.** `openprodregistry` (`rg-open-prod`) y `opendevregistry` (`OpenDevAKSRG`, del cluster retirado). Ambos SKU Basic, admin user deshabilitado. El doc no estaba viejo.
- **Key Vaults: 6, todos `kv-provia-*`** — `kv-provia-prod` (en `rg-open-prod`), `kv-provia-dev/test/qa/uat/preprod` (en `rg-open-devtest`). Todo el tooling gira alrededor de ProvIA.
- **Storage:** `websiteopen` (RG `Open-Web-Prod`, StorageV2, sitio estático, **HTTPS-only deshabilitado** — nota menor de seguridad) + storages de sistema de los MC_ de AKS.
- **Cognitive Services:** `FacturaAPI` y `FacturasIA`, ambos `FormRecognizer` S0, RG `OpenIA` (sub Operations) — el OCR/IA de facturas.
- **Redis:** no aparece ningún `Microsoft.Cache/redis` en las dos suscripciones. El doc lo nombraba "sin instancia"; sigue sin instancia.

### Identidad — B2C

**4 directorios B2C** (el doc preguntaba "¿uno o varios?" → varios, separados por entorno):

| Tenant | Sub / RG | Región |
|---|---|---|
| `openprod.onmicrosoft.com` | Prod / `rg-open-prod` | United States |
| `openarg.onmicrosoft.com` | Ops / `OpenB2C` | United States |
| `OpenDevB2C.onmicrosoft.com` | Ops / `OpenDevB2C_RG_UK` | Europe |
| `opentestb2c.onmicrosoft.com` | Ops / `OpenTestAKSRG` | United States |

Falta: qué app registrations tiene cada uno y quién los administra (necesita acceso al tenant B2C, no alcanza con `Reader` en la suscripción).

### DNS / dominios (bloque 9)

- **Única zona DNS en Azure: `proviadev01.condor.com.ar`** (RG `MC_OpenDevAKSRG_OpenDevAKS_eastus` — la del cluster retirado). `condor.solutions` y `open.com.ar` se resuelven fuera de Azure (registrador externo — confirmar cuál).
- `proviadev01.condor.com.ar` → PIP `172.171.154.190` = un LoadBalancer de Kubernetes en `OpenDevAKS` (detenido). **No es una VM aparte** — resuelve la contradicción del bloque 9 del plan.

### Resource groups no documentados antes

Sub Prod: `Open-Web-Prod`, `NetworkWatcherRG`, `MC_rg-open-prod_aks-open-prod_eastus`.
Sub Operations: `mcpp-purchase`, `OpenIA`, `OpenB2C`, `OpenDevB2C_RG_UK`, `OpenDevAKSRG`, `OpenTestAKSRG`, `Open-BI-RG`, `rg-provia-prod01`, `VisualStudioOnline-…`, varios `MC_…`.

### Nota de método

Varios `az <grupo> list` a nivel suscripción (sin `-g`) devuelven vacío con este `Reader` (`network nic list`, `network vnet-gateway list`, `network route-table list`, `network local-gateway list`). El workaround que funcionó: `az resource list` para sacar nombre+RG y después `az <grupo> show -g <rg> -n <nombre>`. Tenerlo presente en la próxima pasada.

---

## Abiertos (siguen sin resolver)

- **Bloque 2 — qué resuelve el login de ProvIA hoy.** Ver arriba: no hay VM Core. ¿Workload en `aks-provia-prod01` (caído)? ¿`ords-tcore` on-prem? ¿`aks-open-prod`? Prioridad alta para la reunión.
- **Bloque 2/5 — Base Core: ¿Oracle o PostgreSQL?** Hay 3 `psql-core-*` reales pero los endpoints son ORDS (Oracle). ¿PG es solo metadata de plataforma y el dato del cliente es Oracle on-prem? Falta credencial de lectura a los `psql-core-*` para ver esquemas.
- **`aks-provia-prod01` está Stopped/Failed** — ¿apagado a propósito (costos, migración) o caído? ¿ProvIA prod está degradado?
- **Bloque 3 — adentro de los clusters vivos** (`aks-open-prod`, `aks-open-devtest-v2`): namespaces, deployments, imágenes, ingress hosts, configmaps con `Core:BaseUrl` / `OrdsByOrganizationPath`. **`az aks get-credentials` da `AuthorizationFailed` con el `Reader` actual** (`Microsoft.ContainerService/managedClusters/listClusterUserCredential/action` denegado). Hace falta que agreguen el rol **"Azure Kubernetes Service Cluster User Role"** (+ un RoleBinding de Kubernetes si el cluster usa Azure AD RBAC), o el **"...Cluster Admin Role"**.
- **Bloque 6 — B2C:** app registrations y administradores de los 4 tenants.
- **Bloque 7 — Azure DevOps `OpenArg`:** repos, pipelines, service connections. Falta acceso a la org.
- **`192.168.222.0/24`** (DB de Balanz) — ligada al espacio on-prem ruteado, pero falta el sitio físico.
- **AWS — vacío total.** El email de NPM menciona "instancias con IP pública de AWS" sin un solo dato. `condor.com.ar → 34.198.2.32`, `condorsolutions.com.py → 34.202.29.65` tienen pinta AWS. Preguntar si hay cuenta.
- **Zona `condor.solutions`** — ¿en qué registrador/DNS vive?

---

## VM "Core" en Azure, `10.66.66.33` — histórico (previo al 9 sep 2026)

`arquitectura_configuraciones_instalacion.txt` la describía como "una Virtual Machine de Azure" (no un contenedor en AKS) que resuelve la relación Usuario B2C → organización → endpoint ORDS. Expone tres entornos por puerto: `CORETEST:8090`, `COREPROD:8040`, `COREDEV:8080`. **La verificación del 9 sep 2026 (ver arriba) no encontró ninguna VM standalone; `10.66.66.0/24` es la VNet del cluster `aks-provia-prod01`, hoy detenido.**

## AWS — vacío total

El email de Nginx Proxy Manager menciona de pasada "instancias con direcciones IP públicas pertenecientes a AWS" — pero ningún documento da una IP, nombre de recurso, cuenta o región. Ver `inventory-cloud.json` → `aws_blind_spot`.

## Azure — red sin segmentación interna (hallazgo de seguridad)

Confirmado el 9 sep 2026: ninguna subred de ninguna VNet tiene NSG. Sin Azure Firewall, sin Private Endpoints. Los 3 PostgreSQL tienen acceso de red público habilitado. `websiteopen` con HTTPS-only deshabilitado. Escalar por separado a quien tenga la postura de seguridad del cliente.

## Nota: pfSense sigue confirmado en infra/findings.md

La identidad de `OPENVPNFW01` como pfSense se confirmó cruzando su IP contra la configuración de VPN de Azure — pero esa VM es on-premise, así que ese hallazgo puntual se mantiene en `infra/findings.md`, no acá.
