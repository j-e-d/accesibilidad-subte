import csv
import operator
from copy import deepcopy
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlite_utils import Database
import requests


result = requests.get(
    "https://aplicacioneswp.metrovias.com.ar/APIAccesibilidad/Accesibilidad.svc/GetLineas"
)
json_data = result.json()

results = list()
results_no_date = list()
for line in json_data:
    data_dict = {
        "idLinea": line["idLinea"],
        "nombreLinea": line["nombre"].strip(),
        "fueraDeHorario": line["fueraDeHorario"],
    }
    for station in line["estaciones"]:
        station_dict = data_dict | {
            "idEstacion": station["idEstacion"],
            "nombreEstacion": station["nombre"].strip(),
        }
        for access in station["accesos"]:
            fecha_actualizacion_str = (
                access["fechaActualizacion"].split("-")[0].split("(")[1][:-3]
            )
            fecha_actualizacion_ts = (
                datetime.fromtimestamp(int(fecha_actualizacion_str))
                .astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
                .isoformat()
            )

            fecha_normalizacion_ts = None
            if access["fechaNormalizacion"] != "/Date(-62135586000000-0300)/":
                fecha_normalizacion_str = (
                    access["fechaNormalizacion"].split("-")[0].split("(")[1][:-3]
                )
                fecha_normalizacion_ts = (
                    datetime.fromtimestamp(int(fecha_normalizacion_ts))
                    .astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
                    .isoformat()
                )

            access_dict = station_dict | {
                "cabecera": access["cabecera"],
                "descripcion": access["descripcion"].strip(),
                "fechaActualizacion": fecha_actualizacion_ts,
                "fechaNormalizacion": fecha_normalizacion_ts,
                "funcionando": access["funcionando"],
                "nombre": access["nombre"].strip(),
                "sentido": access["sentido"],
                "tipo": access["tipo"],
            }
            results.append(access_dict)
            access_dict_no_dates = deepcopy(access_dict)
            access_dict_no_dates.pop("fechaActualizacion")
            access_dict_no_dates.pop("fechaNormalizacion")
            results_no_date.append(access_dict_no_dates)


results.sort(key=operator.itemgetter("nombre"))
results.sort(key=operator.itemgetter("idEstacion"))
results.sort(key=operator.itemgetter("idLinea"))
with open("data-completo.csv", "w", encoding="utf8", newline="") as output_file:
    fc = csv.DictWriter(
        output_file,
        fieldnames=results[0].keys(),
    )
    fc.writeheader()
    fc.writerows(results)

results_no_date.sort(key=operator.itemgetter("nombre"))
results_no_date.sort(key=operator.itemgetter("idEstacion"))
results_no_date.sort(key=operator.itemgetter("idLinea"))
with open("data-sin-fechas.csv", "w", encoding="utf8", newline="") as output_file:
    fc = csv.DictWriter(
        output_file,
        fieldnames=results_no_date[0].keys(),
    )
    fc.writeheader()
    fc.writerows(results_no_date)


db = Database("accesibilidad.sqlite")

commit_datetime = datetime.now(timezone.utc).isoformat()
for result in results:
    result["commit-datetime"] = commit_datetime
    last_state = next(iter(db["status"].rows_where(
            "idEstacion = :idEstacion AND nombre = :nombre ORDER BY `commit-datetime` DESC LIMIT 1",
            {"idEstacion": result["idEstacion"], "nombre": result["nombre"]},
        )), None)
    if last_state is None:
        continue
    if result["commit-datetime"] > last_state["commit-datetime"]:
        if result["funcionando"] != last_state["funcionando"]:
            db["status"].insert(result)