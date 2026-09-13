# Informe — Capacidad y sobreasignación de RAM en el cluster ESXi principal

**Origen:** pedido de Alexis Lombardi (12 sep 2026) — por host ESXi: cantidad de VMs, recursos asignados y recursos reales. Sospecha de fondo: que hay más RAM asignada a las VMs de la que algún host físico realmente tiene.

**Resultado:** confirmado. **7 de los 12 hosts del cluster ESXi principal (`192.1.1.214`–`224`) ya tienen más RAM asignada a sus máquinas virtuales encendidas que la capacidad física que el propio host reporta tener.** No es un caso aislado en uno o dos servidores — es un patrón que atraviesa más de la mitad del cluster.

## Cómo se calculó, sin acceso directo a vCenter

Se cruzaron por nombre de VM tres exports distintos, cada uno con una pieza que los otros no tienen — no hizo falta entrar host por host a mano:

1. **RAM/vCPU asignada por VM, y a qué host ESXi pertenece cada una** (`ExportList-Datacenter-Full.csv` / `ExportList-Piedras-Full.csv`, snapshot del 18 ago 2026): columnas `CPU` (vCPUs configuradas) y `Tamaño de memoria` (RAM configurada) — el dato de "cuánto se le prometió a cada VM", independientemente de cuánto use en un momento dado. Es el único export que trae esto.
2. **Estado (encendida/apagada) y uso real por VM, actualizado** (`ExportList20260912.csv`, 12 sep 2026 23:30): export más liviano, sin host ni columnas de asignación, pero con el dato del día. Las 144 VMs del export de agosto siguen todas presentes por nombre — cero perdidas, permite actualizar el uso real de cada host sin perder el mapeo a su host.
3. **Porcentaje de memoria consumida por host** (`ExportList-hosts_and_clusters.csv`, export de la vista *Hosts and Clusters* de vCenter, 13 sep 2026 00:15 — 45 minutos después del export anterior, misma sesión de trabajo): `Consumed Memory %` — qué porción de la RAM física total de cada host está en uso ahora mismo.

Con (2) y (3), ya alineados a la misma sesión (noche del 12 al 13 de septiembre), se despeja la capacidad física del host sin necesidad de leerla directamente de ningún panel:

```
RAM física implícita del host ≈ RAM real usada (GB, 12 sep) / (Consumed Memory % del 13 sep / 100)
```

Y comparando esa capacidad física contra (1) — la RAM que ya está *prometida* a las VMs encendidas — se responde la pregunta de Alexis directamente.

**Nota sobre 5 VMs que cambiaron de estado entre el 18 ago y el 12 sep:** `OPENDB19DEV01` y `OPENDBPROD011` (host `192.1.1.218`) y `OPENOEM24ai` (`192.1.1.223`) se apagaron, además de `WL-GIAR`/`DB-GIAR` (`192.1.3.252`, stack legado de un cliente sin relación con este análisis). Los conteos de la tabla ya reflejan el estado actualizado, no el de agosto.

## Tabla por host

| Host ESXi | VMs (total / encendidas, 12 sep) | vCPU asignada (total / ON) | RAM asignada GB (total / ON) | RAM real usada GB (ON, 12 sep) | Memoria consumida % (13 sep) | RAM física implícita (GB) | ¿Sobreasignado? |
|---|---|---|---|---|---|---|---|
| 192.1.1.214 | 5 / 4 | 30 / 22 | 86 / 62 | 49.7 | 43% | ~116 | No |
| **192.1.1.215** | 7 / 7 | 40 / 40 | 114 / 114 | 52.1 | 47% | ~111 | **Sí** (al límite) |
| **192.1.1.216** | 11 / 10 | 33 / 29 | 129 / 105 | 51.5 | 81% | ~64 | **Sí** |
| **192.1.1.217** | 7 / 7 | 56 / 56 | 110 / 110 | 71.1 | 74% | ~96 | **Sí** |
| **192.1.1.218** | 7 / 5 | 36 / 30 | 100 / 66 | 51.1 | 84% | ~61 | **Sí** |
| 192.1.1.219 | 7 / 6 | 32 / 24 | 58 / 52 | 45.8 | 67% | ~68 | No |
| 192.1.1.220 | 9 / 6 | 39 / 32 | 106 / 70 | 44.1 | 36% | ~123 | No |
| **192.1.1.221** | 22 / 5 | 60 / 20 | 128 / 46 | 32.7 | 86% | ~38 | **Sí** |
| 192.1.1.222 | 5 / 3 | 23 / 13 | 92 / 36 | 23.4 | 20% | ~117 | No *(ver nota HA abajo)* |
| **192.1.1.223** | 17 / 15 | 134 / 116 | **330 / 290** | **231.7** | 91% | ~255 | **Sí** *(único host en `Status: Warning`)* |
| **192.1.1.224** | 16 / 14 | 115 / 107 | **324 / 292** | **239.5** | 94% | ~255 | **Sí** |
| 192.1.3.252 *(sitio aparte, sin confirmar)* | 16 / 9 | 96 / 48 | 158 / 82 | 77.9 | 85% | ~92 | No *(con `WL-GIAR`/`DB-GIAR` ya apagadas — antes del 12 sep hubiera dado sobreasignado también)* |
| 192.168.100.4 *(Piedras)* | 15 / 2 | 58 / 6 | 177 / 16 | 16.1 | — *(host fuera de este export)* | — | Sin dato |

*"RAM asignada (total)" incluye VMs apagadas — capacidad ya comprometida en configuración, lista para activarse. "RAM asignada (ON)" es la que hoy compite de verdad por RAM física.*

## Hallazgos destacados

- **`192.1.1.223` y `192.1.1.224` son los más críticos**, y ya se veían así en el primer corte: concentran la mayor RAM asignada del cluster (290 GB y 292 GB solo en VMs encendidas) y el uso real más alto (232 GB y 240 GB — 91-94% de su propia capacidad física). `192.1.1.223` es además el **único host que la propia vCenter marca en `Status: Warning`**, no `Normal` como el resto — coincide con ser uno de los hosts más comprometidos de RAM del cluster.
- **El problema no es solo de esos dos hosts.** `192.1.1.215`, `216`, `217`, `218` y `221` completan la lista de 7 hosts con más RAM prometida que física disponible — es un patrón de todo el cluster, consistente con la intuición original de Alexis, no una excepción puntual.
- **`192.1.1.222` tiene un `HA State: Uninitialization Error`** en el export de hosts — anomalía separada de la cuestión de RAM, sin investigar todavía, pero vale la pena marcarla.
- **No fue posible aplicar el mismo método a CPU**, ni con los datos de agosto ni con los de septiembre. El `Consumed CPU %` es una foto de un instante que varía demasiado (a diferencia de la RAM, que es más estable) — cruzarlo con el uso de CPU en MHz da capacidades físicas implícitas sin sentido (de ~4 a ~36 GHz entre hosts del mismo cluster). No es un artefacto de fechas: se repite igual con datos de la misma sesión. Si se necesita el dato de CPU física (sockets/cores/GHz por host), requiere lectura directa del panel Summary de cada host.

## Limitaciones del cálculo

- Es una **aproximación, no una lectura directa de la capacidad física** — ese dato no aparece en ningún export de VMs ni de hosts que tengamos; se infiere combinando dos métricas de fuentes distintas.
- **La RAM/vCPU *asignada* (columnas 1 de la metodología) sigue viniendo del export del 18 de agosto**, porque el export más reciente (`ExportList20260912.csv`) no trae esas columnas, solo estado y uso. No es un problema real en la práctica — la configuración de una VM no cambia con el uso día a día, solo cuando alguien la edita a propósito — pero si se sospecha un cambio de configuración reciente en alguna VM puntual, la forma de descartarlo es pedir un export "Full" nuevo (con columnas `CPU`/`Tamaño de memoria`).
- El uso real y el porcentaje de consumo por host sí están alineados a la misma sesión de trabajo (12 sep 23:30 / 13 sep 00:15), lo que reduce el margen de error respecto de una primera versión de este cálculo que comparaba uso de agosto contra porcentaje de septiembre.

## Recomendación / próximos pasos

1. **Informar el hallazgo tal como está** — el patrón (7/12 hosts, con `.223` además en estado de warning) ya es suficiente para justificar una revisión de capacidad, sin necesitar más relevamiento previo.
2. Si se decide invertir tiempo en precisión adicional: confirmar la capacidad física exacta de CPU por host (sockets/cores/GHz) vía TeamViewer, y verificar que la RAM/vCPU configurada de cada VM no haya cambiado desde agosto (un export "Full" nuevo lo confirma de una).
3. Priorizar `192.1.1.223` y `192.1.1.224` para cualquier acción correctiva (redistribuir VMs, reducir RAM configurada donde esté sobredimensionada, o ampliar RAM física) — son los que ya están operando más cerca del límite real, no solo del asignado.

---
*Fuentes: `source-files/ExportList-Datacenter-Full.csv`, `source-files/ExportList-Piedras-Full.csv`, `source-files/ExportList20260912.csv`, `source-files/ExportList-hosts_and_clusters.csv`. Detalle técnico y metodología completa en [`infra/findings.md`](infra/findings.md) y [`infra/topology.md`](infra/topology.md) §3; datos estructurados en `infra/inventory.json` → `esxi_capacity`.*
