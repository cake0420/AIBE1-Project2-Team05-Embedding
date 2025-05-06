from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer, util
import logging
from flask_cors import CORS, cross_origin

# 로그 설정
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Flask 앱
app = Flask(__name__)
# CORS 설정 - 모든 오리진 허용
from flask_cors import CORS

# SentenceTransformer 모델 로드 (한국어 지원)
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 태그 문자열 → 리스트로 전처리
def split_tags(tag_string):
    return [tag.strip() for tag in tag_string.split(',') if tag.strip()]

@app.route('/')
def hello():
    return 'Tag Similarity API is running.'


@app.route('/word-similarity', methods=['POST'])
@cross_origin(
    origins=["http://localhost:8080", "https://dev-linkup.duckdns.org"],
    methods=["POST"],
    allow_headers=["Content-Type"]
)
def word_similarity():
    data = request.get_json()
    print("Received data:", data)

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


        if not other_tags:
            continue

        try:
            other_embeds = model.encode(other_tags, convert_to_tensor=True)
            other_mean = other_embeds.mean(dim=0)
            similarity = util.cos_sim(query_mean, other_mean).item()
            if similarity > 0.5:
                results.append({
                    "areacode": areacode,
                    "areaName" : area_name,
                    "sigungucode" : sigungu_code,
                    "sigunguname" : sigunguname,
                    "nickname": nickname,
                    "profileTag": ", ".join(other_tags),
                    "profileImageUrl" : profile_image_url,
                    "similarity": similarity,
                })
        except Exception as e:
            results.append({
                "error": str(e)
            })

    # 유사도 높은 순 정렬
    sorted_results = sorted(results, key=lambda x: x.get("similarity", -1), reverse=True)
    return jsonify({
        "profileTag": my_tag,
        "results": sorted_results
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
