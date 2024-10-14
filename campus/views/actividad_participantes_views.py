import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse, parse_qs
import json
from ..utils.helpers import obtener_JSESSIONID, quitar_tildes
from urllib.parse import urlparse, parse_qs

class ActividadParticipantesCampusView(APIView):
  def get(self, request):
    nombre = request.query_params.get('nombre_actividad') 

    session = obtener_JSESSIONID()
    url = "https://eros.pucp.edu.pe/pucp/procinsc/piwconfi/piwconfi"
    data = {
      "accion": "BuscarActividad",
      "nombreProceso": nombre,
    }
    res = session.post(url, data=data)
    res.raise_for_status()
    html_content = res.text
    soup = BeautifulSoup(html_content, 'html.parser')
    # Buscar la primera fila de la tabla que contiene los resultados de búsqueda
    table = soup.find_all('table', width='98%')[2]  # Selecciona la tabla relevante
    print("TABLE", table)
    first_row = table.find_all('tr')[1]  # Saltamos el primer 'tr' (es el encabezado) y tomamos la primera fila de datos

    # Buscar el enlace en la primera fila
    link = first_row.find('a', class_='pucpLinkCelda')  # Encuentra el enlace con la clase específica
    
    # Obtener el href del enlace
    if link:
      url = link.get('href')
      print(url)
    else:
      print("No se encontró el enlace")

    # Analizar la URL
    parsed_url = urlparse(url)
    # Extraer los parámetros del query
    query_params = parse_qs(parsed_url.query)
    proceso = {k: v[0] for k, v in query_params.items()}
    # ***** Ejemplo de simple_query_params
    # {
    #   'accion': 'AbrirPanelActividad',
    #   'tipoProceso': '090',
    #   'identificaProceso': '909'
    # }

    url_participantes = "https://eros.pucp.edu.pe/pucp/procinsc/piwadmin/piwadmin"
    search_params = {
      "accion": "BuscarParticipantesActividad",
      "tipoproceso": proceso["tipoProceso"],
      "identificaproceso": proceso["identificaProceso"]
    }

    res = session.get(url_participantes, params=search_params)
    html_content = res.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # Encontrar todas las filas de la tabla que contienen participantes
    tabla_participantes = soup.find('tbody')
    filas = tabla_participantes.find_all('tr')

    # Extraer información de cada participante
    participantes = []
    for fila in filas:
      columnas = fila.find_all('td')
      numero = columnas[0].text.strip()  # Número del participante
      codigo = columnas[1].text.strip()  # Código del participante
      nombre = columnas[2].text.strip()  # Nombre del participante
      correo = columnas[3].text.strip()  # Correo del participante
      # f1413377@pucp.edu.pe,mard1208@gmail.com

      correos = correo.split(",")

      if (len(correos) > 1):
        correo_pucp = correos[0]
        correo_personal = correos[1]
      else:
        correo_pucp = correo
        correo_personal = ""
        
      participante = {
        'numero': numero,
        'codigo': codigo,
        'nombre': nombre,
        'correo_pucp': correo_pucp,
        'correo_personal': correo_personal
      }
      participantes.append(participante)
    return Response({"data": proceso, "participantes": participantes}, status=status.HTTP_200_OK)