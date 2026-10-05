# Backend structure

The FastAPI entry point is intentionally small. HTTP details, file access, input validation, and model calculations live in separate modules.

```text
backend/
  app.py         create FastAPI app, attach API router, serve built frontend
  api.py         HTTP paths, liveness endpoint, and conversion of data errors to HTTP 422
  config.py      dataset paths and shared CSV projections
  data_io.py     byte reads, hashes, CSV decoding and column projections
  parsers.py     domain validation and normalization for route/telemetry rows
  restoration.py fill blank numeric measurements by distance interpolation
  services.py    use cases: route, telemetry, dataset comparison and analysis
  analysis.py    terrain experiment, fuel model and speed recommendation algorithms
  errors.py      application-level input/data error
```

## Request flow

`api.py` delegates to `services.py`. Services load the configured full/missing/restored datasets through `data_io.py`, fill any blank numeric measurements in the restored dataset through `restoration.py`, use `parsers.py` to build domain points, and return plain response dictionaries. Analysis is cached by the projected CSV bytes, so edits to the restored dataset invalidate the cached result naturally. The route and telemetry endpoints preserve their existing response shapes.

The API router exposes `GET /api/health` for server liveness, `GET /api/status` for dataset availability, and the route, telemetry, analysis, and dataset comparison endpoints.

Keep FastAPI request/response handling in `api.py`, filesystem and CSV mechanics in `data_io.py`, validation in `parsers.py`, and cross-file/model orchestration in `services.py`. Put mathematical model changes in `analysis.py`.
