# Infraestructura cloud (Azure / AWS) — fuera de alcance por ahora

**Esta carpeta está estacionada, no activa.** El relevamiento actual se enfoca en la infraestructura on-premise (vSphere, TeamViewer). Decidimos no seguir investigando activamente la infraestructura en proveedores cloud por el momento — lo de acá es lo que ya habíamos encontrado antes de acotar el alcance, guardado para no perderlo, no una investigación en curso.

## Qué hay acá

- **`inventory-cloud.json`** — la sección `azure` completa (suscripciones, AKS, VNets, VPN, y la VM "Core" en `10.66.66.33` recién descubierta) más el hallazgo sin detalle de AWS, sacados de `infra/inventory.json`.
- **`topology-cloud.md`** — el diagrama Mermaid de la topología Azure/AKS, sacado de `infra/topology.md`.
- **`findings-cloud.md`** — los hallazgos específicos de cloud: la VM Core, el vacío de AWS, y el hallazgo de seguridad de red de Azure (sin NSGs).
- **`questions-cloud.md`** — las preguntas relacionadas a cloud que habíamos preparado para el equipo saliente, estacionadas acá en vez de en `QUESTIONS.md`.
- **`source/`** — los tres documentos fuente que son puramente sobre cloud (`analisis_azure.txt`, `arquitectura_configuraciones_instalacion.txt`, `especificaciones_hosting_cloud.txt`), movidos desde `source-files/extracted/`.

## Por qué se estacionó esto

Con una reunión (quizás la única) disponible con el equipo saliente, priorizamos terminar de mapear el lado on-premise, que es donde vamos a operar día a día. La VM Core de Azure en particular parece importante (posible punto único de falla para el login de varios clientes) — si en algún momento retomamos esta carpeta, es el primer lugar por donde seguir.

## Si se retoma esto

1. Volver a integrar `inventory-cloud.json` en `infra/inventory.json` (claves `azure` y el ítem AWS de `blind_spots`).
2. Volver a poner el diagrama de `topology-cloud.md` en `infra/topology.md`.
3. Fusionar `findings-cloud.md` y `questions-cloud.md` de vuelta en `infra/findings.md` y `QUESTIONS.md`.
4. Mover los archivos de `source/` de vuelta a `source-files/extracted/`.
