import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bs4 import BeautifulSoup
import urllib.parse
import json
from ..utils.helpers import obtener_JSESSIONID, separar_nombre_completo, buscar_persona_por_nombres

# @csrf_exempt  # Solo necesario si estás desarrollando una API que acepta solicitudes desde otro dominio
# @require_GET  # Asegura que la vista solo responda a solicitudes GET
class UserCampusView(APIView):
    def get(self, request):
      print("PETICION GET")
      session = obtener_JSESSIONID();
        # Obtener el parámetro 'codigo' de la solicitud
      codigo = request.query_params.get('codigo')
      ap_pat = request.query_params.get('ap_pat')
      ap_mat = request.query_params.get('ap_mat')
      nombres = request.query_params.get('nombres')
      if not codigo:
          if not ap_pat and not ap_mat and not nombres:
            return Response({"error": "Falta el parámetro 'codigo'"}, status=status.HTTP_400_BAD_REQUEST)
          else:
            return buscar_persona_por_nombres(session, ap_pat or "", ap_mat or "", nombres or "")
      api_url = "https://eros.pucp.edu.pe/pucp/general/gewpealu/gewpealu"
      search_params = {
        "accion": "AbrirPanel",
        "codigo": codigo,
        "misdatos": "0",
      }
      query_string = urllib.parse.urlencode(search_params)
      full_url = f"{api_url}?{query_string}"
      print("BUSCANDO CODIGO", codigo)
      try:
          headers = {
            'Cache-Control': 'max-age=0',
            'Cookie': f'JSESSIONID={session.cookies.get("JSESSIONID")}',
          }
          response = requests.get(full_url, headers=headers)
          response.raise_for_status()
          
          html_content = response.text
          soup = BeautifulSoup(html_content, 'html.parser')

          persona_data = {}

          # Extraer nombre
          nombre = soup.select_one("table.pucpTablaTitulo font.pucpTitulo").get_text(strip=True)
          persona_data['nombre'] = nombre

          # Extraer correo
          correo_href = soup.select_one("a.pucpSubTitulo")['href']
          correo = urllib.parse.parse_qs(urllib.parse.urlparse(correo_href).query)['dirPara'][0]
          persona_data['correo'] = urllib.parse.unquote(correo)

          # Extraer otros datos
          otros_datos = [el.get_text(strip=True) for el in soup.select("td.pucpValor")]
          persona_data['otrosDatos'] = otros_datos

          # Extraer la foto
          foto_url = soup.select_one('img[alt=""]')['src']
          persona_data['fotoUrl'] = f"https://eros.pucp.edu.pe{foto_url}"

          res = separar_nombre_completo(persona_data['nombre'])
          return buscar_persona_por_nombres(session, res['apellido_paterno'], res['apellido_materno'], res['nombres'])
          # Llamar a la función buscar_persona_por_nombres con el nombre extraído
          # response = buscar_persona_por_nombres(persona_data['nombre'], internal_call=True)
          # print("Persona:", response)
          # return jsonify(response)  # Devolver la respuesta como JSON
          
      except requests.exceptions.RequestException as e:
          return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request):
      print("PETICION POST")
      print("REQUEST", request.content_type)
      
      session = obtener_JSESSIONID();
      print("REQUEST BODY", request.body)
      if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        print("BODY", body_data)
        codigo = body_data.get('codigo')
        ap_pat = body_data.get('ap_pat')
        ap_mat = body_data.get('ap_mat')
        nombres = body_data.get('nombres')
      else:
        codigo = request.POST.get('codigo')
        ap_pat = request.POST.get('ap_pat')
        ap_mat = request.POST.get('ap_mat')
        nombres = request.POST.get('nombres')
        
      if not codigo:
          if not ap_pat and not ap_mat and not nombres:
            return Response({"error": "Falta el parámetro 'codigo'"}, status=status.HTTP_400_BAD_REQUEST)
          else:
            return buscar_persona_por_nombres(session, ap_pat or "", ap_mat or "", nombres or "")
      api_url = "https://eros.pucp.edu.pe/pucp/general/gewpealu/gewpealu"
      search_params = {
        "accion": "AbrirPanel",
        "codigo": codigo,
        "misdatos": "0",
      }
      query_string = urllib.parse.urlencode(search_params)
      full_url = f"{api_url}?{query_string}"
      
      try:
          headers = {
            'Cache-Control': 'max-age=0',
            'Cookie': f'JSESSIONID={session.cookies.get("JSESSIONID")}',
          }
          response = requests.get(full_url, headers=headers)
          response.raise_for_status()
          
          html_content = response.text
          soup = BeautifulSoup(html_content, 'html.parser')

          persona_data = {}

          # Extraer nombre
          nombre = soup.select_one("table.pucpTablaTitulo font.pucpTitulo").get_text(strip=True)
          persona_data['nombre'] = nombre

          # Extraer correo
          correo_href = soup.select_one("a.pucpSubTitulo")['href']
          correo = urllib.parse.parse_qs(urllib.parse.urlparse(correo_href).query)['dirPara'][0]
          persona_data['correo'] = urllib.parse.unquote(correo)

          # Extraer otros datos
          otros_datos = [el.get_text(strip=True) for el in soup.select("td.pucpValor")]
          persona_data['otrosDatos'] = otros_datos

          # Extraer la foto
          foto_url = soup.select_one('img[alt=""]')['src']
          persona_data['fotoUrl'] = f"https://eros.pucp.edu.pe{foto_url}"

          res = separar_nombre_completo(persona_data['nombre'])
          return buscar_persona_por_nombres(session, res['apellido_paterno'], res['apellido_materno'], res['nombres'])
          # Llamar a la función buscar_persona_por_nombres con el nombre extraído
          # response = buscar_persona_por_nombres(persona_data['nombre'], internal_call=True)
          # print("Persona:", response)
          # return jsonify(response)  # Devolver la respuesta como JSON
          
      except requests.exceptions.RequestException as e:
          print("Error al realizar la búsqueda:", e)
          return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
