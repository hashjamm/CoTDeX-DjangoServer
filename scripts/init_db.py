import pandas as pd
from sqlalchemy import create_engine
import os

# MariaDB 연결 URL
DB_URL = "mysql+pymysql://root:992828@localhost:3306/network0618"  # 사용자명, 비밀번호, 호스트, 포트, 데이터베이스 이름

# SQLAlchemy 엔진을 통해 MariaDB 연결
engine = create_engine(DB_URL)

# 각 Follow-up 데이터를 MariaDB에 저장
# for follow_up in range(1, 11):
#     file_path = f"media/final_result_{follow_up}.csv"  # 엑셀 파일 경로
#     if os.path.exists(file_path):
#         df = pd.read_csv(file_path)
#         # 데이터프레임을 SQL 테이블로 저장 (if_exists='replace'는 기존 테이블을 덮어씀)
#         df.to_sql(f"follow_up_{follow_up}", engine, if_exists="replace", index=False)
#         print(f"Data for follow-up {follow_up} saved to database.")
#     else:
#         print(f"File {file_path} does not exist.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# # node_pids_info.csv 저장
shape_file_path = os.path.join(BASE_DIR, "media", "node_pids_info.csv")
if os.path.exists(shape_file_path):
    shape_df = pd.read_csv(shape_file_path)

#     # 데이터 프레임 구조 확인
    print("Shape DataFrame Columns:", shape_df.columns)

    shape_table_name = "node_shapes"  # 테이블 이름
    shape_df.to_sql(shape_table_name, engine, if_exists="replace", index=False)
    print("Data for node shapes saved to database.")
else:
    print(f"File {shape_file_path} does not exist.")

# # pastel_colors.csv 저장
# pastel_color_file_path = f"media/pastel_colors.csv"  # pastel_colors.csv 파일 경로
# if os.path.exists(pastel_color_file_path):
#     pastel_df = pd.read_csv(pastel_color_file_path)




#     # 데이터 프레임 구조 확인
#     print("Pastel Colors DataFrame Columns:", pastel_df.columns)

#     pastel_table_name = "pastel_colors"  # 테이블 이름
#     pastel_df.to_sql(pastel_table_name, engine, if_exists="replace", index=False)
#     print("Data for pastel colors saved to database.")
# else:
#     print(f"File {pastel_color_file_path} does not exist.")


# file_path = "media/final_result_1.csv"

# # 파일이 존재하면 DB에 저장
# if os.path.exists(file_path):
#     df = pd.read_csv(file_path)
#     df.to_sql("follow_up_1", engine, if_exists="replace", index=False)
#     print("Data for final_result_1.csv saved to database.")
# else:
#     print("File final_result_1.csv does not exist.")