# Common API

## `GET /`

Returns a simple liveness response for infrastructure checks, local verification, and container health monitoring.

### Request

- Method: `GET`
- Path: `/`
- Authentication: none
- Request body: none

### Response

- Status: `200 OK`
- Content-Type: `application/json`

Schema:

```json
{
  "status": "string"
}
```

Example:

```json
{
  "status": "ok"
}
```
