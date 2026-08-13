/**
 * Base da API do `api_service`.
 *
 * Ponto único de verdade: antes cada service repetia a URL literal e elas divergiram —
 * `login`/`register` apontavam para 8001 (a porta que o docker-compose publica) enquanto
 * `offers`/`profile` apontavam para 8008, onde nada escuta.
 *
 * A porta 8001 vem de `docker-compose.yml` (`api: ports: "8001:8000"`). Rodando a API fora
 * do compose (`make api`, uvicorn direto), ela sobe em 8000 — ajuste aqui.
 */
export const API_BASE_URL = 'http://localhost:8001/api/v1';

/** UI do MLflow, embutida no console via iframe. */
export const MLFLOW_URL = 'http://localhost:5000';
