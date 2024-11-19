from django.urls import path
from . import views
from .views import buscar_itens

urlpatterns = [
        path('', views.homepage, name="homepage"),         # Inclui as urls do app blog
        path('login', views.login, name="login"),           # Inclui as urls do app blog
        path('cadastroUsuario', views.cadastroUsuario, name='cadastroUsuario'),
        path('profile', views.profile, name="profile"),       # Inclui as urls do app blog
        path('faq', views.faq, name="faq"),                 # Inclui as urls do app blog
        path('welcomeHomepage', views.welcomeHomepage, name="welcomeHomepage"),   # Inclui as urls do app blog
        path('itens', views.itens, name="itens"),           # Inclui as urls do app blog
        path('adicionar_inventario', views.adicionar_inventario, name="adicionar_inventario"),   # Inclui as urls do app blog
        path('buscar', buscar_itens, name='buscar_itens'),
        path('excluir_inventario/', views.excluir_inventario, name='excluir_inventario'),
        path('update-item/', views.update_item, name='update_item'),
        path('excluir-item/', views.excluir_inventario, name='excluir_inventario'),
        path('update-sala/', views.update_sala, name='update_sala'),
        path('excluir-sala/', views.excluir_sala, name='excluir_sala'),
        path('adicionar-salas/', views.adicionar_salas, name='adicionar_salas'),
        path('buscar-itens-sala', views.buscar_itens_sala, name='buscar_itens_sala'),
        path('salas', views.salas, name='salas'),
        path('buscar-salas', views.buscar_salas, name='buscar_salas'),
        path('logout/', views.logout, name='logout'),
        path('usuarios/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
        path('editar_usuario/', views.editar_usuario, name='editar_usuario'),
        path('excluir_usuario/', views.excluir_usuario, name='excluir_usuario'),
]