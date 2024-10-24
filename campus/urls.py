from django.urls import path
from .views.user_views import UserCampusView
from .views.actividad_views import ActividadCampusView, ObtenerVacantesView
from .views.propuesta_views import PropuestaCampusView
from .views.actividad_participantes_views import ActividadParticipantesCampusView
from .views.inscripcion_views_2 import AgregarInscripcionView, ModificarInscripcionView, EliminarInscripcionView, ObtenerInscritosView
# from views.user_views import UserCampusView
# from views.actividad_views import ActividadCampusView
#import UserCampusView, ActividadCampusView

urlpatterns = [
    path('usercampus/', UserCampusView.as_view(), name='usercampus'),
    path('actividades/actividades', ActividadCampusView.as_view(), name='actividad'),
    path("actividades/participantes", ActividadParticipantesCampusView.as_view(), name="actividad_participantes"),
    path('actividades/vacantes', ObtenerVacantesView.as_view(), name='vacantes'),
    path('propuesta/', PropuestaCampusView.as_view(), name='propuesta'),
    path('inscripcion/obtener/', ObtenerInscritosView.as_view(), name='obtener_inscritos'),
    path('inscripcion/agregar/', AgregarInscripcionView.as_view(), name='agregar_inscripcion'),
    path('inscripcion/modificar/', ModificarInscripcionView.as_view(), name='modificar_inscripcion'),
    path('inscripcion/eliminar/', EliminarInscripcionView.as_view(), name='eliminar_inscripcion'),
]
