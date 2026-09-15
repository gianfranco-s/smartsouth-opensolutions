# Informe — Capacidad y sobreasignación de RAM en el cluster ESXi

**6 de los 12 hosts del cluster ESXi principal (`192.1.1.214`–`224`) ya tienen más RAM asignada a sus máquinas virtuales encendidas que la RAM física que el host realmente tiene instalada.** El host del sitio Piedras (`192.168.100.4`) se suma en esta versión — hoy no está sobreasignado, pero ver nota abajo.

Se calculó en base a exports de vCenter:
* listado completo por VM: host ESXi, RAM/vCPU **asignada** (columnas `Memory Size`/`CPUs`, configuración), estado ON/OFF, y uso real (`Host CPU`/`Host Mem`). Único export que trae asignación + host + uso real juntos, sin mezclar fechas.
1. listado completo de hosts y clusters host ESXi: **`Memory Size (MB)`, la RAM física real instalada**. También trae `CPUs` (cantidad de sockets físicos) y `Consumed CPU/Memory %`.
1. mismo listado de hosts, para el sitio "Piedras" (`ExportListPiedras-host_and_clusters20260912.csv`) — antes quedaba afuera por no tener este export propio.

## Tabla por host

| Host ESXi | VMs (total/ON) | vCPU asignada (total/ON) | RAM asignada GB (total/ON) | RAM real usada GB (ON) | **RAM física exacta (GB)** | Excedente GB (%) | ¿Sobreasignado? |
|---|---|---|---|---|---|---|---|
| 192.1.1.214 | 5/4 | 30/22 | 86/62 | 49.7 | **120.0** | −58.0 (−48%) | No |
| 192.1.1.215 | 8/8 | 46/46 | 126/126 | 64.2 | **140.0** | −14.0 (−10%) | No |
| **192.1.1.216** | 11/10 | 33/29 | 129/105 | 51.5 | **63.9** | **+41.1 (+64%)** | **Sí** |
| **192.1.1.217** | 7/7 | 56/56 | 110/110 | 71.3 | **95.9** | +14.1 (+15%) | **Sí** |
| **192.1.1.218** | 7/5 | 36/30 | 100/66 | 51.6 | **64.0** | +2.0 (+3%) | **Sí** (al límite) |
| 192.1.1.219 | 7/6 | 32/24 | 58/52 | 45.9 | **72.0** | −20.0 (−28%) | No |
| 192.1.1.220 | 9/6 | 39/32 | 106/70 | 44.1 | **128.0** | −58.0 (−45%) | No |
| **192.1.1.221** | 22/5 | 60/20 | 128/46 | 32.7 | **40.0** | +6.0 (+15%) | **Sí** |
| 192.1.1.222 | 5/3 | 23/13 | 92/36 | 23.4 | **128.0** | −92.0 (−72%) | No *(`HA State: Uninitialization Error`)* |
| **192.1.1.223** | 17/15 | 136/118 | **326/286** | **231.8** | **255.9** | +30.1 (+12%) | **Sí** *(único `Status: Warning`)* |
| **192.1.1.224** | 16/14 | 115/107 | **324/292** | **238.1** | **255.9** | +36.1 (+14%) | **Sí** |
| 192.1.3.252 | 18/11 | 108/60 | 186/110 | 105.7 | **127.3** | −17.3 (−14%) | No |
| 192.168.100.4 (Piedras) | 15/2 | 58/6 | 177/16 | 16.1 | **32.0** | −16.0 (−50%) | No — hoy |

"Excedente" = RAM asignada (ON) − RAM física: positivo (%) es cuánto se pasó de asignar; negativo es margen todavía disponible.*

**Piedras hoy no está sobreasignado** (solo 2 de sus 15 VMs están encendidas), pero tiene sobreasignación latente: las otras 13 VMs, todas apagadas, suman **177 GB asignados en total** contra apenas **32 GB físicos** — si se prendieran todas a la vez, el host no tiene forma de soportarlo (+145 GB, +453% sobre su capacidad). No es urgente porque están apagadas, pero es una alerta a tener en cuenta antes de reactivar cualquiera de ellas. RAM/vCPU asignada de Piedras sigue siendo del export del 18 ago (no hay una versión más nueva de ese export específico); la capacidad física sí es del 12 sep.
