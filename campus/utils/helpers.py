import unicodedata
import requests
from bs4 import BeautifulSoup
from rest_framework.response import Response
from rest_framework import status
import urllib.parse
# In your settings or function where you need credentials
from decouple import config

USERNAME = config('USER')
PASSWORD = config('PASSWORD')

def obtener_JSESSIONID():
    res = requests.get("https://pandora.pucp.edu.pe/pucp/login?TARGET=https%3A%2F%2Feros.pucp.edu.pe%2Fpucp%2Fjsp%2FIntranet.jsp")
    # Crear una instancia de BeautifulSoup
    soup = BeautifulSoup(res.text, 'html.parser')
    print("USERNAME AND PASSWORD", USERNAME, PASSWORD)
    # Encontrar el input con name="execution"
    execution_input = soup.find('input', {'name': 'execution'})

    # Obtener el valor del atributo 'value'
    execution_value = execution_input['value'] if execution_input else None

    session = requests.Session()
    payload = {
        "username": USERNAME,
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