# Hallazgos cloud (Azure/AWS) — estacionado

Sacado de `infra/findings.md` cuando se acotó el alcance del relevamiento actual a on-premise. Ver `cloud-infra/README.md`.

## VM "Core" en Azure, `10.66.66.33` — sin inventariar

`arquitectura_configuraciones_instalacion.txt` (ver `source/`) la describe como "una Virtual Machine de Azure" (no un contenedor en AKS) que resuelve la relación Usuario B2C → organización → endpoint ORDS — es decir, es el paso central del login para Work, Enterprise y ProvIA. Expone tres entornos por puerto: `CORETEST:8090`, `COREPROD:8040`, `COREDEV:8080`. No está en ExportList.csv (no es una VM de vSphere) ni estaba en la sección `azure` que se había armado — quedó registrada en `inventory-cloud.json` → `azure.core_vm`, pero no tenemos su nombre de recurso en Azure ni sabemos si es de alta disponibilidad. Dado que parece ser un punto único de fallo para el login de varios productos/clientes, si se retoma esta carpeta es el primer punto a seguir.

## AWS — vacío total

El email de Nginx Proxy Manager menciona de pasada "instancias con direcciones IP públicas pertenecientes a AWS" — pero ningún documento da una IP, nombre de recurso, cuenta o región. Es una nube completa de la que no tenemos ni un solo dato identificable. Ver `inventory-cloud.json` → `aws_blind_spot`.

## Azure — red sin segmentación interna (hallazgo de seguridad)

Tanto el entorno de producción como el de dev/test de AKS en Azure usan una única subred plana para tráfico de aplicaciones, VPN, y servicios expuestos a internet — sin NSGs, sin Azure Firewall, sin Private Endpoints. Si se retoma el trabajo sobre Azure, vale la pena reportarlo a quien tenga a cargo la postura de seguridad de este cliente independientemente del resto.

## Nota: pfSense sigue confirmado en infra/findings.md

La identidad de `OPENVPNFW01` como pfSense se confirmó cruzando su IP contra la configuración de VPN de Azure — pero esa VM es on-premise, así que ese hallazgo puntual se mantiene en `infra/findings.md`, no acá. Se menciona solo para que quede claro por qué un documento de Azure aparece citado como fuente en un hallazgo on-premise.
