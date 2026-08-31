FROM ubuntu:22.04 AS build
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev make && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY src/chall.c src/Makefile ./
RUN make

FROM ubuntu:22.04
RUN apt-get update && \
    apt-get install -y --no-install-recommends socat && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m ctf
WORKDIR /home/ctf

COPY --from=build /build/orwjail /home/ctf/orwjail
COPY flag.txt /home/ctf/flag.txt

RUN mv /home/ctf/flag.txt "/home/ctf/flag_$(tr -dc a-f0-9 < /dev/urandom | head -c 16).txt" && \
    chown -R root:root /home/ctf && \
    chmod 755 /home/ctf && \
    chmod 555 /home/ctf/orwjail && \
    chmod 444 /home/ctf/flag_*.txt

USER ctf
EXPOSE 1337

CMD ["socat", "-T", "30", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:/home/ctf/orwjail,stderr"]
