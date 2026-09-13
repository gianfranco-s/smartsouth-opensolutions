PEDIDO DE ALEXIS (12/13 sep 2026) — capacidad real de cada host ESXi, sospecha de sobreasignación de RAM — **prácticamente resuelto, sin necesitar TeamViewer**

`ExportList-hosts_and_clusters.csv` (export de la vista Hosts and Clusters, con `Consumed Memory %` por host) resolvió lo que pensábamos que iba a necesitar anotación manual host por host: cruzando el % contra el uso real ya conocido se despeja la capacidad física implícita sin entrar a ningún Summary tab. Resultado en `infra/topology.md` §3 y `infra/findings.md`: **7 de 12 hosts del cluster principal (`.215`, `.216`, `.217`, `.218`, `.221`, `.223`, `.224`) ya tienen más RAM asignada a VMs encendidas que su capacidad física implícita** — confirma la sospecha de Alexis como patrón de cluster, no solo en los dos hosts más grandes. `.223` además es el único host con `Status: Warning` en vCenter (no `Normal`).

Único cabo suelto, bajo costo y no urgente: el mismo cálculo para CPU no sirve (`Consumed CPU %` es demasiado volátil, da resultados sin sentido). Si en algún momento hace falta el dato exacto de sockets/cores/GHz por host, ahí sí no hay atajo — TeamViewer, vCenter → Hosts and Clusters → cada host → Summary. También serviría, si la herramienta que generó `ExportList-hosts_and_clusters.csv` lo permite, agregar una columna de capacidad absoluta (no solo %) para reemplazar la aproximación de RAM por un número exacto — pero no bloquea informar el hallazgo tal como está.

---

puede ser que ABB este dado de baja, pero tengamos datos como backup exlusinvamente?

Próximos pasos de GIAR (por orden) — ver plan_relevamiento_alta_giar.md para el detalle completo

0. HECHO (12 sep 2026): dashboard de `FW` (`192.1.3.1`) accedido, NAT completo transcripto (`pfsense-192.1.3.1-nat-rules.txt`, cargado en inventory.json). Confirmado: `200.55.243.117:80/443` -> `10.10.1.50` (`WL-GIAR`) es el backend real de `giarprod.condorenterprise.com.ar`. Capa 3 cerrada.

1. SSH a `WL-GIAR` (10.10.1.50) -- directo primero, si no responde usar la ruta NAT confirmada (puerto 215 en la IP publica de FW):
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@10.10.1.50
# si no responde:
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa -p 215 soportesmart@200.55.243.117
sudo ss -tlnp
ps -ef | grep -iE 'java|weblogic|forms'
Si responde algo vivo -> GIAR legado activo. Si mudo -> dato duro a favor de la baja.

2. Repetir en `DB-GIAR` (`10.10.1.9`) — primero solo para ver si hay una instancia Oracle levantada:
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@10.10.1.9
# o via NAT: -p 212 soportesmart@200.55.243.117
ps -ef | grep pmon
cat /etc/oratab

3. Si `DB-GIAR` esta muda: probar el candidato nuevo `10.1.1.10` (NAT `.117:51521` -> `10.1.1.10:1521`, descripcion "GIAR DB 1521 NUEVO" -- ojo, la subred no coincide con ninguna conocida, podria ser typo por 10.10.1.10).

4. `OPENDBPROD001`/`CDBOPEN03` (ya accesible via `su - oracle`): repetir `v$session` sobre `PRODGIAR` un día hábil, y sobre todo correr `dba_tab_modifications` del schema de aplicación (probablemente `CONDOR`) para un último-DML — el mismo truco que cerró ABB sin depender de pescar una sesión activa en el momento exacto.

5. `DOCKER-DEB` (`192.1.1.37`), ya con acceso de la sesión de ROMAN:
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@192.1.1.37
sudo docker ps
sudo docker exec <NPM> sh -c "find /data/logs -name 'proxy_host-*.log' -exec grep -l giarprod {} \;"
tail -50 <log encontrado>


---

Pendiente de ROMAN (pausado, no se sigue esta sesión — ver infra/findings.md y plan_relevamiento_alta_roman.md):

1. Access log del NPM de DOCKER-DEB para romanprod.condor.solutions — el que dirime si ROMAN está vivo o dormido.

ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@192.1.1.37
sudo docker ps                          # ubicar el contenedor NPM
sudo docker exec <NPM> sh -c "ls -la /data/logs | grep -E 'proxy.host.(93|94)'"
sudo docker exec <NPM> sh -c "tail -50 /data/logs/proxy-host-93_access.log"
Si tiene POST /forms/lservlet 200 reciente → ROMAN vivo, capa 1 cerrada y 4/6 pasan a "1.0". Si está vacío → ROMAN dormido pese a los labels "PRODUCCION" (hallazgo en sí).

2. v$session en OPENDBPROD03 (10.77.7.30:1525, servicio PRODCSM) — cierre definitivo de capa 6. Bloqueado por credencial de DB (la misma que falta para 10.77.7.15 / .22 — está en QUESTIONS.md). Mientras tanto: un netstat -tn en OPENWLPROD01 un día hábil, para ver si aparece tráfico a .30.

3. Capas 3 y 5 (pendientes, bajo costo): revisar vms[FWOPEN].nat_rules por regla dedicada a 10.77.7.201:9001 o 200.55.243.116:2235; y grep -i 'roman\|csm' proxy_hosts.csv + docker ps en OPENDOCKER01 por Jasper/Condor Link de ROMAN.

4. Cabo aparte: clasificar OPENDBDES011 (10.77.7.151, "Roman test" en vCenter), descartado de la ruta productiva, pero sin trazar qué corre ahí (¿romanstest de la matriz? VINST2025 también apunta a esa IP).


DBs que no se pudo acceder
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@10.77.7.30
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@10.77.7.151
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@10.77.7.15


tampoco puedo a .238