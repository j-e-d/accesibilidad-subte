import csv
import io

import git
from sqlite_utils import Database
from tqdm import tqdm


def get_git_files(filename, skip_shas):
    results = list()
    ref = "main"
    repo = git.Repo("../", odbt=git.GitDB)
    commits = reversed(list(repo.iter_commits(ref)))
    for commit in commits:
        if commit.hexsha not in skip_shas:
            for b in commit.tree.blobs:
                if b.name == filename:
                    results.append(
                        (commit.committed_datetime.isoformat(), b.data_stream.read())
                    )
    return results


def csv_read(content):
    decoded = content.decode("utf-8")
    # dialect = csv.Sniffer().sniff(decoded[:1024])
    reader = csv.DictReader(io.StringIO(decoded))  # , dialect=dialect)
    return reader


def store_to_db(db, line):
    status = db["status"]
    status.insert(line)
    return


def get_last_status(db, line):
    return list(
        db["status"].rows_where(
            "idEstacion = :idEstacion AND nombre = :nombre",
            {"idEstacion": line["idEstacion"], "nombre": line["nombre"]},
        )
    )[-1]


def check_if_new_line(db, line):
    last = db.execute(
        """
            SELECT `commit-datetime`, `funcionando`
            FROM status 
            WHERE idEstacion = :idEstacion AND nombre = :nombre
            ORDER BY `commit-datetime` DESC
            LIMIT 1
        """,
        {"idEstacion": line["idEstacion"], "nombre": line["nombre"]},
    ).fetchone()
    if not last:
        return True, None
    return line["commit-datetime"] > last[0], last[1]


def create_table(db):
    db["status"].create(
        {
            "id": int,
            "idLinea": int,
            "nombreLinea": str,
            "fueraDeHorario": bool,
            "idEstacion": int,
            "nombreEstacion": str,
            "cabecera": str,
            "descripcion": str,
            "fechaActualizacion": str,
            "fechaNormalizacion": str,
            "funcionando": bool,
            "nombre": str,
            "sentido": int,
            "tipo": int,
            "commit-datetime": str,
        },
        pk="id",
    )


db = Database("accesibilidad.sqlite")
res = get_git_files("data-completo.csv", [])
if "status" not in db.table_names():
    create_table(db)

# data-completo start in 10: previous had date in strange format
for r in tqdm(res[10:]):
    a = csv_read(r[1])
    for line in a:
        line["commit-datetime"] = r[0]
        new_line, last_state = check_if_new_line(db, line)
        if new_line:
            if last_state != line["funcionando"]:
                store_to_db(db, line)
