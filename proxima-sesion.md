puede ser que ABB este dado de baja, pero tengamos datos como backup exlusinvamente?

Próximos pasos de ROMAN (por orden)
1. Access log del NPM de DOCKER-DEB para romanprod.condor.solutions — el que dirime si ROMAN está vivo o dormido.


ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa soportesmart@192.1.1.37
sudo docker ps                          # ubicar el contenedor NPM
sudo docker exec <NPM> sh -c "ls -la /data/logs | grep -E 'proxy.host.(93|94)'"
sudo docker exec <NPM> sh -c "tail -50 /data/logs/proxy-host-93_access.log"
Si tiene POST /forms/lservlet 200 reciente → ROMAN vivo, capa 1 cerrada y 4/6 pasan a "1.0". Si está vacío → ROMAN dormido pese a los labels "PRODUCCION" (hallazgo en sí).

2. v$session en OPENDBPROD03 (10.77.7.30:1525, servicio PRODCSM) — cierre definitivo de capa 6. Bloqueado por credencial de DB (la misma que falta para 10.77.7.15 / .22 — está en QUESTIONS.md). Mientras tanto: un netstat -tn en OPENWLPROD01 un día hábil, para ver si aparece tráfico a .30.

3. Capas 3 y 5 (pendientes, bajo costo): revisar vms[FWOPEN].nat_rules por regla dedicada a 10.77.7.201:9001 o 200.55.243.116:2235; y grep -i 'roman\|csm' proxy_hosts.csv + docker ps en OPENDOCKER01 por Jasper/Condor Link de ROMAN.

4. Cabo aparte: clasificar OPENDBDES011 (10.77.7.151, "Roman test" en vCenter) — descartado de la ruta productiva, pero sin trazar qué corre ahí (¿romanstest de la matriz? VINST2025 también apunta a esa IP).




DBs que no se pudo acceder
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@10.77.7.30
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@10.77.7.151
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@10.77.7.15
