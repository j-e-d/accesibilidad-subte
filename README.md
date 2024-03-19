# Accesibilidad Subte

Proyecto para guardar una copia de los datos de Emova sobre accesibilidad de las estaciones.

Cada 30 minutos baja el archivo json que Emova usa para generar la página [Estaciones accesibles en la Red de Subte
](https://emova.com.ar/index.php/accesibilidad/). Los datos se convierten a csv y se agregan a la base de datos en caso de que el estado de un ascensor o escalera mecánica haya cambiado. Se genera un git commit para tener un registro histórico de todos los archivos bajados.

Los primeros datos son de julio de 2022.