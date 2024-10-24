import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bs4 import BeautifulSoup
import urllib.parse
import json
import re
from ..utils.helpers import obtener_JSESSIONID, separar_nombre_completo, buscar_persona_por_nombres

estado_opciones = {
  "INSCRITO": "0",
  "INVITADO": "G",
  "MATRICULADO": "1",
  "ELIMINADO": "3",
  "RETIRADO": "5",
  "REGISTRO INCOMPLETO": "I",
  "REGISTRO CANCELADO": "J",
  "APTO": "9"
}

class InscripcionCampusView(APIView):
  def post(self, request):
    session = obtener_JSESSIONID();

    accion = request.data.get("accion")
    tipo_proceso = request.data.get("tipo_proceso")
    identifica_proceso = request.data.get("identifica_proceso")
    codigo = request.data.get("codigo")

    url_modificar_inscritos = "https://eros.pucp.edu.pe/pucp/procinsc/piwadmin/piwadmin"
    print("JSSessionID: ", session.cookies.get("JSESSIONID"))
    datos_proceso = {
      "accion": accion,
      "tipoproceso": tipo_proceso,
      "identificaproceso": identifica_proceso,
      "ordenarPor": "",
      "accionOrd": "BusquedaListaInscritos",
      "tipoEnvio": "",
      "hProgramado": "",
      "cis": 1,
      "flag": "",
      "session": session.cookies.get("JSESSIONID"),
      "padre": 0,
      "indActivHorario": "",
      "codDestino": "",
      "horariobusca": "",
      "tipoingresobusca": "",
      "codparticipante": "",
      "nombparticipante": "",
      "horariosModificacion": "[]",
      "tiposIngresoModificacion": "",
      "codigosModificacion": "",
      "codigosEliminacion": ""
    }

    if accion == "EliminarInscritos":
      datos_proceso["codigosEliminacion"] = f"[\"{codigo}\"]"
      res = session.post(url_modificar_inscritos, data=datos_proceso)
    elif accion == "ModificarInscritos":
      estado = request.data.get("estado")
      datos_proceso["tiposIngresoModificacion"] = f"[\"{estado_opciones[estado]}\"]"
      datos_proceso["codigosModificacion"] = f"[\"{codigo}\"]"
      res = session.post(url_modificar_inscritos, data=datos_proceso)

    if accion == "Agregar":
      url_agregar_inscritos = "https://eros.pucp.edu.pe/pucp/procinsc/piwinscr/piwinscr"

      datos_inscripcion = {
        "indusosiete": "",
        "mensajeusosiete": "",
        "tipoproceso": tipo_proceso,
        "identificaproceso": identifica_proceso,
        "accion": "CrearInscDatosGenerales",
        "fechaNac": "",
        "inscradmin": "",
        "indCriterioBusqueda": "codigo",
        "codResultado": "",
        "codValido": 1,
        "codigo": codigo,
        "dni": "",
        "fechaNacOblig": 1,
        "correoOblig": 1,
        "apeMaternoOblig": 0,
        "apepaterno": "",
        "apematerno": "",
        "nombres": "",
        "nacdia": "",
        "nacmes": "",
        "nacano": "",
        "correo": "",
        "correoEditable": 1
      }
      res = session.post(url_agregar_inscritos, data=datos_inscripcion)
      res.raise_for_status()
      # res.encoding = 'utf-8' 
      html = res.text
      print("HTML 1 AGREGAR", html)
      soup = BeautifulSoup(html, 'html.parser')
      # Extraer los valores de los campos que necesitas
      dni = soup.find('input', {'name': 'dni'})['value'] if soup.find('input', {'name': 'dni'}) else ""
      apepaterno = soup.find('input', {'name': 'apepaterno'})['value'] if soup.find('input', {'name': 'apepaterno'}) else ""
      apematerno = soup.find('input', {'name': 'apematerno'})['value'] if soup.find('input', {'name': 'apematerno'}) else ""
      nombres = soup.find('input', {'name': 'nombres'})['value'] if soup.find('input', {'name': 'nombres'}) else ""

      nacdia = soup.find('input', {'name': 'nacdia_txt'})['value'] if soup.find('input', {'name': 'nacdia_txt'}) else ""
      nacmes = soup.find('input', {'name': 'nacmes_txt'})['value'] if soup.find('input', {'name': 'nacmes_txt'}) else ""
      nacano = soup.find('input', {'name': 'nacano_txt'})['value'] if soup.find('input', {'name': 'nacano_txt'}) else ""
      fecha_nac = f"{nacdia}/{nacmes}/{nacano}" if nacdia and nacmes and nacano else ""

      correopucp = soup.find('input', {'name': 'correopucp'})['value'] if soup.find('input', {'name': 'correopucp'}) else ""
      correo = soup.find('input', {'name': 'correo'})['value'] if soup.find('input', {'name': 'correo'}) else ""

      datos_inscripcion_generales = {
        "indusosiete": "",
        "mensajeusosiete": "",
        "tipoproceso": tipo_proceso,
        "identificaproceso": identifica_proceso,
        "accion": "AgregarInscDatosGenerales",
        "fechaNac": "",
        "inscradmin": "1",
        "indCriterioBusqueda": "",
        "codResultado": codigo,
        "codValido": "1",
        "codigo": codigo,
        "dni": dni,
        "fechaNacOblig": "1",
        "correoOblig": "1",
        "apeMaternoOblig": "0",
        "apepaterno": apepaterno,
        "apematerno": apematerno,
        "nombres": nombres,
        "nacdia_txt": nacdia,
        "nacmes_txt": nacmes,
        "nacano_txt": nacano,
        "correopucp": correopucp,
        "correo": correo,
        "correoEditable": "1"
      }
      print("DATOS INSCRIPCION GENERALES", datos_inscripcion_generales)
      res = session.post(url_agregar_inscritos, data=datos_inscripcion_generales)
      res.encoding = 'utf-8' 
      # print("HTML 2 AGREGAR", res.text)
      url_crear_inscritos_datos_principales = f"https://eros.pucp.edu.pe/pucp/procinsc/piwinscr/piwinscr?accion=CrearInscDatosPrincipales&codigo={codigo}&tipoproceso={tipo_proceso}&identificaproceso={identifica_proceso}&inscradmin=1"

      datos_inscripcion_principales = {
        "accion": "CrearInscDatosPrincipales",
        "codigo": codigo,
        "tipoproceso": tipo_proceso,
        "identificaproceso": identifica_proceso,
        "inscradmin": "1",
      }

      res = session.get(url_crear_inscritos_datos_principales, data=datos_inscripcion_principales)
      res.raise_for_status()
      # res.encoding = 'utf-8'
      html = res.text
      # print("HTML 3 AGREGAR", html)
      soup = BeautifulSoup(html, 'html.parser')
      form = soup.find("form", {"name": "formPreinscripcion"})
      # print("FORMMMMM", form)
      # Crear la lista de tuplas para almacenar los datos del formulario
      form_data = []

      # Recorrer todos los campos 'input'
      for input_tag in form.find_all('input'):
        input_name = input_tag.get('name')
        input_value = input_tag.get('value', '')  # Si no tiene valor, asignar cadena vacía

        # Agregar cada par (name, value) como una tupla en la lista
        if input_name:  # Asegurarse de que el input tenga nombre
          form_data.append((input_name, input_value))

      # Manejar `select` (comboboxes)
      for select_tag in form.find_all('select'):
        select_name = select_tag.get('name')
        selected_options = select_tag.find_all('option', selected=True)

        if select_name:
          # Si es un combobox con múltiples opciones seleccionadas
          if select_tag.has_attr('multiple'):
            for option in selected_options:
              form_data.append((select_name, option.get('value')))
          else:
            # Si es un combobox con una sola opción seleccionada
            if selected_options:
              form_data.append((select_name, selected_options[0].get('value')))
      # Actualizar la tupla con el campo 'accion'
      for i, (name, value) in enumerate(form_data):
        if name == 'accion':
          # Reemplazar la tupla existente con la nueva tupla modificada
          form_data[i] = ('accion', 'AgregarInscDatosPrincipales')
      # Imprimir los datos extraídos del formulario
      print("FORM DATA:", form_data)
      # Establecer los encabezados para asegurar que se envían correctamente en UTF-8
      headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      }

      # Enviar los datos usando requests.post
      res = session.post(url_agregar_inscritos, data=form_data, headers=headers)
      res.raise_for_status()
      res.encoding = 'utf-8' 
      html = res.text

      # print("HTML 4 AGREGAR", html)
    # print(res.text)
    return Response("Matrícula exitosa", status=status.HTTP_200_OK)
