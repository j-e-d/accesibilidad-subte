# script to add a column to the sqlite3 db with the 2024 names of the stations
import csv
import sqlite3

from tqdm import tqdm

# open the database
conn = sqlite3.connect("accesibilidad.sqlite")
cursor = conn.cursor()

# open csv file with the 2024 names
with open("./app/2024_names.csv", "r") as f:
    reader = csv.DictReader(f)
    data_dicts = [row for row in reader]

# add new column to the db if it doesn't exist
cursor.execute("PRAGMA table_info(status)")
columns = [column[1] for column in cursor.fetchall()]
if "nombre_2024" not in columns:
    cursor.execute("ALTER TABLE status ADD COLUMN nombre_2024 TEXT")

# copy the names to the new column
query = """
    UPDATE status 
    SET nombre_2024 = nombre
    """
cursor.execute(query)
conn.commit()

# iterate over the lines and add the names to the db
for dict in tqdm(data_dicts, desc="Updating db", smoothing=0.6):
    if dict["nombre"] != dict["oldName"]:
        query = f"""
            UPDATE status 
            SET nombre_2024 = :new_name
            WHERE nombre = :old_name
            AND nombreLinea = :line
            AND nombreEstacion = :station
            """
        cursor.execute(
            query,
            {
                "new_name": dict["nombre"],
                "old_name": dict["oldName"],
                "line": dict["linea"],
                "station": dict["estacion"],
            },
        )
conn.commit()
conn.close()
