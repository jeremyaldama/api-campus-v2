from django.urls import path
from .views.user_views import UserCampusView
from .views.actividad_views import ActividadCampusView
from .views.propuesta_views import PropuestaCampusView
from .views.actividad_participantes_views import ActividadParticipantesCampusView
from .views.inscripcion_views import InscripcionCampusView
# from views.user_views import UserCampusView
# from views.actividad_views import ActividadCampusView
#import UserCampusView, ActividadCampusView

urlpatterns = [
    path('usercampus/', UserCampusView.as_view(), name='usercampus'),
    path('actividad/', ActividadCampusView.as_view(), name='actividad'),
    path("actividad/participantes", ActividadParticipantesCampusView.as_view(), name="actividad_participantes"),
    path('propuesta/', PropuestaCampusView.as_view(), name='propuesta'),
    path('inscripcion/', InscripcionCampusView.as_view(), name='inscripcion'),
]
