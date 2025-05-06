import multiprocessing
import os

# 바인딩할 주소와 포트
bind = "0.0.0.0:5000"

# 워커 프로세스 수
workers = 1  # 작은 인스턴스에서는 하나로 제한

# 타임아웃 설정
timeout = 120

# 워커 클래스 - 비동기 작업을 위한 설정
worker_class = "sync"

# 각 워커당 스레드 수
threads = 2

# 시작 시 preload_app
preload_app = True

# 로깅 설정
loglevel = "info"
accesslog = "-"
errorlog = "-"

# 프로세스 이름 접두사
proc_name = "embedding_api"