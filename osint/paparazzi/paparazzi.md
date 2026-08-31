# [OSINT] Paparazzi

## Descripción

_¿Qué voy a hacer? Je ne sais pas_

_¿Qué voy a hacer? Je ne sais plus_

_¿Qué voy a hacer? Je suis perdu_

_¿Qué horas son, mi corazón?_

_Me gusta la moto, me gustas tú_

_Me gusta correr, me gustas tú_

_Me gusta la lluvia, me gustas tú_

Hay un cantante que me gusta mucho, parece que se está moviendo por alguna ciudad, estaría increíble "encontrármelo en la calle" y tomarme una foto con él. La única pista que encontré es que está esperando en la parada de autobús que sale en el vídeo, ¿podrías encontrarla por mí?

Formato: `AHAU{nombre_de_la_calle-ID_parada_bus}`

Ej. `AHAU{santo_ahau_team-111}`

## Archivos proporcionados

- `video.mp4`

## Análisis

En el video se menciona **Sant Cosme** (en L'Hospitalet de Llobregat, área metropolitana de Barcelona), y poco después aparece la parada de bus. Intenté revisar esa escena en cámara lenta y con zoom para leer algún texto, pero no logré encontrar nada legible.

Sin poder leer el texto directamente, recurrí a [Overpass Turbo](https://overpass-turbo.eu/), una herramienta de consulta sobre datos de OpenStreetMap. Centré el mapa en Sant Cosme y usé la siguiente consulta Overpass QL para filtrar únicamente las paradas de autobús dentro de esa área:

```
[out:json][timeout:25];
(
  node["highway"="bus_stop"]({{bbox}});
  node["public_transport"="platform"]({{bbox}});
);
out body;
>;
out skel qt;
```

El barrio es relativamente pequeño, así que el resultado arrojó un número manejable de paradas. Empecé a revisar cada una manualmente; cada nodo traía metadata así:

```
Node 1688383732

Tags:
bench = yes
bus = yes
highway = bus_stop
name = Antoni Martín i Sánchez
name:ca = Antoni Martín i Sánchez
network = AMB Bus Metropolità
operator = Àrea Metropolitana de Barcelona
public_transport = platform
ref = 000821
route_ref = 65 L20 PR2 PR3
shelter = yes
url = https://www.ambmobilitat.cat/Principales/DatosParada.aspx?cerca=1&CodParada=000821

Coordinates: 41.3169535 / 2.0849548 (lat/lon)
```

Con las coordenadas de cada nodo, fui comparando el street view en Google Maps con la imagen del video (más que nada los edificios de fondo), hasta encontrar la parada correcta.

## Extracción

La parada que coincidía visualmente correspondía al mismo nodo de ejemplo anterior: `ref = 000821`, ubicada en **Carrer del Riu Llobregat**. Usando el `ref` (sin ceros a la izquierda) como ID de parada y el nombre de la calle en el formato pedido, armé la flag:

```text
AHAU{carrer_del_riu_llobregat-821}
```

## Flag

`AHAU{carrer_del_riu_llobregat-821}`
