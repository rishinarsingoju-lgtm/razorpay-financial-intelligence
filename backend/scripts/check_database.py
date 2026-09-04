from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.check import check_database_connection


def main() -> int:
    check_database_connection()
    print("PostgreSQL connection OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
