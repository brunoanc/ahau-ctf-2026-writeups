# [OSINT] Donde estan?

## Descripción

Hace unos meses fui a una playa con unos amigos, pero los perdí de vista, necesito ayuda para ubicarlos ya que solo me enviaron una foto de referencia diciendo que están yendo hacia ahí. ¿Podrías encontrar su ubicación exacta?

Formato de la flag: `AHAU{playa_municipio_color}`

## Archivos proporcionados

- `WhatsApp_Image_2026-08-29_at_12.35.34_AM.jpeg`

## Análisis

Empecé revisando los metadatos EXIF de la imagen en busca de datos de ubicación, pero WhatsApp los elimina al comprimir la foto.

Como siguiente paso probé con búsqueda inversa de imágenes con Google Lens. Esto devolvió varios candidatos visualmente similares dentro de la costa norte de la península de Yucatán (principalmente Chuburná, Progreso). Probé construir la flag con distintas combinaciones de esos nombres y colores de baliza (rojo, verde) sin éxito.

Como siguiente intento, analicé la imagen y los elementos geográficos visibles en la foto con ayuda de Gemini, pidiéndole que interpretara la orientación y el entorno:

- El sol se oculta hacia la derecha mirando mar adentro, lo que indica una vista hacia el oeste/noroeste.
- En la punta tenemos un espigón de rocas y una baliza marítima al final.
- Una palapa en mal estado del lado izquierdo de la imagen.

Con esas tres pistas, el modelo redujo la búsqueda a unas pocas opciones de la costa norte de Yucatán: Sisal, Dzilam de Bravo, Chelem/Chicxulub/Telchac, San Crisanto y El Cuyo/Las Coloradas. Comparando fotos públicas de cada una contra la forma del terreno, la posición de la baliza y la silueta de la palapa, **Sisal** fue la que mejor coincidía en los tres elementos a la vez.

## Extracción

Con Sisal como candidato principal, faltaba confirmar el municipio y el color exacto de la baliza para armar la flag en el formato `playa_municipio_color`. Sisal pertenece al municipio de **Hunucmá**, y las balizas de la zona suelen ser de color **rojo**. Probé:

```text
AHAU{sisal_hunucma_rojo}
```

y esa fue la flag correcta.

### Notas

- Asumí que "color" se refería al color de la baliza, ya que era el único elemento visualmente llamativo por su color.

## Flag

`AHAU{sisal_hunucma_rojo}`
