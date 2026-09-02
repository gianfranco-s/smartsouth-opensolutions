# Plan de relevamiento — infraestructura Azure

**Objetivo:** mapear capa por capa la infraestructura cloud de Open Solutions en Azure — el plano donde corren los portales Angular de CONDOR (Work / Enterprise / ProvIA) — con el mismo criterio punta a punta que los `plan_relevamiento_alta_*.md` del lado on-premise: identidad del recurso → red → cómputo → datos → identidad/acceso → CI/CD, distinguiendo siempre **lo confirmado contra el portal** de **lo que solo dicen los documentos internos**.

**Contexto / reapertura de alcance.** La investigación de cloud se había estacionado en [`cloud-infra/`](cloud-infra/README.md) para priorizar on-premise. Este plan la reabre. Todo lo que ya teníamos está en `cloud-infra/` (`inventory-cloud.json`, `findings-cloud.md`, `questions-cloud.md`, `topology-cloud.md`, `source/`) y resumido en la tabla de abajo. **Nada de eso está verificado contra Azure** — sale de tres documentos del equipo saliente (`cloud-infra/source/`), a tomar con las mismas pinzas que el resto del material de Relevamiento.

**La seguridad no es foco de esta pasada.** Los hallazgos de postura (red plana, sin NSGs, etc.) ya están anotados en `cloud-infra/findings-cloud.md`; se escalan por separado. Acá lo que interesa es *qué hay y cómo se conecta*.

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
| 0 | **Acceso** | ❌ Abierto — bloqueante | Conseguir: (a) cuenta en el portal/CLI de Azure con al menos `Reader` en las 3 suscripciones; (b) acceso a la organización de Azure DevOps; (c) forma de entrar a la VM Core `10.66.66.33` (SSH/RDP/Bastion); (d) credencial de lectura a `psql-core-*` y a la base CORE. Ver `cloud-infra/questions-cloud.md`. |
| 1 | **Tenant / suscripciones / facturación** | ❌ | `az account list -o table`; `az account tenant list`. Owner de cada suscripción, tipo de contrato (EA / pago por tarjeta), quién paga. Confirmar que `Azure Subscription 1` está vacía (`az resource list --subscription "Azure Subscription 1"`). |
| 2 | **VM Core `10.66.66.33`** — máxima prioridad | ❌ | `az vm list -d -o table` / `az resource list --query "[?contains(name,'core')]"` → nombre de recurso, RG, suscripción, tamaño, zona, si tiene availability set / zonas. ¿HA o SPOF? En qué VNet/subred vive (la IP `10.66.66.0/24` no es ninguna de las conocidas — ¿VNet nueva? ¿peering? ¿`Azure Subscription 1`?). Adentro: `systemctl` / `docker ps` para ver ORDS + APEX + Oracle/же; `SELECT name FROM v$database` o `\l` en PG. **Leer `CONDOR.CORE_BASES`** (`numcli`, `organizacion`, `ords_url`, `estado`) — es la lista real de clientes que pasan por Azure (bloque 8). |
| 3 | **AKS (prod + devtest)** | ❌ | `az aks list -o table`; `az aks get-credentials` para cada uno. `kubectl get ns`, `kubectl get deploy,sts,svc,ingress -A`, `kubectl get pods -A -o wide`. Mapear: namespaces por producto/entorno (`work-prod`, `enterprise-prod`, `provia-prod`, `dev-*`, `test-*`), imágenes en uso (`kubectl get pods -A -o jsonpath` sobre `.spec.containers[*].image`), réplicas, Ingress hosts (Nginx Ingress + cert-manager), y a qué apuntan los backends (`Core:BaseUrl`, `Core:OrdsByOrganizationPath` en configmaps/secrets). Versión de Kubernetes y de los node pools. |
| 4 | **Red** | ❌ | `az network vnet list -o table` + `az network vnet subnet list` por VNet. `az network vnet peering list` (¿hay peering hacia la red de la VM Core?). `az network vnet-gateway list` + `az network vpn-connection list` — estado real de los dos túneles S2S, SAs, selectors. `az network nat gateway list`, `az network public-ip list -o table` — reconciliar con las IPs del doc. Route tables (`az network route-table list`) — confirmar la ruta `10.77.0.0/16 → gateway` de devtest y si prod tiene equivalente. **Resolver `10.66.66.0/24`.** |
| 5 | **Datos** | ❌ | `az postgres flexible-server list -o table` (o `az postgres server list`) → versión, tier, HA, backups, firewall rules, si tiene Private Endpoint o va por IP pública. Contenido: qué esquemas/bases hay en `psql-core-*` y cómo se relacionan con la "Base Core" de la VM (¿la VM Core es Oracle y PG es solo metadata de plataforma? — contradicción a cerrar). `az acr list -o table` + `az acr repository list` para cada registry (¿`openprodregistry` y `opendevregistry` son dos o el doc está viejo?). `az keyvault list` + `az keyvault secret list` (nombres, no valores). `az storage account list -o table`. Redis: `az redis list`. |
| 6 | **Identidad — Entra ID B2C** | ❌ | Nombre del/los tenant(s) B2C (¿uno o separados dev/test/prod?), user flows / custom policies, application registrations de los frontends/backends (`msal-angular`, `Microsoft.Identity.Web`). Quién lo administra. `az ad` / portal de Entra. Relación `SUBID` (B2C) ↔ `CORE_USUARIOS` en la base Core. |
| 7 | **CI/CD — Azure DevOps** | ❌ | Organización y proyectos. Repos (¿código de Work/Enterprise/ProvIA/Core?). Pipelines: cuáles despliegan a AKS, service connections a ACR/AKS/Azure, variable groups, aprobaciones. Self-hosted vs Microsoft-hosted agents. `az devops` CLI o portal. |
| 8 | **Clientes que pasan por Azure** | 🟡 Lista inicial armada (abajo) | Cruzar la lista contra `CONDOR.CORE_BASES` (bloque 2) y contra los `application` de B2C. Cerrar: qué producto CONDOR usa cada uno, dónde vive su Oracle, y cuáles de los `<cliente>.condor.solutions` son Angular en AKS vs. web on-prem. |
| 9 | **DNS / dominios** | 🟡 | ¿Dónde está la zona `condor.solutions` (Azure DNS? registrador externo?)? `az network dns zone list` / `az network dns record-set list`. Mapear cada `*.condor.solutions` a su Ingress de AKS o a su destino on-prem. `proviadev01.condor.com.ar` → `172.171.154.190` (rango Azure): ¿es una VM aparte de ProvIA dev? Contradice "ProvIA solo en contenedores". |
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
