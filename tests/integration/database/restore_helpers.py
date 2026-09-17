import os
import subprocess
from pathlib import Path


def restore_dump(
    pg_restore_path: str,
    dump_file: Path,
    database_name: str,
    host: str = "localhost",
    port: str = "5432",
    user: str = "timeline_user",
) -> None:
    """Restore a custom dump when the client is newer than the server."""
    env = os.environ.copy()
    env.setdefault("PGPASSWORD", "timeline_password")
    psql_path = str(Path(pg_restore_path).with_name("psql.exe"))
    sql_file = dump_file.with_suffix(".sql")

    export = subprocess.run(
        [
            pg_restore_path,
            "-f",
            str(sql_file),
            "--clean",
            "--if-exists",
            "--no-owner",
            str(dump_file),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    del export

    sql = sql_file.read_text(encoding="utf-8")
    sql = sql.replace("SET transaction_timeout = 0;\n", "")
    sql_file.write_text(sql, encoding="utf-8")

    subprocess.run(
        [
            psql_path,
            "-X",
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            database_name,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            str(sql_file),
        ],
        env=env,
        check=True,
    )