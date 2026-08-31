# [Misc] Script fantasma

## Descripción

`REto.txt` parece un módulo de python autogenerado (señuelo), pero en realidad es un programa Whitespace escondido en los espacios/tabs/saltos.

## Archivos proporcionados

- `REto.txt`

## Análisis

Al abrir el archivo, notamos que solo contiene carácteres de whitespace. Por la descripción del reto nos es fácil intuir que se trata de un archivo en el lenguaje de programación Whitespace.

## Extracción

Al correr el archivo en un interpreter de Whitespace, obtenemos como salida `QUhBVXtsMDVfbDNuZ3U0ajM1XzM1MDczcjFjMDVfNTBuX2wwX200eDFtMH0=`. Al decodificar este string en Base64, obtenemos la flag.

## Flag

`AHAU{l05_l3ngu4j35_35073r1c05_50n_l0_m4x1m0}`
