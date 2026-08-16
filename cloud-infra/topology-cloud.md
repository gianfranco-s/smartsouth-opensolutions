# Topología cloud (Azure/AKS) — estacionado

Sacado de `infra/topology.md` cuando se acotó el alcance del relevamiento actual a on-premise. Ver `cloud-infra/README.md`. Basado en `source/analisis_azure.txt`. No es parte del inventario de vSphere — es un plano de gestión completamente distinto (portal/CLI de Azure, no TeamViewer/vCenter). Las capas de aplicación de Condor Work, Enterprise, y ProvIA corren acá como contenedores, no como VMs de vSphere.

```mermaid
flowchart TB
  subgraph OnPrem["Datacenter on-premise"]
    pfsense["OPENVPNFW01 (pfSense)<br/>200.55.243.92"]
  end
  subgraph AzureProd["Azure — Open Prod Subscription / rg-open-prod"]
    aksprod["AKS: aks-open-prod<br/>vnet-open-prod 10.201.0.0/16<br/>(plana, sin NSGs)"]
    natprod["NAT GW: natgw-aks-prod<br/>172.190.147.110"]
    pgprod["psql-core-prod-eus"]
    core["VM Core (ORDS)<br/>10.66.66.33<br/>CORETEST:8090 / COREPROD:8040 / COREDEV:8080"]
  end
  subgraph AzureDev["Azure — Open Operations Subscription / rg-open-devtest"]
    aksdev["AKS: aks-open-devtest<br/>vnet-open-devtest 10.200.0.0/16<br/>(plana, sin NSGs)"]
    natdev["NAT GW: natgw-aks-devtest<br/>13.92.235.102"]
    pgdev["psql-core-nonprod-eus"]
  end
  pfsense <-->|"VPN S2S IPsec<br/>open-pfsense-connection"| aksprod
  pfsense <-->|"VPN S2S IPsec<br/>open-pfsense-connection-devtest<br/>rutea 10.77.0.0/16"| aksdev
  aksprod --> pgprod
  aksdev --> pgdev
  aksprod --> natprod
  aksdev --> natdev
  aksprod -.->|"resuelve org→ORDS"| core
  natprod -.->|"salida a internet"| Internet1(("Internet"))
  natdev -.->|"salida a internet"| Internet2(("Internet"))
```

Los dos túneles VPN terminan en el mismo firewall pfSense, `OPENVPNFW01` — confirmado por coincidencia de IP (`200.55.243.92`), no solo una conjetura por el SO invitado FreeBSD. Ese hallazgo específico (identidad de `OPENVPNFW01`) sigue documentado en `infra/findings.md` porque es sobre una VM on-premise, aunque la evidencia haya salido de un documento de Azure.

El tráfico de la VPN en sí es bajo (mayormente acceso a Oracle DB e integraciones puntuales desde Azure hacia on-premise); la mayor parte de la salida de AKS va directo a internet vía NAT Gateway (llamadas a ORDS/APIs), no por el túnel. El detalle completo — suscripciones, resource groups, IPs públicas, volúmenes de tráfico, la VM Core — está en `inventory-cloud.json` y en `source/analisis_azure.txt`.
