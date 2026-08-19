## VM-DOCKER-clientes

soportesmart@vm-docker:~$ sudo docker ps
CONTAINER ID   IMAGE                                                                   COMMAND                  CREATED       STATUS                 PORTS                                            NAMES
fb2c720183f5   registry.gitlab.com/opentecnologia/self-service-backend:cefas-sfd       "java -jar SelfServi…"   4 years ago   Up 4 years             0.0.0.0:9001->9001/tcp                           ss_back_cefas
aaa82a1152b1   jc21/nginx-proxy-manager:latest                                         "/init"                  5 years ago   Up 4 years (healthy)   0.0.0.0:80-81->80-81/tcp, 0.0.0.0:443->443/tcp   nginx_app_1
3585ab9fa5aa   registry.gitlab.com/opentecnologia/self-service-angular:cefas-sfd       "httpd-foreground"       5 years ago   Up 4 years             0.0.0.0:8881->80/tcp                             ss_front_cefas
2f8d630573cb   jc21/mariadb-aria:latest                                                "/scripts/run.sh"        5 years ago   Up 4 years             3306/tcp                                         nginx_db_1
0b5c66733e91   registry.gitlab.com/opentecnologia/self-service-database:yacyreta-sfd   "docker-entrypoint.s…"   5 years ago   Up 4 years             0.0.0.0:5532->5432/tcp                           ss_pg_cefas

soportesmart@vm-docker:~$ sudo docker exec nginx_app_1 printenv
PATH=/opt/certbot/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=aaa82a1152b1
DB_MYSQL_HOST=db
DB_MYSQL_PORT=3306
DB_MYSQL_USER=npm
DB_MYSQL_PASSWORD=npm
DB_MYSQL_NAME=npm
SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
OPENRESTY_VERSION=1.19.3.1
CERT_HOME=/data/acme.sh/
CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
SUPPRESS_NO_CONFIG_WARNING=1
S6_FIX_ATTRS_HIDDEN=1
S6_BEHAVIOUR_IF_STAGE2_FAILS=1
NODE_ENV=production
NPM_BUILD_VERSION=2.9.4
NPM_BUILD_COMMIT=4b6b276
NPM_BUILD_DATE=2021-06-21 23:51:50 UTC
HOME=/root

soportesmart@vm-docker:~$ sudo docker exec nginx_db_1 printenv
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=2f8d630573cb
MYSQL_ROOT_PASSWORD=npm
MYSQL_DATABASE=npm
MYSQL_USER=npm
MYSQL_PASSWORD=npm
HOME=/root

soportesmart@vm-docker:~$ sudo docker exec -it nginx_db_1 mysql -h 127.0.0.1 -u npm -pnpm npm -e "SELECT id, domain_names, forward_scheme, forward_host, forward_port, enabled, certificate_id, created_on FROM proxy_host;
"
+----+--------------------------------------+----------------+--------------+--------------+---------+----------------+---------------------+
| id | domain_names                         | forward_scheme | forward_host | forward_port | enabled | certificate_id | created_on          |
+----+--------------------------------------+----------------+--------------+--------------+---------+----------------+---------------------+
|  1 | ["cefas.condorlink.com.ar"]          | http           | 192.1.1.38   |         8881 |       1 |              2 | 2021-06-30 00:55:05 |
|  2 | ["cefasbk.condorlink.com.ar"]        | http           | 192.1.1.38   |         9001 |       1 |              3 | 2021-06-30 00:59:25 |
|  3 | ["cefas.opensol.com.ar"]             | http           | 192.1.1.191  |         8888 |       1 |             13 | 2021-06-30 01:45:38 |
|  4 | ["roman.condorwork.com.ar"]          | http           | 172.18.5.40  |           80 |       0 |              5 | 2022-01-20 12:45:27 |
|  5 | ["argocean.condorenterprise.com.ar"] | http           | 172.18.5.40  |           80 |       0 |              6 | 2022-01-20 13:49:27 |
|  6 | ["roman.condorenterprise.com.ar"]    | http           | 172.18.5.40  |           80 |       0 |              7 | 2022-01-20 13:50:42 |
|  7 | ["cefas.condorwork.com.ar"]          | http           | 192.1.1.191  |           80 |       1 |             14 | 2023-02-28 20:48:30 |
|  8 | ["cefasjasper.condorwork.com.ar"]    | http           | 192.1.1.110  |         8095 |       1 |             15 | 2023-12-29 15:25:40 |
|  9 | ["cloud.opensolutions.com.ar"]       | http           | 192.1.1.33   |           80 |       1 |              0 | 2024-03-07 21:24:51 |
+----+--------------------------------------+----------------+--------------+--------------+---------+----------------+---------------------+