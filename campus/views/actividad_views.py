import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse, parse_qs
import json
from ..utils.helpers import obtener_JSESSIONID, buscar_actividad, obtener_datos_vacantes_actividad

class ActividadCampusView(APIView):
    
    def get(self, request):
      print("PETICION GET")
      session = obtener_JSESSIONID();
      nombre_actividad = request.query_params.get('nombre')
      print("NOMBRE ACTIVIDAD", nombre_actividad)
      api_url = "https://eros.pucp.edu.pe/pucp/procinsc/piwconfi/piwconfi"
      api_url_admin = "https://eros.pucp.edu.pe/pucp/procinsc/piwadmin/piwadmin"
      data = {
        "accion": "BuscarActividad",
        "comboAreaProceso": "06",
        "nombreProceso": nombre_actividad,
      }

      headers = {
         'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }
      try:
        res = session.post(api_url, data=data, headers=headers)
        html_content = res.text
        print("HTML CONTENT", html_content)
        soup = BeautifulSoup(html_content, 'html.parser')
        tds = soup.find_all('td', class_='pucpCelda')
        links = soup.find_all('a', class_='pucpLinkCelda')

        link=links[0]['href']
        print("LINK" + link)
        # Analizar la URL
        parsed_url = urlparse(link)

        # Analizar la cadena de consulta
        query_params = parse_qs(parsed_url.query)

        # Extraer los valores de 'tipoProceso' e 'identificaProceso'
        tipo_proceso = query_params.get('tipoProceso', [None])[0]
        identifica_proceso = query_params.get('identificaProceso', [None])[0]
        print("TIPO PROCESO", tipo_proceso)
        print("IDENTIFICA PROCESO", identifica_proceso)
        data = {}
        data["unidad_responsable"] = tds[2].get_text(strip=True)
        data["fecha_inicio"] = tds[3].get_text(strip=True)
        data["fecha_fin"] = tds[4].get_text(strip=True)
        data["modalidad"] = tds[5].get_text(strip=True)
        data["numero_matriculados"] = tds[6].get_text(strip=True)

        search_params = {
           "accion": "BuscarListaDocentes",
           "tipoProceso": tipo_proceso,
           "identificaProceso": identifica_proceso
        }
        res = session.get(api_url_admin, params=search_params)
        res.raise_for_status()
        # Encontrando todas las tablas con los atributos deseados
        html_content = res.text
        print("LISTA DOCENTES", html_content)
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table', {'border': '0', 'width': '100%'})

        # Encuentra todas las tablas que tengan la clase "pucpTablaSubTitulo" y el ancho "100%"
        asignaturas = soup.find_all("table", {"class": "pucpTablaSubTitulo", "width": "100%"})

        modulos = {}
        # Imprime las tablas encontradas
        for index, tabla in enumerate(asignaturas):
          print(f"Tabla {index + 1}:")
          primera_tr = tabla.find("tr")
          next_sibling =  tabla.find_next_sibling()
          if next_sibling:
            name = next_sibling.name
            print("NAME", name)
          if primera_tr:
              primer_td = primera_tr.find("td")
              if primer_td:
                  modulos[index] = {
                    "nombre": primer_td.get_text(strip=True),
                    "tiene_profesores": name == "table"  
                  }
                  print(f"Nombre del módulo: {modulos[index]}")
              else:
                  print("No se encontró ningún <td> dentro del primer <tr>")
          else:
              print("No se encontró ningún <tr> dentro de la tabla")
          print("\n---\n")
        # Initialize dictionary to store results
        result = {}

        # iterate through an object
        for key, value in modulos.items():
          result[modulos[key]["nombre"]] = []

        # Iterate through matched tables
        guardados = []
        for idx, table in enumerate(tables):
            rows = table.find_all('tr')
            table_data = []
            
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3:  # Ensure row has enough columns
                    numero = cols[0].text.strip()
                    codigo = cols[1].text.strip()  # Second column (index 1) is the code
                    nombre = cols[2].text.strip()  # Third column (index 2) is the name
                    rol = cols[3].text.strip()  # Fourth column (index 3) is the role
                    table_data.append({'numero': numero, 'codigo': codigo, 'nombre': nombre, 'rol': rol})
            
            # Add table data to result dictionary
            # result[f'tabla_{idx+1}'] = table_data
            if modulos[idx]["tiene_profesores"] == True:
              result[modulos[idx]["nombre"]] = table_data
            else:
              guardados.append(table_data)

        for key, value in modulos.items():
          if value["tiene_profesores"] == True and len(guardados) > 0 and result[modulos[key]["nombre"]] == []:
            result[modulos[key]["nombre"]] = guardados.pop(-1)
            

        search_params = {
           "accion": "AbrirActividadDatosGenerales",
           "tipoProceso": tipo_proceso,
           "identificaProceso": identifica_proceso
        }
        response_datos = session.get(api_url, params=search_params)
        response_datos.raise_for_status()
        html_datos = response_datos.text
        soup_datos = BeautifulSoup(html_datos, 'html.parser')

        # Definir las etiquetas que buscamos
        targets = {
          "numero_de_propuesta": {"label": "Número de propuesta", "class": "pucpCriterio"},
          "tipo_de_actividad": {"label": "Tipo de actividad", "class": "pucpCriterio"},
          "modalidad": {"label": "Modalidad", "class": "pucpCriterio"},
          "diseno": {"label": "Diseño", "class": "pucpCriterio", "alternative_label": "Dise&ntilde;o"}
        }

        # Diccionario para almacenar los resultados
        results = {}

        # Buscar las tablas que contienen la información
        tables = soup_datos.find_all('table', {"width": "98%", "align": "center"})

        for table in tables:
          for key, value in targets.items():
            criterio_td = table.find('td', text=value['label'])
            if criterio_td:
              valor_td = criterio_td.find_next_sibling('td', class_="pucpValor")
              if valor_td:
                results[key] = valor_td.get_text(strip=True)
            # Caso especial para "Diseño" por el uso de 'Dise&ntilde;o'
            elif 'alternative_label' in value:
              criterio_td = table.find('td', text=value['alternative_label'])
              if criterio_td:
                valor_td = criterio_td.find_next_sibling('td', class_="pucpValor")
                if valor_td:
                  results[key] = valor_td.get_text(strip=True)

        for key, value in results.items():
          print(f"{key}: {value}")

        search_params = {
           "accion": "AbrirActividadEstructura",
           "tipoProceso": tipo_proceso,
           "identificaProceso": identifica_proceso
        }
        response_datos = session.get(api_url, params=search_params)
        response_datos.raise_for_status()
        html_datos = response_datos.text
        soup = BeautifulSoup(html_datos, 'html.parser')

        # Encuentra todas las filas en las tablas de unidades formativas
        claves = []

        # Encuentra todas las filas que tienen las celdas con las clases específicas
        rows = soup.find_all('tr')

        for row in rows:
          # Encuentra todas las celdas en la fila
          celdas = row.find_all('td', class_=['pucpCelda', 'pucpCeldaGris'])
          if len(celdas) > 3:
            clave = celdas[0].get_text(strip=True)
            print("CLAVE " + clave)
            if clave.isdigit():
              print("CLAVE IS DIGIT " + clave)
              claves.append(clave)

        # Imprime las claves encontradas
        for clave in claves:
          print(f"Clave: {clave}")

        return Response({**data, "modulos": result, **results, "claves": claves}, status=status.HTTP_200_OK)
      except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
class ObtenerVacantesView(APIView):
   def get(self, request):
      session = obtener_JSESSIONID();
      nombre_actividad = request.query_params.get('nombre')
      api_url = "https://eros.pucp.edu.pe/pucp/procinsc/piwconfi/piwconfi"
      api_url_admin = "https://eros.pucp.edu.pe/pucp/procinsc/piwadmin/piwadmin"
      data = {
        "accion": "BuscarActividad",
        "comboAreaProceso": "06",
        "nombreProceso": "SS-VII PROGRAMA DE ESPECIALIZACIÓN EN LIDERAZGO Y GERENCIA DE LA FELICIDAD 2024-01",
      }

      headers = {
         'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }
      try:
        datos = []
        vacantes_1 = obtener_datos_vacantes_actividad(session, api_url, headers, **data)
        datos.append({"nombre_curso": "SS-VII PROGRAMA DE ESPECIALIZACIÓN EN LIDERAZGO Y GERENCIA DE LA FELICIDAD 2024-01" + " - Vacantes " + vacantes_1})

        data = {
          "accion": "BuscarActividad",
          "comboAreaProceso": "06",
          "nombreProceso": "CI-MM-OCT-24 CURSO DE CAPACITACIÓN EN POWER AUTOMATE NIVEL BÁSICO 2024-01",
        }
        vacantes_2 = obtener_datos_vacantes_actividad(session, api_url, headers, **data)
        datos.append({"nombre_curso": "CI-MM-OCT-24 CURSO DE CAPACITACIÓN EN POWER AUTOMATE NIVEL BÁSICO 2024-01" + " - Vacantes " + vacantes_2})

        data = {
          "accion": "BuscarActividad",
          "comboAreaProceso": "06",
          "nombreProceso": "TALLER DE TEATRO Y EXPRESIÓN CREATIVA 2024-03",
        }
        vacantes_3 = obtener_datos_vacantes_actividad(session, api_url, headers, **data)
        datos.append({"nombre_curso": "TALLER DE TEATRO Y EXPRESIÓN CREATIVA 2024-03" + " - Vacantes " + vacantes_3})

        return Response({"data": datos}, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

