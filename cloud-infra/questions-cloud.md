# Preguntas cloud (Azure/AWS) — estacionado

Sacado de `QUESTIONS.md` cuando se acotó el alcance del relevamiento actual a on-premise. Ver `cloud-infra/README.md`. Si se retoma el trabajo sobre cloud, estas son las preguntas que ya teníamos preparadas para el equipo saliente:

- **Encontramos una VM de Azure en `10.66.66.33` que no estaba en ningún inventario nuestro (ni vSphere ni Azure/AKS) — expone ORDS en `CORETEST:8090`, `COREPROD:8040`, `COREDEV:8080` y parece resolver el login de Work/Enterprise/ProvIA para todos los clientes.** ¿Qué es exactamente (nombre del recurso en Azure), tiene alta disponibilidad o es un punto único de falla, y cómo accedemos?
- **¿Existe infraestructura real en AWS?** Un email menciona de pasada "instancias con IP pública pertenecientes a AWS" pero no da ningún dato (ni una IP, ni un nombre de recurso, ni cuenta). Si existe, ¿qué corre ahí y cómo accedemos?
- **Las redes de producción y dev/test de Azure no tienen NSGs y usan una única subred plana** — ¿es un riesgo ya conocido y aceptado, o vale la pena reportarlo como hallazgo nuevo?
- (También seguía pendiente, del acceso en general) **¿podemos conseguir cuentas reales para el portal/CLI de Azure?** — la parte de vCenter de esta pregunta se mantuvo en `QUESTIONS.md` porque sigue siendo necesaria para el trabajo on-premise activo.
