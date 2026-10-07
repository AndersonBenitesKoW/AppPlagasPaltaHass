import json
from pathlib import Path

from plagas.main import create_app

if __name__ == "__main__":
    app = create_app()
    openapi_schema = app.openapi()
    destino = Path(__file__).resolve().parents[3] / "openapi.json"
    destino.write_text(json.dumps(openapi_schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Esquema OpenAPI exportado correctamente en: {destino}")
