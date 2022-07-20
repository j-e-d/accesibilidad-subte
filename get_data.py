import csv
import operator

import requests


result = requests.get(
    "https://aplicacioneswp.metrovias.com.ar/APIAccesibilidad/Accesibilidad.svc/GetLineas"
)
json_data = result.json()

results = list()
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
            access_dict = station_dict | {
                "cabecera": access["cabecera"],
                "descripcion": access["descripcion"].strip(),
                'fechaActualizacion': access['fechaActualizacion'],
                "fechaNormalizacion": access["fechaNormalizacion"],
                "funcionando": access["funcionando"],
                "nombre": access["nombre"].strip(),
                "sentido": access["sentido"],
                "tipo": access["tipo"],
            }
            results.append(access_dict)


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

results.pop('fechaActualizacion')
results.pop('fechaNormalizacion')
with open("data-sin-fechas.csv", "w", encoding="utf8", newline="") as output_file:
    fc = csv.DictWriter(
        output_file,
        fieldnames=results[0].keys(),
    )
    fc.writeheader()
    fc.writerows(results)
