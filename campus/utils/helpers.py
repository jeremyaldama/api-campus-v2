import unicodedata
import requests
from bs4 import BeautifulSoup
from rest_framework.response import Response
from rest_framework import status
import urllib.parse
from urllib.parse import urlparse, parse_qs
# In your settings or function where you need credentials
from decouple import config

USERNAMEC = config('USERC')
PASSWORD = config('PASSWORD')

def obtener_JSESSIONID():
    res = requests.get("https://pandora.pucp.edu.pe/pucp/login?TARGET=https%3A%2F%2Feros.pucp.edu.pe%2Fpucp%2Fjsp%2FIntranet.jsp")
    # Crear una instancia de BeautifulSoup
    soup = BeautifulSoup(res.text, 'html.parser')
    print("USERNAME AND PASSWORD", USERNAMEC, PASSWORD)
    # Encontrar el input con name="execution"
    execution_input = soup.find('input', {'name': 'execution'})

    # Obtener el valor del atributo 'value'
    execution_value = execution_input['value'] if execution_input else None

    session = requests.Session()
    payload = {
        "username": USERNAMEC,
        "password": PASSWORD,
        "execution": execution_value,
        "_eventId": "submit",
    }

    response = session.post("https://pandora.pucp.edu.pe/pucp/login?TARGET=https%3A%2F%2Feros.pucp.edu.pe%2F", data=payload)
    cookies = session.cookies

    # Imprime las cookies

    # Para acceder a una cookie específica, usa cookies.get(nombre_cookie)
    # session_cookie = cookies.get('JSESSIONID')
    return session;

def separar_nombre_completo(nombre_completo):
  # Primero, separar por la coma
  apellidos, nombres = nombre_completo.split(',')

  # Luego, separar los apellidos por el espacio
  apellido_paterno, apellido_materno = apellidos.strip().split()

  # Eliminar espacios extra alrededor de los nombres
  nombres = nombres.strip()

  return {
      'apellido_paterno': apellido_paterno,
      'apellido_materno': apellido_materno,
      'nombres': nombres
  }

def buscar_persona_por_nombres(session=None, ap_pat="", ap_mat="", nombres=""):
  url = "https://eros.pucp.edu.pe/pucp/general/gewpealu/gewpealu"
    
  # Payload recibido desde los search params o desde la llamada interna
  payload = {
      'accion': 'Buscar',
      'apepaterno': ap_pat,
      'apematerno': ap_mat,
      'nombres': nombres,
      'codigo': '',
      'docenteactivo': 'on',
      'docentejyb': '',
      'nodocenteactivo': 'on',
      'nodocentejyb': '',
      'alumnomat': 'off',
      'alumnonomat': 'off',
      'egresadoasoc': '',
      'alumnoext': '',
      'email': '',
      'tipodocumento': '',
      'numerodocumento': '',
      'enintranet': '1',
  }
  headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Cookie': f'JSESSIONID={session.cookies.get("JSESSIONID")}',
  }

  try:
    response = requests.post(url, headers=headers, data=urllib.parse.urlencode(payload))
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # Extraer las tablas de resultados de búsqueda
    tablas = []
    
    for table in soup.find_all('table'):
        if table.find('td', class_='pucpNro'):
            rows = []
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all('td')]
                if cells:  # Solo agregar filas que no estén vacías
                    rows.append(cells)
            if rows:
                tablas.append(rows)
    
    return Response({"tablas": tablas}, status=status.HTTP_200_OK)
  except requests.RequestException as e:
    return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
def quitar_tildes(texto):
    # Normaliza el texto en forma de descomposición canónica
    texto_normalizado = unicodedata.normalize('NFD', texto)
    # Elimina los caracteres acentuados (diacríticos)
    texto_sin_tildes = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return texto_sin_tildes


def get_all_form_values(form):
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
    return form_data

def modify_form_data(form_data):
    # Helper functions to find index of a tuple based on the key
    def get_tuple_index(key):
        for index, (name, _) in enumerate(form_data):
            if name == key:
                return index
        return None

    # Helper function to update the value of a tuple
    def update_tuple_value(key, new_value):
        index = get_tuple_index(key)
        if index is not None:
            form_data[index] = (key, new_value)
        else:
            form_data.append((key, new_value))

    # fValidarDatosGenerales logic
    mensaje_usosiete_index = get_tuple_index("mensajeusosiete")
    if mensaje_usosiete_index is not None and form_data[mensaje_usosiete_index][1] != '':
        usosiete_index = get_tuple_index("usosiete")
        if usosiete_index is not None and form_data[usosiete_index][1] == 'checked':
            update_tuple_value("indusosiete", '1')
        else:
            update_tuple_value("indusosiete", '0')

    codigo_index = get_tuple_index("codigo")
    if codigo_index is not None and form_data[codigo_index][1] != '':
        update_tuple_value("accion", 'AgregarInscDatosGenerales')
        update_tuple_value("inscradmin", '1')

        cod_resultado_index = get_tuple_index("codResultado")
        if cod_resultado_index is not None and form_data[cod_resultado_index][1] == form_data[codigo_index][1]:
            pass  # Simulate form submission
        else:
            print("El código de búsqueda no coincide con los datos generales completados. Presionar el botón Buscar.")
    else:
        # Assuming fValidar() returns '1'
        if get_tuple_index("nacdia_txt") and get_tuple_index("nacmes_txt") and get_tuple_index("nacano_txt"):
            nacdia = form_data[get_tuple_index("nacdia_txt")][1]
            nacmes = form_data[get_tuple_index("nacmes_txt")][1]
            nacano = form_data[get_tuple_index("nacano_txt")][1]
            update_tuple_value("fechaNac", f"{nacdia}/{nacmes}/{nacano}")

        if not valida_fecha(form_data[get_tuple_index("fechaNac")][1]):
            update_tuple_value("fechaNac", "")
        
        update_tuple_value("accion", 'AgregarInscDatosGenerales')
        update_tuple_value("inscradmin", '1')
    return form_data

# Helper functions to simulate validation (to be implemented as needed)
def valida_fecha(fecha):
    # Here you'd implement date validation logic; returning True if valid
    return True  # For simplicity, assume all dates are valid

def valida_numero(numero):
    # Check if the string is all digits
    return numero.isdigit()

def buscar_actividad(html):
    soup = BeautifulSoup(html, 'html.parser')
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
    return {"tipo_proceso": tipo_proceso, "identifica_proceso": identifica_proceso}

def obtener_datos_vacantes_actividad(session, api_url, headers, **data):
    try:
        res = session.post(api_url, data=data, headers=headers)
        res.raise_for_status()
        html_content = res.text
        print("HTML CONTENT", html_content)
        codigos = buscar_actividad(html_content)
        # https://ares.pucp.edu.pe/pucp/procinsc/piwconfi/piwconfi?accion=ConsultarDatosActividad&tipoProceso=090&identificaProceso=909
        search_params = {
            "accion": "ConsultarDatosActividad",
            "tipoProceso": codigos["tipo_proceso"],
            "identificaProceso": codigos["identifica_proceso"]
        }
        res = session.get(api_url, params=search_params)
        html_content = res.text
        # Analizar el contenido HTML con BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Encontrar la tabla específica. En este caso, asumimos que es la única tabla con border="0" y width="100%"
        tabla = soup.find('table', attrs={'border': '0', 'width': '100%'})

        # Verificar si se encontró la tabla
        if not tabla:
            print("No se encontró la tabla especificada.")
            exit()

        # Extraer las filas de la tabla
        filas = tabla.find_all('tr')

        # Lista para almacenar los datos extraídos
        datos = []

        # Iterar sobre las filas, omitiendo la fila de encabezado
        for fila in filas[1:]:  # Saltamos el encabezado
            celdas = fila.find_all('td')
            if len(celdas) >= 3:
                # Extraer el texto de cada celda, eliminando espacios en blanco
                metrica = celdas[1].get_text(strip=True)
                cantidad = celdas[2].get_text(strip=True)
                datos.append({'Métrica': metrica, 'Cantidad': cantidad})
        return datos[3]["Cantidad"]
    except requests.RequestException as e:
        exit()