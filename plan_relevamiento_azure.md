# Plan de relevamiento — infraestructura Azure

**Objetivo:** mapear capa por capa la infraestructura cloud de Open Solutions en Azure — el plano donde corren los portales Angular de CONDOR (Work / Enterprise / ProvIA) — con el mismo criterio punta a punta que los `plan_relevamiento_alta_*.md` del lado on-premise: identidad del recurso → red → cómputo → datos → identidad/acceso → CI/CD, distinguiendo siempre **lo confirmado contra el portal** de **lo que solo dicen los documentos internos**.

**Contexto / reapertura de alcance.** La investigación de cloud se había estacionado en [`cloud-infra/`](cloud-infra/README.md) para priorizar on-premise. Este plan la reabre. Todo lo que ya teníamos está en `cloud-infra/` (`inventory-cloud.json`, `findings-cloud.md`, `questions-cloud.md`, `topology-cloud.md`, `source/`) y resumido en la tabla de abajo. **Nada de eso está verificado contra Azure** — sale de tres documentos del equipo saliente (`cloud-infra/source/`), a tomar con las mismas pinzas que el resto del material de Relevamiento.

**La seguridad no es foco de esta pasada.** Los hallazgos de postura (red plana, sin NSGs, etc.) ya están anotados en `cloud-infra/findings-cloud.md`; se escalan por separado. Acá lo que interesa es *qué hay y cómo se conecta*.

> **Actualización 9 sep 2026 — primera pasada de verificación hecha.** Se consiguió acceso `Reader` real a `Open Prod Subscription` y `Open Operations Subscription` y se corrió toda la enumeración read-only (bloques 1, 3, 4, 5, 6, 9 en buena parte). Resultados verificados en [`cloud-infra/findings-cloud.md`](cloud-infra/findings-cloud.md) §"Verificado contra el portal — 9 sep 2026" y volcados en `cloud-infra/inventory-cloud.json` (`verified_2026_09_09`). Crudo en `cloud-infra/raw/`. **Titular: no existe ninguna "VM Core" standalone — `10.66.66.0/24` es la VNet del cluster `aks-provia-prod01` (Brazil South), hoy detenido y con aprovisionamiento fallido.** La tabla "Estado de partida" de abajo es el punto de partida documental; para el estado real ver findings-cloud.md.

## Estado de partida (1 sep 2026)

De `cloud-infra/inventory-cloud.json` + `cloud-infra/source/analisis_azure.txt` + `arquitectura_configuraciones_instalacion.txt`:

| Item | Lo que sabemos | Confianza |
|---|---|---|
| Suscripciones | `Open Prod Subscription`, `Open Operations Subscription`, `Azure Subscription 1` (sin uso) | Doc |
| Resource groups | `rg-open-prod` (en Open Prod), `rg-open-devtest` (en Open Operations) | Doc |
| AKS prod | `aks-open-prod` en `vnet-open-prod` `10.201.0.0/16` (2 subredes: `GatewaySubnet` /27, `subnet-aks-prod` /24) | Doc |
| AKS dev/test | `aks-open-devtest` en `vnet-open-devtest` `10.200.0.0/16` (misma estructura) | Doc |
| VPN S2S | `open-vpn-gateway` / `open-vpn-gateway-devtest` → peer `200.55.243.92` = pfSense `OPENVPNFW01` on-prem. devtest rutea `10.77.0.0/16` al datacenter. Tráfico casi nulo (~487 MiB/30d prod) | Doc + IP cruzada con `infra/inventory.json` |
| NAT Gateway | `natgw-aks-prod` `172.190.147.110` · `natgw-aks-devtest` `13.92.235.102`. Grueso de la salida de AKS (63 GB / 150 GB por 30d) | Doc |
| IPs públicas | prod: `20.253.49.89` (AKS), `172.191.115.119` (VPN). devtest: `20.228.185.188` (VPN), `172.191.116.4` (AKS) | Doc |
| PostgreSQL | `psql-core-prod-eus` · `psql-core-nonprod-eus` (sufijo `-eus` → East US) | Doc |
| Container Registry | `openprodregistry` **y** `opendevregistry.azurecr.io` — dos nombres, reconciliar | Doc |
| **VM Core** | `10.66.66.33`, VM standalone (no AKS). Resuelve org→ORDS para todo el login. Puertos `CORETEST:8090` / `COREPROD:8040` / `COREDEV:8080`. Sin nombre de recurso, sin HA confirmada. IP fuera de ambas VNets conocidas | Doc — **sin inventariar** |
| Auth ProvIA | Azure Entra ID B2C (OAuth2/OIDC) | Doc |
| Otros servicios nombrados | Key Vault, Azure Monitor + OpenTelemetry, Storage Accounts, Redis, Microsoft Graph, `Azure.AI.FormRecognizer`, Managed Identities | Doc, sin instancia |
| Dominios | `*.condor.solutions` (`work` / `enterprise` / `provia`, con `dev`/`test`), + ORDS `ords-*.open.com.ar` | Doc + NPM on-prem |
| Rastro AWS | `condor.com.ar` → `34.198.2.32`, `condorsolutions.com.py` → `34.202.29.65`. Cero detalle | `infra/findings.md:58` |

## El plan, bloque por bloque

Orden por dependencia: sin el bloque 0 nada de lo demás pasa de "leer documentos".

| # | Bloque | Estado | Próximo paso |
|---|---|---|---|
| 0 | **Acceso** | 🟡 Parcial (9 sep 2026) | ✅ `Reader` en `Open Prod` + `Open Operations`. ❌ Falta: (b) org de Azure DevOps `OpenArg`; (c) forma de entrar a lo que sea que resuelva el login de ProvIA (ya no hay "VM Core" — ver bloque 2); (d) credencial de lectura a `psql-core-*`. RBAC de Kubernetes para `az aks get-credentials` sin probar. |
| 1 | **Tenant / suscripciones / facturación** | 🟡 (9 sep 2026) | ✅ Un tenant (`16c899e1-…`); 2 suscripciones accesibles con sus IDs; `Azure Subscription 1` no visible (asumir inexistente). ❌ Falta owner/contrato/quién paga de cada suscripción. |
| 2 | **"VM Core `10.66.66.33`"** — máxima prioridad | 🟡 Reclasificado (9 sep 2026) | **No existe ninguna VM standalone.** `10.66.66.0/24` = `vnet-provia-prod01` (Brazil South), VNet del cluster `aks-provia-prod01`, **Stopped + provisioning Failed**. El "Core" o corría como workload k8s ahí (caído) o siempre fue el `ords-tcore → 192.1.1.80` on-prem. **Preguntar al equipo saliente:** ¿qué resuelve hoy el login de ProvIA? ¿`aks-provia-prod01` se apagó a propósito? Y leer `CONDOR.CORE_BASES` donde efectivamente viva. |
| 3 | **AKS (prod + devtest)** | 🟡 Inventariado, falta adentro (9 sep 2026) | ✅ 5 clusters, solo 2 Running: `aks-open-prod` (eastus, 1.33.5) y `aks-open-devtest-v2` (eastus, 1.34.8). Detenidos: `aks-open-devtest`, `OpenDevAKS`, `aks-provia-prod01`. ❌ Falta `az aks get-credentials` + `kubectl` sobre los 2 vivos: namespaces, deployments, imágenes, ingress hosts, configmaps con `Core:BaseUrl` / `OrdsByOrganizationPath`. |
| 4 | **Red** | ✅ Mapeada (9 sep 2026) | VNets, subredes, peerings (provia↔prod, provia↔devtest), 2× S2S IPsec `Connected` al pfSense `200.55.243.92`, NAT gateways, route tables. Hallazgos: `rt-aks-prod-cefas` cablea un solo destino on-prem (`192.1.1.32/32` = Oracle de CEFAS); `rt-aks-to-pfsense-dev` (hoy sin adosar) lista `192.168.222.0/24` = subred DB de Balanz. Sin NSGs en ninguna subred. Detalle en findings-cloud.md. |
| 5 | **Datos** | 🟡 Inventariado, falta contenido (9 sep 2026) | ✅ 3× PostgreSQL flexible (`psql-core-prod/test/nonprod-eus`, PG17, B1ms Burstable, HA off, red pública on); 2× ACR (`openprodregistry`, `opendevregistry` — son dos de verdad); 6× Key Vault `kv-provia-*`; storage `websiteopen`; 2× FormRecognizer (`OpenIA`); sin Redis. ❌ Falta credencial para ver esquemas de `psql-core-*` y cerrar Oracle vs PG. |
| 6 | **Identidad — Entra ID B2C** | 🟡 (9 sep 2026) | ✅ 4 directorios: `openprod`, `openarg`, `OpenDevB2C` (Europe), `opentestb2c`. ❌ Falta acceso a los tenants: user flows, app registrations, administradores, relación `SUBID` ↔ `CORE_USUARIOS`. |
| 7 | **CI/CD — Azure DevOps** | 🟡 Org identificada (9 sep 2026) | ✅ Org = `https://dev.azure.com/OpenArg/`. ❌ Falta acceso: repos, pipelines, service connections a ACR/AKS, variable groups, agents. |
| 8 | **Clientes que pasan por Azure** | 🟡 Lista inicial armada (abajo) | Cruzar la lista contra `CONDOR.CORE_BASES` (bloque 2) y contra los `application` de B2C. Cerrar: qué producto CONDOR usa cada uno, dónde vive su Oracle, y cuáles de los `<cliente>.condor.solutions` son Angular en AKS vs. web on-prem. Señal nueva: la ruta `cefas-oracle → 192.1.1.32/32` en `aks-open-prod` confirma a CEFAS como cliente vivo en el prod de Azure. |
| 9 | **DNS / dominios** | 🟡 (9 sep 2026) | ✅ Única zona en Azure DNS: `proviadev01.condor.com.ar` (→ `172.171.154.190`, un LB de k8s en el `OpenDevAKS` retirado — **no es una VM aparte**, contradicción cerrada). `condor.solutions` y `open.com.ar` viven fuera de Azure. ❌ Falta: qué registrador/DNS hostea `condor.solutions` y mapear cada `*.condor.solutions` a su Ingress. |
| 10 | **AWS (rastro)** | ❌ | Fuera del foco Azure pero anotarlo: `34.198.2.32` (`condor.com.ar`), `34.202.29.65` (`condorsolutions.com.py`) tienen pinta AWS. Preguntar al equipo saliente si hay cuenta AWS y qué corre ahí. |

## Bloque 8 — clientes que pasan por Azure (estado 1 sep 2026)

Señal usada: tener un `ords-<cliente>.open.com.ar` publicado (lo que registra `CORE_BASES` y consume el backend de AKS) y/o un entrypoint Angular de generación actual `<cliente>.condor.solutions`. Fuente: NPM de `DOCKER-DEB` (`DOCKER-DEB-NginxProxyManager/proxy_hosts.csv`, `infra/inventory.json` → `vms[DOCKER-DEB].docker_detail.proxy_hosts`).

### Qué es un `ords-<cliente>` y cómo entra en el circuito

**No es una VPN.** Un `ords-<cliente>` es una **API REST sobre la base Oracle de ese cliente** — Oracle REST Data Services (ORDS), un middleware Java que corre en su propio puerto (`:8080`, `:7005`, `:7007`…) **pegado a la base Oracle, on-premise**, y expone paquetes PL/SQL, tablas y APEX como endpoints HTTP bajo el prefijo `.../ppcdr/` (módulos `ppcdr/core`, `ppcdr/erp`, `ppcdr/provia`, `ppcdr/psol`). El NPM lo publica a internet con cert Let's Encrypt en `ords-<cliente>.open.com.ar`; el destino real es siempre una IP interna (`192.1.2.54:7005`, `192.168.222.20:8080`, …).

Hay uno por cliente porque cada cliente tiene su propia base Oracle. `CONDOR.CORE_BASES` (tabla en la VM Core de Azure) mapea `organización / NUMCLI → URL del ORDS`.

**Quién le pega:** el cliente final nunca; es servidor a servidor. Es la única vía por la que los portales Angular de CONDOR (en AKS/Azure) leen y escriben los datos del cliente:

```
navegador del usuario del cliente
      │  HTTPS
      ▼
frontend Angular               ← AKS / Azure
      │  HTTPS
      ▼
backend .NET                   ← AKS / Azure
      │  1) "¿cuál ORDS para esta organización?" → VM Core 10.66.66.33 (Azure)
      │        → devuelve https://ords-<cliente>.open.com.ar/.../ppcdr/
      │  2) HTTPS por internet (endpoint publicado por el NPM), con apikey + producto en el header
      ▼
ords-<cliente>  (ORDS)         ← ON-PREMISE, junto a la base
      │  SQL*Net, local
      ▼
Oracle del cliente             ← ON-PREMISE, misma subred
```

Autenticación: `apikey` + `producto` en el header, validados en cada llamada por un pre-hook en la base del cliente (`condor.valida_servicios_ords`); para el login se hace además un ping de conexión como usuario Oracle real. La VPN S2S Azure↔datacenter es otra cosa — lleva casi nada de tráfico (solo SQL\*Net directo e integraciones puntuales); **el grueso app→datos va por estos ORDS, por internet**.

**Nivel A — `ords-<cliente>` propio publicado (misma señal que Balanz):**

| Cliente | Endpoints ORDS → destino | Alta |
|---|---|---|
| Balanz | `ords-balanz` → `192.168.222.20:8080` · `ords-balanztest` → `192.168.222.19:8080` | 29 dic 2025 / 29 jul 2025 |
| Boca (`BOCA`, NUMCLI 310) | `ords-boca` → `192.1.2.54:7005` | 23 may 2023 |
| CEFAS (`CEFAS`, NUMCLI 108) | `ords-cefast` → `192.1.2.54:7007` https | 29 feb 2024 |
| EBY / Yacyretá (`EBY`) | `ords-eby` → `192.1.2.54:7010` · `ords-ebyqa` → `10.77.7.15:8040` · `ords-yacy` → `10.77.7.15:8080` | 2024–2026 |
| JOBS (`JOBS`) | `ords-jobs` → `192.1.1.1:8002` · `ords-jobst` → `192.1.2.54:7002` · `ords-jobsdev` → `192.1.1.44:8080` | 2024–2025 |
| ROMAN / CSM (`ROMAN`) | `ords-roman2` → `10.77.7.12:8040` | fecha del panel dudosa (2028) |

**Nivel B — entrypoint `<cliente>.condor.solutions` de generación actual, sin `ords-` propio visto** (señal débil: varios apuntan a `:9001` de WebLogic on-prem, no distinguible de Forms clásico):

| Cliente | Dominio → destino |
|---|---|
| Heinlein | `heinleintest.condor.solutions` → `192.1.2.195:9001` |
| ROMAN / CSM | `romanprod` / `romanqa.condor.solutions` → `10.77.7.201:9001` |
| Maipú (DASA) | `qadmportal.condor.solutions` (deshab.) + `dmportal` → `10.77.10.201:8040` |
| "serzarex" (¿Rex Argentina?) | `serzarex.condor.solutions` + `serzarex-test` → `192.1.2.195:9001` |

**Nombrados textualmente en el doc de instalación como altas en `CORE_BASES`:** SMQ (NUMCLI 42), CEFAS (108), Boca (310). SMQ no tiene VM ni dominio mapeado (aparece también en la nota de `VPNCLIENTESRDP`, `infra/findings.md:216`).

**Endpoints ORDS genéricos / de plataforma (no son un cliente):** `ords-open`, `ords-angular`, `ordserp19`, `ordsppc`, `ords-t2022dev01`, y **`ords-tcore` / `-dev` / `-prod` → `192.1.1.80` puertos 8090/8050/8040** — el esquema de puertos calca al de la VM Core de Azure: posible **Core on-premise** (¿test? ¿mirror?), aclararlo.

## Preguntas para el equipo saliente

Ya redactadas en [`cloud-infra/questions-cloud.md`](cloud-infra/questions-cloud.md). Prioridad para la (probable única) reunión:

1. **Acceso** — portal Azure (`Reader` mínimo) + Azure DevOps + forma de entrar a la VM Core. Sin esto el relevamiento no arranca.
2. **VM Core `10.66.66.33`** — nombre del recurso, suscripción/RG, ¿HA o SPOF?, en qué red vive, cómo se accede.
3. **Base Core: ¿Oracle o PostgreSQL?** La VM expone ORDS (Oracle) pero existen `psql-core-*`. ¿Qué corre dónde?
4. **`192.168.222.x`** — subred de la DB de Balanz (`.19`/`.20`), no aparece en ningún documento. ¿Qué sitio/red es?
5. **B2C** — nombre del tenant, cuántos, quién lo administra.
6. **ACR** — ¿`openprodregistry` y `opendevregistry` son dos registries o uno con nombre viejo?
7. **AWS** — ¿existe cuenta? ¿qué corre en `34.198.2.32` / `34.202.29.65`?
8. **Owner / facturación** de las suscripciones.

## Al terminar

1. Volcar todo lo confirmado en `cloud-infra/inventory-cloud.json` (o, si se decide reintegrar de verdad, en `infra/inventory.json` → clave `azure`, siguiendo el checklist de `cloud-infra/README.md` §"Si se retoma esto").
2. Actualizar la tabla "Estado de partida" de este plan con los datos reales del portal (marcar qué se confirmó y qué cambió respecto de los documentos).
3. Regenerar el diagrama de `cloud-infra/topology-cloud.md` con la VNet real de la VM Core, los peerings y los namespaces de AKS.
4. Pasar cada cliente del bloque 8 de "inferido por `ords-`/dominio" a "confirmado en `CORE_BASES`", y anotar producto CONDOR + ubicación de su Oracle. Cruzar con `infra/inventory.json` → `clients[]`.
5. Cerrar en `cloud-infra/findings-cloud.md` (con fecha, sección "Resueltos"): identidad de la VM Core, naturaleza de `192.168.222.x`, `ords-tcore` (¿Core on-prem?), y el rastro AWS.
6. Si se confirma que la investigación cloud queda reabierta de forma permanente, actualizar `README.md`, `PLAN.md` y `QUESTIONS.md` para sacar las notas de "alcance: solo on-premise".
