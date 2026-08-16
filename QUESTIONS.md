# Preguntas para el equipo saliente

**Solo vamos a tener una o dos reuniones con el equipo saliente (probablemente una sola).** Este archivo tiene que quedar acotado a lo que *solo ellos* pueden responder — decisiones, contactos, accesos, estado de negocio. Todo lo que se pueda verificar entrando a un host por TeamViewer se resuelve nosotros mismos y vive en [PLAN.md](PLAN.md), no acá. Antes de cada reunión, revisar esta lista de arriba hacia abajo: si el tiempo se corta, lo de más abajo queda para la próxima (si la hay).

**Alcance: solo on-premise.** Las preguntas sobre Azure/AWS se estacionaron en [`cloud-infra/questions-cloud.md`](cloud-infra/questions-cloud.md) — la infraestructura cloud quedó fuera del relevamiento actual (ver `cloud-infra/README.md`).

## Prioridad alta — llevar sí o sí

- **¿Cuál es el proceso real para dar de alta a un cliente nuevo?** No encontramos nada que lo documente, y no hay forma de reconstruirlo entrando a un host — es puramente institucional.
- **¿Podemos conseguir cuentas reales (no TeamViewer prestado) para vCenter?** Sin esto, buena parte de lo que sigue en esta lista y en PLAN.md avanza mucho más lento de lo necesario. Pedirlo temprano en la reunión, antes de que se acabe el tiempo.
- **Confirmar el estado de baja de ABB y Arris/GIAR, y si hay un cronograma de retención/eliminación de sus datos.** Es una decisión de negocio, no algo que podamos inferir mirando un servidor.
- **¿Hay un plan de rotación de credenciales como parte de esta transición?** La planilla de Relevamiento tenía una única contraseña de administrador compartida para las bases de datos de los 13 clientes, en texto plano.
- **¿Quién es "Desarrollo" y cómo los contactamos?** Vamos a necesitar ese contacto directo para varios puntos del relevamiento de Docker (despliegues dudosos, instancias posiblemente obsoletas).

## Prioridad media — preguntar si sobra tiempo

- **¿Hay un relevamiento específico de firewalls ya armado?** Uno de los emails (Alexis Lombardi, 22 jul) sugiere que se planeaba uno. Si ya existe, nos ahorra recorrer 8 firewalls candidatos nosotros mismos — vale la pena preguntar antes de invertir ese tiempo, pero no es bloqueante: si no hay respuesta, lo hacemos por TeamViewer igual (ver PLAN.md).
- **¿Se terminó el inventario de ruteo de dominios de Nginx Proxy Manager (dominio → servidor/puerto interno)?** Mismo criterio que arriba: si existe, nos ahorra reconstruirlo; si no hay tiempo de preguntar, lo armamos nosotros.
- **¿Qué es el segundo host ESXi (`192.1.3.252`)** — ¿sitio físico separado, colo, o standalone en el mismo datacenter? Vamos a intentar averiguarlo de forma pasiva primero (ruteo, IPs públicas asociadas); preguntar solo si esa investigación no da una respuesta clara.
- **¿Qué es "Piedras"?** Se nos mencionó verbalmente como un sitio adicional, sin más contexto. El único rastro que tenemos es el nombre de una VM de backup, `VEEAM-PIEDRAS`, que corre dentro del cluster principal (no en `192.1.3.252`). Vamos a revisar primero los destinos de replicación de sus jobs de Veeam por TeamViewer; preguntar solo si esa revisión no aclara nada.

## Resueltas

_(ninguna todavía)_
