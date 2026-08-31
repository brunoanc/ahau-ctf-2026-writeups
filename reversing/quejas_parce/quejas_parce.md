# [Reversing] Quejas parce

## Descripción

Este tipo de retos normalmente no vienen con flag incluida, eso o al creador se le olvidó meter la buena.

## Archivos proporcionados

- `quejas_parce.exe`

## Análisis

Primero ejecutamos el programa para observar su comportamiento:

```bash
WINEDEBUG=-all wine quejas_parce.exe
```

La salida fue:

```
 20 211 196  67  90 117
 89  76 157 248 183 179
191  38 242 243  61 153
128 169  44   9 147 186
245  86  56  68 208  84
 52  69   1  90 153  13
AHAU{l4_fl4g_no_sale_con_i4_4h97h938d}
Fin del programa.
```

Esta flag, por supuesto, no es la real, así que continuamos con el análisis.

Analizando el ejecutable encontramos que se trata de un PE de 32 bits. Buscando datos interesantes encontramos un bloque de 38 bytes cifrados:

```
e6 84 59 b1 37 fd 55 76 80 7b 6f c8 30 cd 95 f8
20 d1 fb a8 5f e8 37 0b 6f c4 6a a9 c2 b5 8b fe
e2 3b de 19 b0 b4
```

El programa los descifra mediante las siguientes operaciones, comenzando con el estado `0xC0FFEE11`:

```c
state = state * 0x41c64e6d + 0x3039;
plain[i] = cipher[i] ^ ((state >> 16) & 0xff);
```

Reproduciendo este algoritmo obtenemos exactamente la flag falsa del inicio:

```
AHAU{l4_fl4g_no_sale_con_i4_4h97h938d}
```

Siguiendo el flujo vemos que el programa posteriormente trabaja con la sección `hotpath`. Antes de utilizarla cambia sus permisos mediante `VirtualProtect` y descifra su contenido utilizando una clave derivada de `argc`:

```c
key = (argc - 1) ^ 0x67;
```

Al ejecutar el programa sin argumentos tenemos `argc = 1`, por lo que:

```
key = 0x67
```

Al usar esta clave para descifrar `hotpath`, su contenido se convirtió en código x86 válido. Analizando esta nueva rutina encontramos un segundo descifrado, esta vez sobre otro bloque almacenado en `.rdata`. La semilla se construye a partir del resultado de `QueryPerformanceFrequency()`:

```c
QueryPerformanceFrequency(&freq);
state = freq ^ 0xDE584819;
```

Posteriormente utiliza operaciones similares a las de la flag falsa para descifrar cada byte:

```c
for (i = 0; i < 39; i++) {
    state = state * 0x41C64E6D + 0x3039;
    plaintext[i] = encrypted[i] ^ ((state >> 16) & 0xff);
}
```

## Extracción

El bloque cifrado utilizado por `hotpath` contiene los siguientes 39 bytes:

```
06 f9 cf 62 08 ae 7a 81 c5 fa 78 90 77 ca d2 0c
dc 45 f2 6d f5 88 49 9b 96 13 10 85 df 2b f4 09
fc 5a 7f 42 8f ba 81
```

Para reproducir el descifrado necesitamos el valor de `QueryPerformanceFrequency()`. Escribí un programa rápido para probarlo:

```c
#include <windows.h>
#include <stdio.h>

int main(void) {
    LARGE_INTEGER freq;

    QueryPerformanceFrequency(&freq);
    printf("%lld\n", freq.QuadPart);

    return 0;
}
```

Tras compilar y correr:

```bash
i686-w64-mingw32-gcc qpf.c -o qpf.exe
WINEDEBUG=-all wine qpf.exe
```

La salida fue:

```
10000000
```

Teniendo este valor, podemos intentar descifrar los bytes directamente:

```python
freq = 10_000_000
state = freq ^ 0xDE584819

encrypted = bytes.fromhex(
    "06 f9 cf 62 08 ae 7a 81 c5 fa 78 90 77 ca d2 0c "
    "dc 45 f2 6d f5 88 49 9b 96 13 10 85 df 2b f4 09 "
    "fc 5a 7f 42 8f ba 81"
)

plaintext = bytearray()

for byte in encrypted:
    state = (state * 0x41C64E6D + 0x3039) & 0xffffffff
    plaintext.append(byte ^ ((state >> 16) & 0xff))

print(plaintext.decode())
```

Al ejecutar el script, obtenemos la flag correcta.

## Flag

`AHAU{w0w_s1_la_encontr4st3_41414141337}`
