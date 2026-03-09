"""Export FastAPI OpenAPI spec to JSON for frontend codegen."""

import json
from pathlib import Path

from app.main import app

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def main() -> None:
    spec = app.openapi()
    output = FRONTEND_DIR / "openapi.json"
    output.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"OpenAPI spec written to {output}")


if __name__ == "__main__":
    main()
