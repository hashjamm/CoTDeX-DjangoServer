import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.core.cache import cache
from sqlalchemy import create_engine
import json
import networkx as nx
from django.contrib.auth.decorators import login_required
import requests
from urllib.parse import quote
from django.views.decorators.http import require_GET
import os
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import UserGraph

# =============================================================================
# VISUALIZATION HOME
# =============================================================================

def visualization_home(request):
    """
    Follow-up 기간 입력 페이지를 렌더링합니다.
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        HttpResponse: visualization_home.html 템플릿 렌더링
    """
    return render(request, 'network/visualization_home.html')

# =============================================================================
# MAIN NETWORK FUNCTIONS
# =============================================================================

@login_required
def main_select(request):
    """
    메인 네트워크 선택 페이지를 렌더링합니다.
    로그인한 사용자만 접근 가능합니다.
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        HttpResponse: main_select.html 템플릿 렌더링
    """
    return render(request, 'network/main_select.html')

def get_db_connection():
    """
    MariaDB 데이터베이스 연결을 생성합니다.
    
    Returns:
        sqlalchemy.engine.Engine: MariaDB 연결 엔진
    """
    engine = create_engine("mysql+pymysql://cotdex_django_user:hanlab1234#@localhost/cotdex_db")
    return engine

@login_required
def graph_page(request):
    """
    Follow-up 데이터 선택 후 그래프를 표시하는 메인 네트워크 페이지입니다.
    
    기능:
    - 사용자가 설정한 파라미터로 네트워크 그래프 생성
    - 캐싱을 통한 성능 최적화
    - 노드 색상, 크기, 라벨 매핑
    - 엣지 가중치 계산
    
    Args:
        request: HTTP 요청 객체
            - follow_up: Follow-up 기간 (1-10)
            - rr_values_min: RR 최소값 (기본값: 0)
            - rr_values_max: RR 최대값 (기본값: 2)
            - chisq_p_values: Chi-square p-value 임계값 (기본값: 0.05)
            - fisher_p_values: Fisher p-value 임계값 (기본값: 0.05)
            
    Returns:
        HttpResponse: graph_page.html 템플릿 렌더링 또는 캐시된 데이터
        
    Raises:
        HttpResponseBadRequest: 잘못된 follow-up 값이 제공된 경우
    """
    follow_up = request.GET.get('follow_up')
    rr_min = float(request.GET.get('rr_values_min', 0))
    rr_max = float(request.GET.get('rr_values_max', 2))
    chisq_threshold = float(request.GET.get('chisq_p_values', 0.05))
    fisher_threshold = float(request.GET.get('fisher_p_values', 0.05))

    if not follow_up or not follow_up.isdigit():
        return HttpResponseBadRequest("Invalid follow-up period. Please provide a numeric value.")

    follow_up = int(follow_up)
    cache_key = f"graph_data_{follow_up}_{rr_min}_{rr_max}_{chisq_threshold}_{fisher_threshold}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return render(request, 'network/graph_page.html', cached_data)

    engine = get_db_connection()

    query = """
    SELECT * FROM edge_stat
    WHERE fu = %(follow_up)s
      AND log_rr_values BETWEEN %(rr_min)s AND %(rr_max)s
      AND adjusted_chisq_p_values <= %(chisq)s
      AND adjusted_fisher_p_values <= %(fisher)s
    """
    params = {
        'follow_up': follow_up,
        'rr_min': rr_min,
        'rr_max': rr_max,
        'chisq': chisq_threshold,
        'fisher': fisher_threshold
    }
    df = pd.read_sql_query(query, engine, params=params)

    node_query = """
    SELECT node_code AS code, width, height, Korean FROM node_base
    """
    disease_df = pd.read_sql_query(node_query, engine)

    pastel_colors = {
        'A': '#FFB3BA', 'B': '#FFDFBA', 'C': '#FFFFBA', 'D': '#BAFFBA',
        'E': '#BAE1FF', 'F': '#D1BAFF', 'G': '#FFBAFF', 'H': '#FFBABA',
        'I': '#FFEBBA', 'J': '#BAFFD8', 'K': '#D7FFBA', 'L': '#FFB6C1',
        'M':'#E3FFE3', 'N': '#BAF3FF', 'O': '#FFD1BA', 'P': '#D9A9FF', 'Q':'#F0F8FF',
        'R':'#FFCCCC','S':'#E2F3E2', 'T':'#D8E8FF', 'U':'#F8D0B3', 'V':'#B9C7FF',
        'W':'#F5B7B1','X':'#E9F7D2','Y':'#D6F3FF','Z':'#FFE0E0'
    }

    nodes = []
    edges = []
    unique_nodes = set()

    size_mapping = {
        row['code']: {
            'width': round(row['width'] * 80, 2) if pd.notna(row['width']) else 30,
            'height': round(row['height'] * 80, 2) if pd.notna(row['height']) else 30
        }
        for _, row in disease_df.iterrows()
    }

    label_mapping = {
        row['code']: row['Korean'] if pd.notna(row['Korean']) else row['code']
        for _, row in disease_df.iterrows()
    }

    # group_mapping = {
    #     row['code']: row['icd10'] if pd.notna(row['icd10']) else "기타"
    #     for _, row in disease_df.iterrows()
    # }

    for _, row in df.iterrows():
        cause = row['cause_abb']
        outcome = row['outcome_abb']
        raw_weight = row['rr_values']
        weight = max(1, min(10, round(raw_weight, 2)))

        for node in [cause, outcome]:
            if node not in unique_nodes:
                size = size_mapping.get(node, {'width': 30, 'height': 30})
                label = label_mapping.get(node, node)
                # group = group_mapping.get(node, "기타")
                color = pastel_colors.get(node[0], "#666")

                nodes.append({
                    "data": {
                        "id": node,
                        "label": label,
                        # "group": group,
                        "width": size['width'],
                        "height": size['height']
                    },
                    "style": {
                        "background-color": color
                    }
                })
                unique_nodes.add(node)

        edges.append({
            "data": {
                "source": cause,
                "target": outcome,
                "weight": weight
            }
        })

    disease_list = disease_df.to_dict(orient='records')
    # icd10_groups = sorted(set(d['icd10'] for d in disease_list if d['icd10']))

    context = {
        'follow_up': follow_up,
        'nodes': json.dumps(nodes),
        'edges': json.dumps(edges),
        'disease_list': disease_list,
        # 'icd10_groups': icd10_groups
    }

    cache.set(cache_key, context, timeout=3600)
    return render(request, 'network/graph_page.html', context)

@require_GET
def get_detail_info(request):
    """
    노드 또는 엣지의 상세 정보를 조회합니다.
    
    기능:
    - 노드 클릭 시: 해당 노드의 속성 정보 조회
    - 엣지 클릭 시: 해당 엣지의 속성 정보 조회
    - 성별, 연령, 지역, 직업별 분포 데이터 제공
    
    Args:
        request: HTTP 요청 객체
            - type: "node" 또는 "edge"
            - node_id: 노드 코드 (type="node"인 경우)
            - source: 시작 노드 코드 (type="edge"인 경우)
            - target: 도착 노드 코드 (type="edge"인 경우)
            - follow_up: Follow-up 기간 (type="edge"인 경우)
            
    Returns:
        JsonResponse: 노드/엣지 상세 정보 또는 오류 메시지
    """
    info_type = request.GET.get("type")

    if info_type == "edge":
        source = request.GET.get("source")
        target = request.GET.get("target")
        follow_up = request.GET.get("follow_up")

        if not (source and target and follow_up):
            return JsonResponse({"error": "필수 파라미터 누락"}, status=400)

        try:
            engine = get_db_connection()
            conn = engine.raw_connection()
            cursor = conn.cursor()

            query = """
                SELECT attribute_1, value_1, attribute_2, value_2, count
                FROM edge_attr
                WHERE fu = %s AND cause_abb = %s AND outcome_abb = %s
            """
            cursor.execute(query, (follow_up, source, target))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            data = {
                "sex": {}, "age": {}, "ctrb": {}, "sido": {},
                "sex_age": {}, "sex_ctrb": {}, "sex_sido": {}
            }

            for attr1, val1, attr2, val2, cnt in rows:
                if val1 is None:
                    continue
                val1 = str(int(float(val1)))  # 숫자 -> 정수 문자열 변환
                cnt = int(cnt)

                if attr2 is None or attr2.strip() == "":
                    if attr1 in data:
                        data[attr1][val1] = cnt
                else:
                    val2 = str(int(float(val2))) if val2 is not None else None
                    key = f"{attr1}_{attr2}"
                    if key not in data:
                        data[key] = {}
                    if val1 not in data[key]:
                        data[key][val1] = {}
                    data[key][val1][val2] = cnt

            return JsonResponse({"type": "edge", "data": data})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif info_type == "node":
        node_id = request.GET.get("node_id")
        if not node_id:
            return JsonResponse({"error": "node_id 누락"}, status=400)

        try:
            engine = get_db_connection()
            query = """
                SELECT attribute_1, value_1, attribute_2, value_2, count
                FROM node_attr
                WHERE node_code = %(code)s
            """
            df = pd.read_sql_query(query, engine, params={"code": node_id})

            data = {
                "sex": {}, "age": {}, "ctrb": {}, "sido": {},
                "sex_age": {}, "sex_ctrb": {}, "sex_sido": {}
            }

            for _, row in df.iterrows():
                attr1 = row['attribute_1']
                val1 = row['value_1']
                attr2 = row['attribute_2']
                val2 = row['value_2']
                cnt = row['count']

                if pd.isna(val1):
                    continue
                val1 = str(int(float(val1)))
                cnt = int(cnt)

                if pd.isna(attr2) or attr2.strip() == "":
                    if attr1 in data:
                        data[attr1][val1] = cnt
                else:
                    val2 = str(int(float(val2))) if pd.notna(val2) else None
                    key = f"{attr1}_{attr2}"
                    if key not in data:
                        data[key] = {}
                    if val1 not in data[key]:
                        data[key][val1] = {}
                    data[key][val1][val2] = cnt

            return JsonResponse({"type": "node", "data": data})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "지원되지 않는 type"}, status=400)


@require_GET
def search_pubmed(request):
    """
    PubMed에서 관련 논문을 검색합니다.
    
    기능:
    - 노드 클릭 시: 단일 질병 관련 논문 검색
    - 엣지 클릭 시: 두 질병 간의 관계 관련 논문 검색
    - PubMed ESearch와 ESummary API 활용
    - 최대 5개의 논문 결과 반환
    
    Args:
        request: HTTP 요청 객체
            - code: 질병 코드 (노드 클릭 시)
            - source: 시작 질병 코드 (엣지 클릭 시)
            - target: 도착 질병 코드 (엣지 클릭 시)
            
    Returns:
        JsonResponse: PubMed 논문 목록 또는 오류 메시지
    """
    code = request.GET.get('code')  # 노드 클릭 시 단일 질병
    source = request.GET.get('source')  # 엣지 클릭 시
    target = request.GET.get('target')

    try:
        engine = get_db_connection()

        # 노드 클릭 시: 단일 코드 검색
        if code:
            query = f"""
            SELECT node_code, Korean, English FROM node_base
            WHERE node_code = '{code}'
            """
            df = pd.read_sql_query(query, engine)
            if df.empty:
                return JsonResponse({"error": "해당 질병 코드의 영문명을 찾을 수 없습니다."}, status=404)

            english_term = df.iloc[0]['English']
            search_term = english_term

        # 엣지 클릭 시: source + target 검색
        elif source and target:
            query = f"""
            SELECT node_code, English FROM node_base
            WHERE node_code IN ('{source}', '{target}')
            """
            df = pd.read_sql_query(query, engine)
            if df.shape[0] != 2:
                return JsonResponse({"error": "source 또는 target 질병의 영문명이 없습니다."}, status=404)

            eng_source = df[df['node_code'] == source]['English'].values[0]
            eng_target = df[df['node_code'] == target]['English'].values[0]
            search_term = f"{eng_source} AND {eng_target}"
            print("source:", source)
            print("target:", target)
            print(df)  # SQL 결과 출력

        else:
            return JsonResponse({"error": "요청 파라미터 부족"}, status=400)

        engine.dispose()

    except Exception as e:
        return JsonResponse({"error": f"DB 오류: {str(e)}"}, status=500)

    # ✅ PubMed 검색 (ESearch)
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    esearch_params = {
        "db": "pubmed",
        "term": search_term,
        "retmode": "json",
        "retmax": 5
    }

    esearch_resp = requests.get(esearch_url, params=esearch_params)
    if esearch_resp.status_code != 200:
        return JsonResponse({"error": "PubMed 검색 실패"}, status=500)

    pmids = esearch_resp.json().get("esearchresult", {}).get("idlist", [])
    if not pmids:
        return JsonResponse({"results": []})

    # ✅ PubMed 상세 정보 (ESummary)
    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    esummary_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json"
    }

    esummary_resp = requests.get(esummary_url, params=esummary_params)
    if esummary_resp.status_code != 200:
        return JsonResponse({"error": "PubMed 요약 정보 실패"}, status=500)

    summaries = esummary_resp.json().get("result", {})
    results = []
    for pmid in pmids:
        paper = summaries.get(pmid)
        if paper:
            results.append({
                "title": paper.get("title", "제목 없음"),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })

    return JsonResponse({"results": results})



# 네트워크 데이터 제공 (JSON 형식)
def get_network_data(request):
    """
    CSV 파일에서 네트워크 데이터를 읽어 JSON 형태로 제공합니다.
    
    기능:
    - Follow-up 기간에 해당하는 CSV 파일 읽기
    - 노드와 엣지 데이터를 JSON 형태로 변환
    - 파일 존재 여부 확인
    
    Args:
        request: HTTP 요청 객체
            - follow_up: Follow-up 기간 (1-10)
            
    Returns:
        JsonResponse: 네트워크 데이터 또는 오류 메시지
    """
    follow_up = request.GET.get('follow_up')

    print(f"Follow-up period received: {follow_up}")

    if not follow_up or not follow_up.isdigit() or not (1 <= int(follow_up) <= 10):
        return JsonResponse({"error": "Invalid follow-up period. Please provide a value between 1 and 10."}, status=400)

    follow_up = int(follow_up)
    file_name = f"final_result_{follow_up}.csv"
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    print(f"Looking for file at: {file_path}")

    if not os.path.exists(file_path):
        return JsonResponse({"error": f"File for follow-up period {follow_up} does not exist."}, status=400)

    try:
        df = pd.read_csv(file_path)
        print(f"Dataframe loaded: {df.head()}")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    nodes = []
    edges = []
    unique_nodes = set()

    for _, row in df.iterrows():
        cause = row['cause_abb']
        outcome = row['outcome_abb']
        weight = row['rr_values']

        if cause not in unique_nodes:
            nodes.append({"data": {"id": cause}})
            unique_nodes.add(cause)
        if outcome not in unique_nodes:
            nodes.append({"data": {"id": outcome}})
            unique_nodes.add(outcome)

        edges.append({
            "data": {
                "source": cause,
                "target": outcome,
                "weight": weight
            }
        })

    data = {"nodes": nodes, "edges": edges}
    return JsonResponse(data)

# =============================================================================
# SINGLE NETWORK FUNCTIONS
# =============================================================================

@login_required
def disease_select(request):
    """
    단일 질병 선택 페이지를 렌더링합니다.
    
    기능:
    - 데이터베이스에서 모든 질병 코드와 한국어명 조회
    - 사용자가 단일 질병을 선택할 수 있는 인터페이스 제공
    - 데이터베이스 연결 오류 시 오류 메시지 표시
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        HttpResponse: disease_select.html 템플릿 렌더링
    """
    try:
        engine = get_db_connection()
        disease_query = "SELECT node_code as code, Korean FROM node_base"
        disease_df = pd.read_sql_query(disease_query, engine)
        engine.dispose()

        # context 데이터 구성
        context = {
            'disease_list': disease_df.to_dict(orient='records')
        }

        return render(request, 'network/disease_select.html', context)

    except Exception as e:
        # 오류 발생 시, 오류 메시지를 포함한 템플릿을 렌더링
        context = {
            'error_message': f"Database connection error: {str(e)}"
        }
        return render(request, 'network/disease_select.html', context)


def single_disease_graph(request):
    """
    단일 질병 그래프를 조회하고 생성합니다.
    
    기능:
    - 선택된 질병과 연결된 모든 노드 표시
    - 고정된 조건으로 네트워크 생성 (follow_up=1, rr=1.1-1.3, p-value=0.5)
    - 노드 색상, 크기, 라벨 매핑
    - AJAX 요청 시 JSON 응답, 일반 요청 시 템플릿 렌더링
    
    Args:
        request: HTTP 요청 객체
            - disease: 선택된 질병 코드
            - X-Requested-With: XMLHttpRequest (AJAX 요청 여부)
            
    Returns:
        JsonResponse 또는 HttpResponse: 그래프 데이터 또는 템플릿 렌더링
        
    Raises:
        JsonResponse: 질병 코드 누락 또는 오류 발생 시
    """
    disease_code = request.GET.get('disease')
    follow_up = 1
    rr_min = 1.1
    rr_max = 1.3
    chisq_p = 0.5
    fisher_p = 0.5

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not disease_code:
        return JsonResponse({"error": "질병 코드가 누락되었습니다."}, status=400)

    try:
        engine = get_db_connection()

        # edge 데이터 필터링
        query = """
        SELECT * FROM edge_stat
        WHERE fu = %(follow_up)s
          AND rr_values BETWEEN %(rr_min)s AND %(rr_max)s
          AND adjusted_chisq_p_values <= %(chisq)s
          AND adjusted_fisher_p_values <= %(fisher)s
          AND (cause_abb = %(disease_code)s OR outcome_abb = %(disease_code)s)
        """
        df = pd.read_sql_query(query, engine, params={
            "follow_up": follow_up,
            "rr_min": rr_min,
            "rr_max": rr_max,
            "chisq": chisq_p,
            "fisher": fisher_p,
            "disease_code": disease_code
        })

        # 노드 색상/크기 정보 조회
        disease_query = """
        SELECT node_code AS code, width, height, Korean FROM node_base
        """
        disease_df = pd.read_sql_query(disease_query, engine)
        engine.dispose()

        pastel_colors = {
            'A': '#FFB3BA', 'B': '#FFDFBA', 'C': '#FFFFBA', 'D': '#BAFFBA',
            'E': '#BAE1FF', 'F': '#D1BAFF', 'G': '#FFBAFF', 'H': '#FFBABA',
            'I': '#FFEBBA', 'J': '#BAFFD8', 'K': '#D7FFBA', 'L': '#FFB6C1',
            'M':'#E3FFE3', 'N': '#BAF3FF', 'O': '#FFD1BA', 'P': '#D9A9FF', 'Q':'#F0F8FF',
            'R':'#FFCCCC','S':'#E2F3E2', 'T':'#D8E8FF', 'U':'#F8D0B3', 'V':'#B9C7FF',
            'W':'#F5B7B1','X':'#E9F7D2','Y':'#D6F3FF','Z':'#FFE0E0'
        }

        size_mapping = {
            row['code']: {
                'width': round(row['width'] * 80, 2) if pd.notna(row['width']) else 30,
                'height': round(row['height'] * 80, 2) if pd.notna(row['height']) else 30
            }
            for _, row in disease_df.iterrows()
        }

        label_mapping = {
            row['code']: row['Korean'] if pd.notna(row['Korean']) else row['code']
            for _, row in disease_df.iterrows()
        }

        nodes, edges, unique_nodes, node_names = [], [], set(), []

        for _, row in df.iterrows():
            for node_code in [row['cause_abb'], row['outcome_abb']]:
                if node_code not in unique_nodes:
                    size = size_mapping.get(node_code, {'width': 30, 'height': 30})
                    label = label_mapping.get(node_code, node_code)
                    color = pastel_colors.get(node_code[0], '#666')

                    node_data = {
                        "data": {
                            "id": node_code,
                            "label": label,
                            "width": size['width'],
                            "height": size['height']
                        },
                        "style": {
                            "background-color": color
                        }
                    }
                    nodes.append(node_data)
                    unique_nodes.add(node_code)
                    node_names.append(f"{node_code} ({label})")

            edges.append({"data": {
                "source": row['cause_abb'],
                "target": row['outcome_abb'],
                "weight": row['rr_values']
            }})

        if is_ajax:
            return JsonResponse({"nodes": nodes, "edges": edges, "node_names": node_names})

        context = {
            'disease_code': disease_code,
            'follow_up': follow_up,
            'rr_min': rr_min,
            'rr_max': rr_max,
            'chisq_p': chisq_p,
            'fisher_p': fisher_p,
            'nodes': json.dumps(nodes),
            'edges': json.dumps(edges),
            'node_names': node_names
        }
        return render(request, 'network/single_disease_graph.html', context)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# =============================================================================
# SUB NETWORK FUNCTIONS
# =============================================================================

@login_required
def sub_select(request):
    """
    Sub network 질병 선택 페이지를 렌더링합니다.
    
    기능:
    - 데이터베이스에서 모든 질병 코드와 한국어명 조회
    - 사용자가 여러 질병을 선택할 수 있는 인터페이스 제공
    - JSON 형태로 질병 목록 전달
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        HttpResponse: sub_select.html 템플릿 렌더링
    """
    try:
        engine = get_db_connection()
        query = "SELECT node_code, Korean FROM node_base"
        df = pd.read_sql_query(query, engine)
        engine.dispose()

        disease_list = df.to_dict(orient='records')

        return render(request, 'network/sub_select.html', {
            'disease_list': json.dumps(disease_list, ensure_ascii=False)
        })

    except Exception as e:
        return render(request, 'network/sub_select.html', {
            'disease_list': [],
            'error_message': str(e)
        })



@login_required
def sub_disease_graph(request):
    """
    선택된 질병들의 Sub network 그래프를 생성합니다.
    
    기능:
    - 선택된 질병들이 공통으로 연결된 노드들만 표시
    - 단일 질병 선택 시: 해당 질병과 연결된 모든 노드 표시
    - 다중 질병 선택 시: 선택된 질병들이 공통으로 연결된 노드들만 표시
    - 선택된 질병들은 좌우 고정 위치에 배치
    - AJAX 요청 시 JSON 응답, 일반 요청 시 템플릿 렌더링
    
    Args:
        request: HTTP 요청 객체
            - diseases: 선택된 질병 코드들 (콤마 구분)
            - follow_up: Follow-up 기간 (기본값: 1)
            - rr_values_min: RR 최소값 (기본값: 1.1)
            - rr_values_max: RR 최대값 (기본값: 1.3)
            - chisq_p_values: Chi-square p-value 임계값 (기본값: 0.5)
            - fisher_p_values: Fisher p-value 임계값 (기본값: 0.5)
            - X-Requested-With: XMLHttpRequest (AJAX 요청 여부)
            
    Returns:
        JsonResponse 또는 HttpResponse: 그래프 데이터 또는 템플릿 렌더링
        
    Raises:
        JsonResponse: 질병 미선택 또는 오류 발생 시
    """
    selected_codes = request.GET.get('diseases')
    follow_up = int(request.GET.get('follow_up', 1))
    rr_min = float(request.GET.get('rr_values_min', 1.1))
    rr_max = float(request.GET.get('rr_values_max', 1.3))
    chisq_p = float(request.GET.get('chisq_p_values', 0.5))
    fisher_p = float(request.GET.get('fisher_p_values', 0.5))

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not selected_codes:
        return JsonResponse({"error": "선택된 질병이 없습니다."}, status=400)

    code_list = selected_codes.split(',')

    try:
        engine = get_db_connection()

        # edge 데이터 필터링
        query = """
        SELECT * FROM edge_stat
        WHERE fu = %(follow_up)s
          AND rr_values BETWEEN %(rr_min)s AND %(rr_max)s
          AND adjusted_chisq_p_values <= %(chisq)s
          AND adjusted_fisher_p_values <= %(fisher)s
        """
        df = pd.read_sql_query(query, engine, params={
            "follow_up": follow_up,
            "rr_min": rr_min,
            "rr_max": rr_max,
            "chisq": chisq_p,
            "fisher": fisher_p
        })

        # 공통 연결 노드 계산
        if len(code_list) == 1:
            connected = set(df[df['cause_abb'].isin(code_list)]['outcome_abb']) | \
                        set(df[df['outcome_abb'].isin(code_list)]['cause_abb'])
            target_nodes = connected | set(code_list)
        else:
            connected_sets = []
            for code in code_list:
                targets = set(df[df['cause_abb'] == code]['outcome_abb']) | \
                          set(df[df['outcome_abb'] == code]['cause_abb'])
                connected_sets.append(targets)
            common_connected = set.intersection(*connected_sets)
            target_nodes = common_connected | set(code_list)

        df = df[(df['cause_abb'].isin(target_nodes)) & (df['outcome_abb'].isin(target_nodes))]

        # 노드 색상/크기 정보 조회
        disease_query = """
        SELECT node_code AS code, width, height, Korean FROM node_base
        """
        disease_df = pd.read_sql_query(disease_query, engine)
        engine.dispose()

        pastel_colors = {
            'A': '#FFB3BA', 'B': '#FFDFBA', 'C': '#FFFFBA', 'D': '#BAFFBA',
            'E': '#BAE1FF', 'F': '#D1BAFF', 'G': '#FFBAFF', 'H': '#FFBABA',
            'I': '#FFEBBA', 'J': '#BAFFD8', 'K': '#D7FFBA', 'L': '#FFB6C1',
            'M':'#E3FFE3', 'N': '#BAF3FF', 'O': '#FFD1BA', 'P': '#D9A9FF', 'Q':'#F0F8FF',
            'R':'#FFCCCC','S':'#E2F3E2', 'T':'#D8E8FF', 'U':'#F8D0B3', 'V':'#B9C7FF',
            'W':'#F5B7B1','X':'#E9F7D2','Y':'#D6F3FF','Z':'#FFE0E0'
        }

        size_mapping = {
            row['code']: {
                'width': round(row['width'] * 80, 2) if pd.notna(row['width']) else 30,
                'height': round(row['height'] * 80, 2) if pd.notna(row['height']) else 30
            }
            for _, row in disease_df.iterrows()
        }

        label_mapping = {
            row['code']: row['Korean'] if pd.notna(row['Korean']) else row['code']
            for _, row in disease_df.iterrows()
        }

        nodes, edges, unique_nodes, node_names = [], [], set(), []

        for _, row in df.iterrows():
            for node_code in [row['cause_abb'], row['outcome_abb']]:
                if node_code not in unique_nodes:
                    size = size_mapping.get(node_code, {'width': 30, 'height': 30})
                    label = label_mapping.get(node_code, node_code)
                    color = pastel_colors.get(node_code[0], '#666')

                    node_data = {
                        "data": {
                            "id": node_code,
                            "label": label,
                            "width": size['width'],
                            "height": size['height']
                        },
                        "style": {
                            "background-color": color
                        }
                    }

                    # 선택된 질병은 좌우 고정 위치 설정
                    if node_code == code_list[0]:
                        node_data["position"] = {"x": 100, "y": 300}
                        node_data["locked"] = True
                    elif node_code == code_list[-1]:
                        node_data["position"] = {"x": 1000, "y": 300}
                        node_data["locked"] = True

                    nodes.append(node_data)
                    unique_nodes.add(node_code)
                    node_names.append(f"{node_code} ({label})")

            edges.append({"data": {
                "source": row['cause_abb'],
                "target": row['outcome_abb'],
                "weight": row['rr_values']
            }})

        if is_ajax:
            return JsonResponse({"nodes": nodes, "edges": edges, "node_names": node_names})

        context = {
            'selected_codes': selected_codes,
            'follow_up': follow_up,
            'rr_min': rr_min,
            'rr_max': rr_max,
            'chisq_p': chisq_p,
            'fisher_p': fisher_p,
            'nodes': json.dumps(nodes),
            'edges': json.dumps(edges),
            'node_names': node_names
        }
        return render(request, 'network/sub_disease_graph.html', context)

    except Exception as e:
        print("❌ sub_network_graph 에러:", str(e))
        return JsonResponse({"error": str(e)}, status=500)



def check_disease_connection(request):
    """
    선택된 질병들의 연결성을 확인합니다.
    
    기능:
    - 선택된 질병들이 하나의 connected component 내에 있는지 확인
    - NetworkX를 사용한 그래프 분석
    - 연결 가능한 경우 적절한 조건값 반환
    
    Args:
        request: HTTP 요청 객체
            - diseases: 선택된 질병 코드들 (콤마 구분)
            
    Returns:
        JsonResponse: 연결성 결과 및 조건값 또는 오류 메시지
    """
    selected_codes = request.GET.get("diseases", "")
    code_list = selected_codes.split(",")

    if not selected_codes or len(code_list) < 2:
        return JsonResponse({"connected": False})

    try:
        engine = get_db_connection()
        query = """
            SELECT cause_abb, outcome_abb
            FROM edge_stat
            WHERE fu = 2
              AND rr_values BETWEEN 1.2 AND 1.3
              AND adjusted_chisq_p_values <= 0.5
              AND adjusted_fisher_p_values <= 0.5
        """
        df = pd.read_sql_query(query, engine)
        engine.dispose()

        # 방향 없는 그래프 생성
        G = nx.Graph()
        G.add_edges_from(zip(df["cause_abb"], df["outcome_abb"]))

        # 모든 선택 질병이 하나의 connected component 내에 있는지 확인
        all_connected = all(
            nx.has_path(G, source=a, target=b)
            for i, a in enumerate(code_list)
            for b in code_list[i+1:]
        )

        if all_connected:
            return JsonResponse({
                "connected": True,
                "follow_up": 2,
                "rr_min": 1.2,
                "rr_max": 1.3,
                "chisq_max": 0.5,
                "fisher_max": 0.5
            })
        else:
            return JsonResponse({"connected": False})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def get_connected_diseases(request):
    """
    특정 질병과 연결된 질병들을 조회합니다.
    
    기능:
    - 주어진 질병과 직접 연결된 모든 질병 조회
    - 고정된 조건으로 연결성 분석
    - 질병 코드 리스트 반환
    
    Args:
        request: HTTP 요청 객체
            - disease: 질병 코드
            
    Returns:
        JsonResponse: 연결된 질병 코드 리스트 또는 오류 메시지
    """
    disease = request.GET.get('disease')
    follow_up = 1
    rr_min = 1.1
    rr_max = 1.3
    p_value = 0.5

    if not disease:
        return JsonResponse({"connected": []})

    try:
        engine = get_db_connection()
        query = f"""
        SELECT cause_abb, outcome_abb
        FROM follow_up_{follow_up}
        WHERE 
          fu={follow_up}
          rr_values BETWEEN {rr_min} AND {rr_max}
          AND adjusted_chisq_p_values <= {p_value}
          AND adjusted_fisher_p_values <= {p_value}
          AND (cause_abb = '{disease}' OR outcome_abb = '{disease}')
        """
        df = pd.read_sql_query(query, engine)
        engine.dispose()

        connected = set(df['cause_abb'].tolist() + df['outcome_abb'].tolist())
        connected.add(disease)  # 선택 질병도 포함
        return JsonResponse({"connected": list(connected)})
    except Exception as e:
        return JsonResponse({"connected": [], "error": str(e)})

# =============================================================================
# USER MANAGEMENT FUNCTIONS
# =============================================================================

@login_required
def mypage(request):
    """
    사용자 마이페이지를 렌더링합니다.
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        HttpResponse: mypage.html 템플릿 렌더링
    """
    return render(request, 'network/mypage.html')

@csrf_exempt
@login_required
def save_graph(request):
    """
    사용자가 생성한 그래프를 데이터베이스에 저장합니다.
    
    기능:
    - 그래프 설정 정보를 UserGraph 모델에 저장
    - 제목, 메모, 파라미터 값들 저장
    - 그래프 타입 정보를 메모에 포함하여 저장
    
    Args:
        request: HTTP 요청 객체 (POST)
            - title: 그래프 제목
            - memo: 그래프 메모
            - fu: Follow-up 기간
            - rr_min: RR 최소값
            - rr_max: RR 최대값
            - chisq_p: Chi-square p-value
            - fisher_p: Fisher p-value
            - disease_names: 질병 이름들
            - graph_type: 그래프 타입 (single, sub, main)
            
    Returns:
        JsonResponse: 저장 성공/실패 결과
    """
    if request.method == 'POST':
        user = request.user
        data = request.POST
        title = data.get('title', '')
        memo = data.get('memo', '')
        fu = data.get('fu')
        rr_min = data.get('rr_min')
        rr_max = data.get('rr_max')
        chisq_p = data.get('chisq_p')
        fisher_p = data.get('fisher_p')
        disease_names = data.get('disease_names', '')
        graph_type = data.get('graph_type', 'single')  # 'single', 'sub', 'main' 중 하나

        # 필수값 체크
        if not (fu and rr_min and rr_max and chisq_p and fisher_p and disease_names and graph_type):
            return JsonResponse({'success': False, 'error': '필수값 누락'}, status=400)

        # graph_type을 memo에 함께 저장 (추후 모델에 필드 추가 권장)
        memo_full = f"{memo}\n[그래프타입:{graph_type}]"

        graph = UserGraph.objects.create(
            user=user,
            title=title,
            memo=memo_full,
            fu=fu,
            rr_min=rr_min,
            rr_max=rr_max,
            chisq_p=chisq_p,
            fisher_p=fisher_p,
            disease_names=disease_names
        )
        return JsonResponse({'success': True, 'graph_id': graph.id})
    else:
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용'}, status=405)

@login_required
def analysis_history(request):
    """
    사용자의 그래프 분석 히스토리를 표시합니다.
    
    기능:
    - 현재 로그인한 사용자의 모든 저장된 그래프 조회
    - 그래프 타입 정보를 메모에서 파싱
    - 생성일 기준 내림차순 정렬
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        HttpResponse: analysis_history.html 템플릿 렌더링
    """
    user = request.user
    graphs = UserGraph.objects.filter(user=user).order_by('-created_at')
    # graph_type은 memo에 [그래프타입:xxx] 형태로 저장되어 있으므로 파싱
    graph_list = []
    for g in graphs:
        graph_type = 'single'
        if '[그래프타입:' in g.memo:
            try:
                graph_type = g.memo.split('[그래프타입:')[1].split(']')[0]
            except:
                graph_type = 'single'
        graph_list.append({
            'id': g.id,
            'title': g.title,
            'memo': g.memo.split('\n[그래프타입:')[0],
            'created_at': g.created_at,
            'graph_type': graph_type,
            'fu': g.fu,
            'rr_min': g.rr_min,
            'rr_max': g.rr_max,
            'chisq_p': g.chisq_p,
            'fisher_p': g.fisher_p,
            'disease_names': g.disease_names
        })
    return render(request, 'network/analysis_history.html', {'graph_list': graph_list})
