# Transición de infraestructura de opensolutions

Esto no es un proyecto de software. Es un directorio de trabajo para mapear la infraestructura de un cliente nuevo (Open Solutions / el ecosistema de productos CONDOR) que estamos tomando con muy poco conocimiento previo. No hay acceso programático a los hosts on-premise — toda la investigación se hace a mano por TeamViewer. Azure es un plano aparte, gestionado en la nube (ver más abajo). Este repo existe para construir y mantener una imagen precisa de lo que realmente hay, de forma iterativa, a lo largo de muchas sesiones.

## Fuentes de datos — saber cuál es cuál, y tomar el material de investigación con pinzas

Todo el material fuente vive en `source-files/`. Dos niveles de confianza:

- **`source-files/ExportList.csv`** — un export crudo de vCenter (VMware vSphere). Lo más cercano a la verdad absoluta que tenemos del lado on-premise: cada VM que existe, estado de encendido, host ESXi, disco, SO invitado según lo reporta VMware tools, y direcciones IP. Solo sabe lo que el hipervisor sabe — nada sobre qué corre realmente adentro de una VM.
- **Todo lo demás es documentación interna de trabajo, no verdad verificada** — un CSV armado a mano, emails internos reenviados, y documentos que un equipo interno produjo haciendo el mismo tipo de relevamiento que estamos haciendo ahora. Verificar cada dato contra ExportList.csv (o TeamViewer) antes de actuar en base a él:
  - **`source-files/Relevamiento (sin claves) - VM Linux.csv`** — armado a mano, mapea 13 clientes conocidos solo a sus servidores WebLogic/DB. Sabido incompleto (solo registra un WL+una DB por cliente — ver `infra/findings.md`) y con al menos un dato desactualizado confirmado. El archivo original tenía credenciales de admin en texto plano en una columna; se quitaron antes de versionar este archivo en git.
  - **`source-files/*.eml`** — dos emails internos reenviados (nombres y direcciones reales de empleados de Smart South / Open Solutions en los headers). Uno reporta hallazgos iniciales de Nginx Proxy Manager; el otro entrega un RAR con documentación interna.
  - **`source-files/extracted/`** — extracciones en texto plano/JSON del adjunto RAR (no se puede re-extraer sin una herramienta RAR, así que el contenido útil se sacó una vez y se guardó acá): una **matriz de servicios por cliente** más completa (`matriz_servicios_por_cliente.json` — SIDs, versiones de DB, qué productos Condor usa cada cliente, y la propia hoja **Discrepancias** del equipo fuente, donde dos de sus fuentes de datos internas no coincidían y no se eligió ninguna sobre la otra), un **relevamiento de infraestructura Docker** (`relevamiento_docker.txt` — inventario de contenedores por host, es lo que resolvió la pregunta sobre nginx, ver findings.md), un **análisis de arquitectura Azure** (`analisis_azure.txt` — suscripciones, AKS, VNets, VPN), una especificación de servicio de hosting, y un resumen de producto/negocio del ecosistema CONDOR.
  - La propia matriz documenta bajas de clientes (dos de los 13 clientes originales ya están dados de baja) — tratar cualquier afirmación sobre el estado de un cliente puntual como algo a reconfirmar, no como un hecho vigente.
  - **Nunca volver a agregar credenciales a ningún archivo versionado.** Si material fuente nuevo las incluye, quitarlas antes de commitear, igual que se hizo con el CSV de Relevamiento.

## Qué hay en `infra/`

- **`inventory.json`** — la fuente única de verdad para el lado on-premise, más una sección `azure` aparte para el lado cloud (ver abajo). Las 129 VMs de ExportList.csv, cada una etiquetada con una `category` (la confianza varía — varias ya están **confirmadas** vía el material del RAR, la mayoría siguen siendo conjeturas basadas en el nombre — ver `infra/topology.md` §3 para el detalle) y, para las VMs referenciadas por un cliente, enlaces resueltos de vuelta a `clients[]`. 15 registros de cliente (13 del CSV original + 2 encontrados solo en la matriz más completa: Rex Argentina, Argocean), cada uno con bloques `weblogic`/`database` que muestran lo que se *afirmaba* vs. lo que efectivamente `resolved` contra ExportList.csv (`resolved_by` indica si el match fue por nombre o por IP, `match: false` marca un nombre desactualizado), más un bloque `matrix_detail` para los clientes cubiertos por la matriz más completa. Los hosts Docker llevan un bloque `docker_detail` con el inventario real de servicios por contenedor.
- **`topology.md`** — vistas generadas: un diagrama Mermaid del mapeo cliente → WebLogic → DB (on-premise), un segundo diagrama Mermaid de la topología Azure/AKS (cloud), una tabla de categorías, y notas sobre hosts/clusters ESXi.
- **`findings.md`** — el resultado concreto de cruzar todo: qué está confirmado ahora (identidad de pfsense, ubicación real de nginx, el cliente Argocean), qué se descubrió de nuevo (2 clientes extra, 2 clientes dados de baja, las propias discrepancias sin resolver del equipo fuente), y qué sigue abierto. Leer esto primero si sos nuevo en el proyecto — es la lista priorizada de qué verificar a continuación por TeamViewer o el portal de Azure.

## Dos planos de infraestructura separados — no confundirlos

1. **vSphere on-premise** (ExportList.csv + la mayor parte de `infra/`) — se accede por TeamViewer, sin API.
2. **Azure/AKS** (`inventory.json` → `azure`, `topology.md` §2) — donde realmente corren las capas de aplicación de Condor Work, Enterprise y ProvIA, como contenedores en AKS. Se gestiona desde el portal/CLI de Azure, no por TeamViewer. Conectado al lado on-premise por una única VPN Site-to-Site que termina en `OPENVPNFW01` (pfSense confirmado). Que exista una VM con un nombre como `WL12C-PROD` en ExportList.csv **no** significa que la lógica de aplicación de ese cliente corra ahí — revisar `matrix_detail.productos` y el documento de Azure antes de asumir que todo es on-prem.

## Cómo funciona la categorización (y sus límites)

La `category` de cada VM en inventory.json arrancó como una expresión regular sobre el *nombre* de la VM y el SO invitado autoreportado por vCenter — una hipótesis, no un hecho. Varias categorías ya se actualizaron a confirmadas gracias al material del RAR (contenido de los hosts Docker, un firewall pfsense confirmado por IP del peer de VPN). El resto sigue siendo conjetura pendiente de verificación por TeamViewer. No dejar que una etiqueta de categoría se lea con más certeza de la que tiene; ante la duda, abrir `findings.md`.

## Cómo mantener esto actualizado

Este es un mapa vivo, no un export de una sola vez. A medida que sesiones de TeamViewer/portal de Azure confirmen hechos, o llegue material fuente nuevo:

1. Editar `infra/inventory.json` directamente — pasar una `category` de conjetura a confirmada, completar `used_by_clients`, agregar un campo `notes`, etc.
2. Si el diagrama de mapeo de clientes en `topology.md` §1 cambia (se reasigna el WL/DB de un cliente, se agrega un cliente nuevo), regenerarlo desde el JSON actualizado en vez de editar el Mermaid a mano — recorrer `clients[]`, un nodo por cliente y uno por cada VM resuelta distinta, deduplicar, conectar cliente→WL→DB. Mantenerlo acotado al subconjunto de clientes; un diagrama con las 129 VMs no se puede leer. El diagrama de Azure (§2) se mantiene a mano porque es un conjunto chico y estable de recursos con nombre — editarlo directamente.
3. Si llega un export o documento genuinamente nuevo, volver a correr el cruce de datos (match por nombre, y si no por IP) en vez de mezclar a mano — así fue como se detectaron los datos desactualizados y los matches solo-por-IP hasta ahora. Adjuntos RAR/zip nuevos: extraer con `unar` (instalado vía Homebrew), sacar el texto plano de `.docx`/`.xlsx` (son XML comprimido — no hace falta ninguna dependencia extra, ver el enfoque de extracción ya usado para `source-files/extracted/`), y guardar el texto/JSON extraído en `source-files/extracted/` en vez de dejarlo solo dentro del archivo comprimido.
4. Cuando un hallazgo en `findings.md` se resuelve, moverlo a una sección "Resueltos" con fecha en vez de dejar preguntas viejas mezcladas con las vigentes (ver el archivo actual para el patrón).

## Seguridad

- Nunca commitear credenciales de ningún tipo. Si estás por escribir una contraseña en un archivo versionado, parar y preguntar primero.
- Este es un repo **privado** de GitHub (`git@github.com:gianfranco-s/smartsouth-opensolutions.git`). El material fuente crudo (CSVs, emails, documentos extraídos) se commiteó intencionalmente, bajo la premisa de que el repo se mantiene privado — no hacerlo público, y no copiar este material a otro lado sin el mismo cuidado.
- Nunca hacer push sin que se pida explícitamente, aunque haya un remoto configurado.
