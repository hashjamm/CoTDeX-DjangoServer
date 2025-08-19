from django.urls import path
from . import views

urlpatterns = [
    path('', views.visualization_home, name='visualization_home'),  # Follow-up 입력 페이지
    path('graph/', views.graph_page, name='graph_page'),           # 그래프 표시 페이지
    path('search_pubmed/', views.search_pubmed, name='search_pubmed'),
    path('get_network_data', views.get_network_data, name='get_network_data'),  # 네트워크 데이터 제공
    path('main_select/', views.main_select, name='main_select'),
    path('disease_select/', views.disease_select, name='disease_select'),  # 단일 질병 선택 페이지
    path('single_disease_graph/', views.single_disease_graph, name='single_disease_graph'),
    path('sub_select/', views.sub_select, name='sub_select'),
    path('sub_disease_graph/', views.sub_disease_graph, name='sub_disease_graph'),
    path('check_disease_connection/', views.check_disease_connection, name='check_disease_connection'),
    path('get_connected_diseases/', views.get_connected_diseases, name='get_connected_diseases'),
    path('mypage/', views.mypage, name='mypage'),
    path('get_detail_info/', views.get_detail_info, name='get_detail_info'),
    path('save_graph/', views.save_graph, name='save_graph'),
    path('analysis_history/', views.analysis_history, name='analysis_history'),
]
