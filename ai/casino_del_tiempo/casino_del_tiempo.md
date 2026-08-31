# [AI] Casino del tiempo

## Descripción

En este casino los que predicen el futuro ganan.

`nc 100.53.245.112 5001`

## Análisis

Al conectarnos, el servidor muestra:

```
╔══════════════════════════════════════════╗
║           CASINO AHAU 2077           ║
╚══════════════════════════════════════════╝

Últimos resultados: 35, 10, 23

La casa te dará la flag si predices los próximos 5 números.
Introduce cinco números del 0 al 36, uno por uno.
Número 1/5
>
```

Primero intenté conectarme varias veces, para verificar si aparecían los mismos 3 números iniciales. Así fue, por lo que podemos concluir que los números no dependían de un estado que cambiara en cada conexión, como el tiempo real actual.

Intenté inicialmente poner números aleatorios, como 0, 0, 0, 0, 0. Descubrí que el servidor no valida los números uno por uno al introducirlos, lo hace hasta el final de introducir los cinco. Al fallar, el servidor proporcionaba una pista:

```
La casa gana. Checa el comando /tiempo e inténtalo otra vez.
```

Al volver a conectarme y ejecutar el comando en vez de un número, obtuve:

```
Hora de apertura: 2026-08-27 05:28 UTC
```

La hipótesis entonces es que el generador se inicializó con esa hora de apertura, y ya tenemos los primeros 3 números para verificar si tenemos la seed correcta. La hora `2026-08-27 05:28 UTC` corresponde al timestamp Unix `1787808480`. Probé los 60 timestamps posibles correspondientes a ese minuto:

```python
import random

base = 1787808480

for second in range(60):
    seed = base + second

    random.seed(seed)
    values = [random.randint(0, 36) for _ in range(3)]

    if values == [35, 10, 23]:
        print("Seed:", seed)
```

Con eso, obtenemos la seed original, `1787808536`.

## Extracción

Teniendo la seed, podemos encontrar los siguientes valores:

```python
import random

random.seed(1787808536)

for _ in range(8):
    print(random.randint(0, 36))
```

Esto nos da:

```
35
10
23
33
25
11
23
18
```

Por lo tanto, los siguientes números a introducir en el casino son 33, 25, 11, 23 y 18. Al conectarnos de nuevo e introducir estos números, el servidor regresó la flag.

## Flag

`AHAU{0jal4_Fuer4_c4sin0_R3a1}`
