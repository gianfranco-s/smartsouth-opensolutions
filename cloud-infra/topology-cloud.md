# Topología cloud (Azure) y su relación con on-premise

**Verificado contra el portal el 9 sep 2026** (identidad `gsalomone_ext@open.com.ar`, rol `Reader` en `Open Prod Subscription` y `Open Operations Subscription`). Reemplaza el diagrama anterior, que estaba armado solo desde `source/analisis_azure.txt`. Fuente de los datos: `inventory-cloud.json` (`verified_2026_09_09`) y `raw/`. Ver también `findings-cloud.md` §"Verificado contra el portal — 9 sep 2026".

Este es un plano de gestión distinto del de vSphere: se releva por el portal/CLI de Azure, no por TeamViewer/vCenter. Las capas de aplicación de Condor Work / Enterprise / ProvIA corren acá como contenedores en AKS, no como VMs.

---

## 1. Topología Azure — estado real

```mermaid
flowchart TB
  Internet(("Internet"))

  subgraph PROD["Open Prod Subscription — c094020b…"]
    direction TB
    subgraph vnetprod["vnet-open-prod 10.201.0.0/16 (sin NSGs)"]
      aksprod["AKS aks-open-prod — RUNNING<br/>k8s 1.33.5 · 2x DS2_v2 · East US<br/>subnet-aks-prod 10.201.0.0/24"]
      gwprod["open-vpn-gateway<br/>PIP 172.191.115.119"]
    end
    natprod["natgw-aks-prod<br/>172.190.147.110"]
    pgprod["psql-core-prod-eus<br/>psql-core-test-eus<br/>(PG17 · B1ms · HA off · red pública)"]
    acrprod["openprodregistry.azurecr.io"]
    b2cprod["B2C openprod.onmicrosoft.com"]
    kvprod["kv-provia-prod"]
    webprod["storage websiteopen (sitio estático)"]
  end

  subgraph OPS["Open Operations Subscription — f025820f…"]
    direction TB
    subgraph vnetdev["vnet-open-devtest 10.200.0.0/16 (sin NSGs)"]
      aksdev2["AKS aks-open-devtest-v2 — RUNNING<br/>k8s 1.34.8 · 4 nodos · East US<br/>subnet-aks-expansion 10.200.4.0/22"]
      aksdev1["AKS aks-open-devtest — STOPPED<br/>(superado por -v2)<br/>subnet-aks-devtest 10.200.0.0/24"]
      gwdev["open-vpn-gateway-devtest<br/>PIP 20.228.185.188"]
    end
    natdev["natgw-aks-devtest<br/>13.92.235.102"]
    pgdev["psql-core-nonprod-eus"]
    subgraph vnetprovia["vnet-provia-prod01 10.66.66.0/24 · Brazil South"]
      aksprovia["AKS aks-provia-prod01 — STOPPED / provisioning FAILED<br/>k8s 1.32.7 · subnet 10.66.66.0/25 · svc 10.66.66.128/27<br/>== acá ubicaban los docs la 'VM Core 10.66.66.33'"]
      gwprovia["provia-pfsense-localgw<br/>(sin VPN gateway ni connection)"]
    end
    subgraph vnetodevaks["OpenDevAKS (retirado) — vnet 10.224.0.0/12"]
      aksold["AKS OpenDevAKS — STOPPED"]
      dnszone["Azure DNS: proviadev01.condor.com.ar<br/>A → 172.171.154.190 (LB de este cluster)"]
      acrdev["opendevregistry.azurecr.io"]
    end
    b2cops["B2C: openarg · OpenDevB2C (Europe) · opentestb2c"]
    ai["FormRecognizer: FacturaAPI · FacturasIA (RG OpenIA)"]
    devops["Azure DevOps: dev.azure.com/OpenArg"]
  end

  aksprod --> pgprod
  aksprod --> acrprod
  aksdev2 --> pgdev
  aksprod -->|salida a internet| natprod --> Internet
  aksdev2 -->|salida a internet| natdev --> Internet

  vnetprovia <-.->|peering Connected| vnetprod
  vnetprovia <-.->|peering Connected| vnetdev

  gwprod <-->|"VPN S2S IPsec · Connected<br/>ingress ~540MB / egress ~18MB 30d"| Internet
  gwdev  <-->|"VPN S2S IPsec · Connected<br/>ingress ~65MB / egress ~7MB 30d"| Internet
```

Notas:

- **Solo 2 de 5 clusters AKS corren**: `aks-open-prod` y `aks-open-devtest-v2`. `aks-open-devtest`, `OpenDevAKS` y `aks-provia-prod01` están detenidos (el de ProvIA además con aprovisionamiento fallido).
- `vnet-open-prod` y `vnet-open-devtest` **no** están peereadas entre sí; ambas peerean con `vnet-provia-prod01`.
- Falta ver adentro de los clusters (namespaces, imágenes, ingress) — `az aks get-credentials` da `AuthorizationFailed` con el `Reader` actual.

---

## 2. Cómo se conecta el plano cloud con el on-premise

Hay **dos caminos independientes** entre Azure y el datacenter on-premise, y llevan volúmenes de tráfico muy distintos:

```mermaid
flowchart TB
  user(("Usuario final<br/>del cliente"))

  subgraph AZ["Azure (East US / Brazil South)"]
    direction TB
    b2c["Entra ID B2C<br/>openprod / openarg / …"]
    ng["Frontend Angular<br/>(AKS: aks-open-prod / -devtest-v2)"]
    net[".NET backend<br/>(mismo AKS)"]
    core["'Core' — resuelve organización → URL de ORDS<br/>UBICACIÓN SIN CONFIRMAR:<br/>¿workload en aks-provia-prod01 (hoy caído)?<br/>¿o el ords-tcore on-prem 192.1.1.80?"]
    natgw["NAT Gateway<br/>172.190.147.110 / 13.92.235.102"]
    vpngw["VPN Gateways<br/>open-vpn-gateway(-devtest)"]
  end

  subgraph OP["On-premise — datacenter Open + sitios"]
    direction TB
    edge["OPENVPNFW01 — pfSense borde<br/>200.55.243.92"]
    npm["4 hosts Docker con Nginx Proxy Manager<br/>publican ords-&lt;cliente&gt;.open.com.ar (Let's Encrypt)"]
    ords["ORDS por cliente<br/>(:7005 :7007 :8002 :8080 …)"]
    ora["Oracle del cliente<br/>(192.1.x / 10.77.x / 192.168.222.x)"]
    cefasora["Oracle CEFAS 192.1.1.32"]
  end

  user -->|HTTPS| ng
  ng -->|"login OAuth2/OIDC"| b2c
  ng -->|HTTPS| net

  net -->|"1 · ¿qué ORDS para esta organización?"| core

  net -->|"2 · CAMINO PRINCIPAL app→datos<br/>HTTPS por INTERNET · apikey + producto"| natgw
  natgw --> Internet(("Internet"))
  Internet -->|"NAT en el borde"| edge
  edge --> npm --> ords -->|"SQL*Net local"| ora

  vpngw <-->|"VPN S2S IPsec (tráfico casi nulo)<br/>SQL*Net directo + integraciones puntuales"| edge
  edge -.->|"prod: única ruta = 192.1.1.32/32<br/>(rt-aks-prod-cefas)"| cefasora
  edge -.->|"devtest: 10.77.0.0/16 + tabla suelta con<br/>192.1.0.0/22 · 192.168.222.0/24 · 10.2.11/24 · 10.77.6/7/8/10"| ora
```

### Camino 1 — ORDS sobre internet (el grueso del tráfico app → datos)

El backend .NET en AKS le pega a `https://ords-<cliente>.open.com.ar/.../ppcdr/` **por internet público**, no por la VPN. Sale por el NAT Gateway de Azure, entra por NAT en el pfSense de borde `OPENVPNFW01`, y el Nginx Proxy Manager on-premise lo enruta al ORDS interno del cliente (`192.1.2.54:7005`, `192.168.222.20:8080`, …), que a su vez habla SQL\*Net local con el Oracle. Autenticación: `apikey` + `producto` en el header, validados en la base del cliente (`condor.valida_servicios_ords`). Detalle y diagrama de secuencia en `relevamiento_azure.md` §"Bloque 8".

### Camino 2 — VPN S2S IPsec (bajo volumen, control / integraciones)

Dos túneles IPsec, ambos `Connected` el 9 sep 2026, terminan en el mismo pfSense de borde `OPENVPNFW01` (`200.55.243.92`):

| Túnel | Suscripción | Tráfico 30d | Qué on-prem alcanza (route tables) |
|---|---|---|---|
| `open-pfsense-connection` | Open Prod | in ~540 MB / out ~18 MB | **Solo `192.1.1.32/32`** = Oracle de CEFAS (`rt-aks-prod-cefas`, adosada a `subnet-aks-prod`) |
| `open-pfsense-connection-devtest` | Open Operations | in ~65 MB / out ~7 MB | `10.77.0.0/16` (`rt-aks-to-pfsense`, adosada). Tabla `rt-aks-to-pfsense-dev` (hoy sin adosar) lista además `10.2.11.0/24`, `10.77.6/7/8/10.0/24`, `192.1.0.0/22`, `192.168.100.0/24`, `192.168.222.0/24` |

`vnet-provia-prod01` tiene un `provia-pfsense-localgw` pero **ningún VPN gateway ni connection** — la VPN de ProvIA prod quedó a medio configurar, coherente con el cluster detenido.

### El punto que une los dos planos: el "Core"

El backend en AKS necesita, para cada organización, saber a qué `ords-<cliente>` pegarle. Esa resolución la hace el "Core". Los documentos del equipo saliente lo ubicaban en una VM de Azure en `10.66.66.33` — **pero esa IP es la VNet del cluster `aks-provia-prod01` (Brazil South), que está detenido, y no hay ninguna VM standalone**. Queda por confirmar si el Core corre (corría) como workload de Kubernetes ahí, o si siempre fue el `ords-tcore → 192.1.1.80` on-premise (mismo esquema de puertos 8090/8050/8040) mal rotulado. Es la pregunta #1 para la reunión con el equipo saliente.

---

## 3. Confirmado vs. inferido en estos diagramas

- **Confirmado (portal, 9 sep 2026):** todos los recursos, estados de encendido, VNets/subredes/peerings, estado `Connected` y volúmenes de los dos túneles VPN, las rutas de las route tables, los 4 tenants B2C, la org de DevOps, la única zona DNS en Azure, la ausencia de NSGs.
- **Confirmado antes (on-premise, `infra/findings.md`):** `OPENVPNFW01` como pfSense de borde y único punto de entrada desde internet; los 4 NPM que publican los `ords-<cliente>`; el circuito NPM → ORDS → Oracle.
- **Inferido / documental, sin verificar en vivo:** el flujo interno navegador → Angular → .NET → Core → ORDS (sale de `source/arquitectura_configuraciones_instalacion.txt`); que el grueso del tráfico app→datos va por internet y no por la VPN (consistente con los volúmenes bajos de los túneles, pero no medido del lado app).
- **Abierto:** ubicación real del "Core"; si `aks-provia-prod01` se detuvo a propósito o se cayó; qué esquemas viven en `psql-core-*` (Oracle vs PostgreSQL); a qué sitio físico corresponde `192.168.222.0/24`.

---

## Cómo regenerar esto

No es generado desde el JSON — se dibuja a mano leyendo `inventory-cloud.json` (`azure.aks_clusters`, `azure.networking`) y `findings-cloud.md`. Al confirmar algo nuevo por el portal (o al conseguir acceso a los clusters / DevOps / B2C), actualizar el diagrama y la tabla §3, y anotar la fuente en el label del enlace, igual que en `infra/topology.md` §4.
