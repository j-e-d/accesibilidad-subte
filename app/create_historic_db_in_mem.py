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
    # add tqdm to show progress
    print("Getting files from git")
    for commit in tqdm(
        commits, smoothing=0.6, total=len(list(repo.iter_commits(ref))), desc="Getting commits"
    ):
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


def store_to_db(db, line, status_table):
    status = db["status"]
    status.insert(line)

    composed_key = f"{line['idEstacion']}:{line['nombre']}"
    status_table[composed_key] = {
        "commit-datetime": line["commit-datetime"],
        "funcionando": line["funcionando"],
    }
    return status_table


def check_if_new_line_mem(line, status_table: dict):
    composed_key = f"{line['idEstacion']}:{line['nombre']}"
    current_values = status_table.get(composed_key, None)
    if current_values is None:
        return True, None
    return line["commit-datetime"] > current_values["commit-datetime"], current_values[
        "funcionando"
    ]


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


status_table = dict()

db = Database("accesibilidad-mem.sqlite")
res = get_git_files("data-completo.csv", [])
if "status" not in db.table_names():
    print("Creating table")
    create_table(db)

# data-completo start in 10: previous had date in strange format
print("Storing data")
for r in tqdm(res[10:], smoothing=0.6):
    a = csv_read(r[1])
    for line in a:
        line["commit-datetime"] = r[0]
        new_line, last_state = check_if_new_line_mem(line, status_table)
        if new_line:
            if last_state != line["funcionando"]:
                status_table = store_to_db(db, line, status_table)
