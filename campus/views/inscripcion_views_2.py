from urllib.parse import urlparse, parse_qs
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bs4 import BeautifulSoup
import requests
from ..utils.helpers import obtener_JSESSIONID, get_all_form_values, modify_form_data

# Mappings for status options
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

class ObtenerInscritosView(APIView):
    def post(self, request):
        session = obtener_JSESSIONID()
        tipo_proceso = request.data.get("tipo_proceso")
        identifica_proceso = request.data.get("identifica_proceso")

        datos_proceso = {
            "accion": "BusquedaListaInscritos",
            "tipoproceso": tipo_proceso,
            "identificaproceso": identifica_proceso,
            "padre": 0
        }

        try:
            url_participantes = "https://eros.pucp.edu.pe/pucp/procinsc/piwadmin/piwadmin"
            res = session.get(url_participantes, params=datos_proceso)
            html_content = res.text
            # Crear un objeto BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')  # Puedes usar 'html.parser' si no tienes 'lxml'

            # Encontrar la tabla con id 'tInscripciones'
            tabla_inscripciones = soup.find('table', {'id': 'tInscripciones'})

            # Verificar si la tabla fue encontrada
            if not tabla_inscripciones:
                print("No se encontró la tabla de inscripciones.")
                return Response({"message": "No hay inscritos"}, status=status.HTTP_400_BAD_REQUEST)

            # Encontrar todas las filas de la tabla, excluyendo la primera fila de encabezado
            filas = tabla_inscripciones.find_all('tr')[1:]  # Asumiendo que la primera fila es el encabezado

            # Lista para almacenar los datos de los participantes
            participantes = []

            for fila in filas:
                columnas = fila.find_all('td')
                
                if len(columnas) < 7:
                    # Si la fila no tiene suficientes columnas, posiblemente sea una fila vacía o de error
                    continue
                
                try:
                    # Extraer datos de cada columna según su posición
                    numero = columnas[0].get_text(strip=True)
                    
                    # Código del participante
                    codigo_tag = columnas[1].find('a')
                    codigo = codigo_tag.get_text(strip=True) if codigo_tag else columnas[1].get_text(strip=True)
                    
                    # Nombre del participante
                    nombre_tag = columnas[2].find('a')
                    nombre = nombre_tag.get_text(strip=True) if nombre_tag else columnas[2].get_text(strip=True)
                    
                    # Correos electrónicos
                    correos_input = columnas[3].find('input', {'name': 'correos'})
                    correos = correos_input['value'] if correos_input else columnas[3].get_text(strip=True)
                    # Separar correos si hay múltiples
                    correos_lista = [correo.strip() for correo in correos.split(',') if correo.strip()]
                    
                    # Fecha de inscripción
                    fecha_inscripcion = columnas[4].get_text(strip=True)
                    
                    # Tipo de ingreso (estado)
                    select = columnas[5].find('select', {'name': 'tipoingreso'})
                    estado = None
                    if select:
                        # Encontrar la opción seleccionada
                        opcion_seleccionada = select.find('option', selected=True)
                        if opcion_seleccionada:
                            estado = opcion_seleccionada.get_text(strip=True)
                        else:
                            # Si no hay opción seleccionada explícitamente, tomar la primera opción
                            estado = select.find('option').get_text(strip=True)
                    
                    # Agregar el participante a la lista
                    participante = {
                        'Número': numero,
                        'Código': codigo,
                        'Nombre': nombre,
                        'Correos Electrónicos': correos_lista,
                        'Fecha de Inscripción': fecha_inscripcion,
                        'Estado': estado
                    }
                    
                    participantes.append(participante)
                except Exception as e:
                    print(f"Error al procesar una fila: {e}")
                    continue
            return Response({"message": "Búsqueda exitosa", "data": participantes}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AgregarInscripcionView(APIView):
    def post(self, request):
        session = obtener_JSESSIONID()
        tipo_proceso = request.data.get("tipo_proceso")
        identifica_proceso = request.data.get("identifica_proceso")
        codigo = request.data.get("codigo")

        try:
            link = self.process_agregar_inscripcion(session, tipo_proceso, identifica_proceso, codigo)
            return Response({"message": "Matrícula exitosa", "link": link}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_agregar_inscripcion(self, session, tipo_proceso, identifica_proceso, codigo):
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
        print("DATOS INSCRIPCION", datos_inscripcion)
        # Make the initial request
        res = session.post(url_agregar_inscritos, data=datos_inscripcion)
        print("HEADERSSSSSS", res.headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form', {'name': 'FGenerales'})
        form_values = get_all_form_values(form)
        print("FORM VALUES 1", form_values)
        form_values2 = modify_form_data(form_values)
        res = session.post(url_agregar_inscritos, data=form_values2, allow_redirects=True)
        res.raise_for_status()
        # res.encoding = 'utf-8'
        html = res.text
        # print("HTML 3 AGREGAR", html)
        soup = BeautifulSoup(html, 'html.parser')
        form = soup.find("form", {"name": "formPreinscripcion"})
        form_values = get_all_form_values(form)
        for i, (name, value) in enumerate(form_values):
            if name == 'accion':
            # Reemplazar la tupla existente con la nueva tupla modificada
                form_values[i] = ('accion', 'AgregarInscDatosPrincipales')
        print("FORM DATA:", form_values)
        # Establecer los encabezados para asegurar que se envían correctamente en UTF-8
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        res = session.post(url_agregar_inscritos, data=form_values, headers=headers, allow_redirects=True)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        dec_modificacion = soup.find_all(lambda tag: tag.name == "font" and "datos de participantes." in tag.text)
        if dec_modificacion:
            return
    
        html_content = res.text
        # Crear el objeto BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Buscar todos los enlaces que contienen la función `abrirVentanaPago`
        payment_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'abrirVentanaPago' in href:
                # Extraer la URL del parámetro de la función
                start = href.find("('") + 2
                end = href.find("','")
                if start != -1 and end != -1:
                    payment_link = href[start:end]
                    payment_links.append(payment_link)
        cod_actividad = soup.find("input", {"name": "codActividad"})
        cod_participante = soup.find("input", {"name": "codParticipante"})
        url_terminar = f"https://eros.pucp.edu.pe/pucp/procpago/pcwinscr/pcwinscr;jsessionid={session.cookies.get('JSESSIONID')}?accion=Terminar&codActividad={cod_actividad.get('value', '')}&codParticipante={cod_participante.get('value', '')}&guardarPreventa=1"
        print("URL TERMINAR", url_terminar)
        res = session.get(url_terminar, allow_redirects=True)
        print("HTML", res.text)
        
        url = f"https://eros.pucp.edu.pe{payment_links[0]}"
        # Parsear la URL
        parsed_url = urlparse(url)

        # Obtener los parámetros de consulta (query) como un diccionario
        query_params = parse_qs(parsed_url.query)

        # Extraer el valor de numPreventa
        num_preventa = query_params.get("numPreventa", [None])[0]
        print("URLLLL", url)
        res = session.get(url, allow_redirects=True)
        print("RES HEADERS", res.headers)
        print("HTML", res.text)
        # return res.headers.get('Location', None)
        soup = BeautifulSoup(res.text, 'html.parser')
        secuenciaInput = soup.find("input", {"name": "secuencia"})
        secuencia = secuenciaInput.get("value", "")
        print("SESSION", session.cookies)
        return f"https://gea.pucp.edu.pe/pucp/vtaitnet/vtwpagcv/vtwpagcv?accion=Preparar&secuencia={secuencia}&idsession={session.cookies.get('JSESSIONID', domain='eros.pucp.edu.pe')}&pucpIdioma=es&ec=null"

class ModificarInscripcionView(APIView):
    def post(self, request):
        session = obtener_JSESSIONID()
        tipo_proceso = request.data.get("tipo_proceso")
        identifica_proceso = request.data.get("identifica_proceso")
        codigo = request.data.get("codigo")
        estado = request.data.get("estado")

        datos_proceso = {
            "accion": "ModificarInscritos",
            "tipoproceso": tipo_proceso,
            "identificaproceso": identifica_proceso,
            "tiposIngresoModificacion": f"[\"{estado_opciones.get(estado, '')}\"]",
            "codigosModificacion": f"[\"{codigo}\"]",
        }

        try:
            url_modificar_inscritos = "https://eros.pucp.edu.pe/pucp/procinsc/piwadmin/piwadmin"
            res = session.post(url_modificar_inscritos, data=datos_proceso)
            return Response({"message": "Modificación exitosa"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EliminarInscripcionView(APIView):
    def post(self, request):
        session = obtener_JSESSIONID()
        tipo_proceso = request.data.get("tipo_proceso")
        identifica_proceso = request.data.get("identifica_proceso")
        codigo = request.data.get("codigo")

        datos_proceso = {
            "accion": "EliminarInscritos",
            "tipoproceso": tipo_proceso,
            "identificaproceso": identifica_proceso,
            "codigosEliminacion": f"[\"{codigo}\"]",
        }

        try:
            url_modificar_inscritos = "https://eros.pucp.edu.pe/pucp/procinsc/piwadmin/piwadmin"
            res = session.post(url_modificar_inscritos, data=datos_proceso)
            return Response({"message": "Eliminación exitosa"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)