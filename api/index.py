from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer, util
import logging
import os
import threading
import time
import sys
from flask_cors import CORS, cross_origin

# 로그 설정
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 시작 정보 로깅
logger.info("API 서버 초기화 중...")
logger.info(f"Python 버전: {sys.version}")
logger.info(f"환경 변수: PORT={os.environ.get('PORT', '5000')}, HOST={os.environ.get('HOST', '0.0.0.0')}")

# Flask 앱
app = Flask(__name__)
# CORS 설정
CORS(app)

# 글로벌 변수로 모델 선언
model = None
model_loaded = False


# 백그라운드에서 모델 로드
def load_model_in_background():
    global model, model_loaded
    try:
        logger.info("모델 로딩 시작...")
        start_time = time.time()
        model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        model_loaded = True
        end_time = time.time()
        logger.info(f"모델 로딩 완료! 소요 시간: {end_time - start_time:.2f}초")
    except Exception as e:
        logger.error(f"모델 로딩 실패: {str(e)}")


# 백그라운드 스레드에서 모델 로드 시작
threading.Thread(target=load_model_in_background, daemon=True).start()


# 태그 문자열 → 리스트로 전처리
def split_tags(tag_string):
    return [tag.strip() for tag in tag_string.split(',') if tag.strip()]


@app.route('/')
def hello():
    if not model_loaded:
        status = "모델 로딩 중... 잠시 후 다시 시도해주세요."
    else:
        status = "Tag Similarity API가 실행 중입니다."
    return jsonify({"status": status})


@app.route('/word-similarity', methods=['POST'])
@cross_origin(
    origins=["http://localhost:8080", "https://dev-linkup.duckdns.org"],
    methods=["POST"],
    allow_headers=["Content-Type"]
)
def word_similarity():
    # 모델이 로드되지 않았다면 대기 요청
    if not model_loaded:
        return jsonify({'error': '모델 로딩 중입니다. 잠시 후 다시 시도해주세요.'}), 503

    data = request.get_json()
    logger.info(f"Received data: {data}")

    my_tag = data.get('profileTag')
    other_profiles = data.get('otherProfiles')

    if not my_tag or not other_profiles:
        return jsonify({'error': 'profileTag 또는 otherProfiles가 누락되었습니다.'}), 400

    # Ensure other_profiles is a list
    if not isinstance(other_profiles, list):
        # If it's a dictionary, wrap it in a list
        if isinstance(other_profiles, dict):
            other_profiles = [other_profiles]
        else:
            return jsonify({'error': 'otherProfiles must be a list or a dictionary'}), 400

    # 내 태그 임베딩
    query_tags = split_tags(my_tag)
    if not query_tags:
        return jsonify({'error': 'profileTag가 비어 있습니다.'}), 400

    try:
        query_embeds = model.encode(query_tags, convert_to_tensor=True)
        query_mean = query_embeds.mean(dim=0)  # 평균 벡터

        results = []
        for profile in other_profiles:
            raw_tag = profile.get("profileTag", "")
            other_tags = split_tags(raw_tag)
            profile_image_url = profile.get("profileImageUrl")
            areacode = profile.get("areacode")
            area_name = profile.get("areaName")
            sigungu_code = profile.get("sigungucode")
            sigunguname = profile.get("sigunguname")
            nickname = profile.get('nickname')
            contactLink = profile.get("contactLink")

            if not other_tags:
                continue

            try:
                other_embeds = model.encode(other_tags, convert_to_tensor=True)
                other_mean = other_embeds.mean(dim=0)
                similarity = util.cos_sim(query_mean, other_mean).item()
                if similarity > 0.5:
                    results.append({
                        "areacode": areacode,
                        "areaName": area_name,
                        "sigungucode": sigungu_code,
                        "sigunguname": sigunguname,
                        "nickname": nickname,
                        "profileTag": ", ".join(other_tags),
                        "profileImageUrl": profile_image_url,
                        "similarity": similarity,
                        "contactLink" : contactLink,
                    })
            except Exception as e:
                logger.error(f"Error processing profile: {str(e)}")
                results.append({
                    "error": str(e)
                })

        # 유사도 높은 순 정렬
        sorted_results = sorted(results, key=lambda x: x.get("similarity", -1), reverse=True)
        return jsonify({
            "profileTag": my_tag,
            "results": sorted_results
        })
    except Exception as e:
        logger.error(f"Error in word_similarity: {str(e)}")
        return jsonify({'error': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500


if __name__ == '__main__':
    # 환경 변수에서 포트 설정 가져오기 (기본값 5000)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')

    logger.info(f"Flask 앱을 {host}:{port}에서 시작합니다...")
    app.run(debug=False, host=host, port=port, threaded=True)

# Fly.io에서 필요한 변수
application = app