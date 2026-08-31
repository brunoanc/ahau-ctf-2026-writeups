# [Misc] Ghost in the wire

## Descripción

La bandera va escondida una letra por ping, en la cola del payload ICMP, entre tráfico de ruido (más pings, DNS, HTTP).

## Archivos proporcionados

- `reto.pcap`

## Análisis

Abriendo el archivo pcap en Wireshark y filtrando únicamente el tráfico ICMP, podemos encontrar bastantes paquetes, pero muchos son ruido. Para identificar cuales eran los relevantes los separé por dirección IP de origen y de destino, ICMP identifier, sequence number y el payload. Esto me permitió identificar que aquellas con identifier 0x1337, de 10.13.37.5 a 10.13.37.1, eran las que contenían un byte inusual al final del payload.

## Extracción

Analizando la secuencia correcta, identifiqué que el byte adicional era un carácter ASCII. Al juntar todos en orden, obtenemos la cadena `QUhBVXsxQ01wXzNzXzFuY3IzMWJsZX0=`. Al decodificar el string en Base64, obtenemos la flag.

## Flag

`AHAU{1CMp_3s_1ncr31ble}`
