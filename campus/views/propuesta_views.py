import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bs4 import BeautifulSoup
import urllib.parse
import json
import re
from ..utils.helpers import obtener_JSESSIONID, separar_nombre_completo, buscar_persona_por_nombres

class PropuestaCampusView(APIView):
  def get(self, request):
    session = obtener_JSESSIONID();
    url_buscar_propuesta = "https://eros.pucp.edu.pe/pucp/propacad/powbuspa/powbuspa"
    codigo = request.query_params.get('codigo')

    data = {
      "accion": "BuscarPropuestaAcademica",
      "idTipoSistema": "1",
      "comboPrefijo": codigo[0],
      "numeroPropuesta": codigo[1:],
    }
    res = session.post(url_buscar_propuesta, data=data)
    res.raise_for_status()
    html_content = res.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # Buscar el elemento <a> con la clase "pucpEnlace" y el texto correspondiente en el atributo href
    enlace = soup.find('a', class_='pucpEnlace', href=re.compile(r"abrirPropuesta\('\d+'"))

    # Extraer el número usando una expresión regular
    if enlace:
        href = enlace['href']
        match = re.search(r"abrirPropuesta\('(\d+)'", href)
        if match:
            numero = match.group(1)
            print("Número extraído:", numero)
        else:
            print("No se encontró el número.")
    else:
        print("No se encontró el enlace.")

    url_propuesta_estados = "https://eros.pucp.edu.pe/pucp/propacad/powregpa/powregpa"
    params = {
      "accion": "ConsultarHistorialEstadosPropuestaAcademica",
      "idTipoSistema": "1",
      "idTipoFlujoAprob": "3",
      "idPropuesta": numero,
    }

    res = session.get(url_propuesta_estados, params=params)
    print("RESPUESTA", res)
    res.raise_for_status()
    html_content = res.text
    print("HTML", html_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    # Encontrar la tabla que contiene los datos de "Bitácora de estados"
    # Para esto buscamos la tabla con el contenido que necesitamos
    tables = soup.find_all('table', border="0", width="100%")
    print("TABLAS", tables)
    target_table = tables[1]  # Seleccionamos la segunda tabla que corresponde a la "Bitácora de estados"

    # Extraer todas las filas excepto la primera que es la cabecera
    rows = target_table.find_all('tr')
    first_row = rows[0]
    print("FIRST ROW", first_row)
    titles = []
    for title in first_row.find_all('td'):
      title = title.get_text(strip=True)
      titles.append(title)
    rows = rows[1:]

    # Lista para almacenar los datos extraídos
    data = []

    # Recorrer las filas y extraer los datos de cada columna
    for row in rows:
      cols = row.find_all('td')
      row_data = [col.get_text(strip=True) for col in cols if col.get_text(strip=True)]
      # Crear un diccionario usando los headers como claves
      row_dict = dict(zip(titles, row_data))
      # Usar split para separar la fecha de la hora
      print("ROW DICT", row_dict)
      row_dict["Fecha de modificación"] = row_dict["Fecha de modificación"].split()[0]
      data.append(row_dict)

    return Response({"data": data}, status=status.HTTP_200_OK)