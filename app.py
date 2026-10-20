import streamlit as st
import json
import os
import subprocess
from crew import VideoPipelineCrew
from git_sync import push_scenes_to_github
from main import clean_and_validate_json

st.set_page_config(
    page_title="AI 비디오 스튜디오 (CrewAI x Colab)",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (세련된 다크 테마 & 카드 UI)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .camera-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 4px solid #38bdf8;
    }
    .scene-box {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# 카메라 구도 프리셋 라이브러리
CAMERA_PRESETS = [
    {
        "name": "🚁 FPV 초고속 드론 추격 (FPV Drone Chase)",
        "keyword": "fast-paced FPV drone chase shot, motion blur, dynamic tracking",
        "desc": "피사체의 뒤나 옆을 초고속으로 추격하며 짜릿한 속도감과 박진감을 연출합니다."
    },
    {
        "name": "🎥 시네마틱 슬로우 패닝 (Slow Cinematic Pan)",
        "keyword": "slow smooth cinematic panning shot, highly detailed, steady camera",
        "desc": "카메라가 부드럽게 좌우로 회전하며 웅장한 배경과 세계관의 디테일을 보여줍니다."
    },
    {
        "name": "🔍 극단적 클로즈업 (Extreme Close-Up)",
        "keyword": "extreme close-up shot, sharp focus on eyes, micro details, shallow depth of field",
        "desc": "인물의 눈동자, 굳게 다문 입술, 기계의 미세한 부품 등 극적인 감정을 포착합니다."
    },
    {
        "name": "🐜 로우 앵글 웜즈아이 뷰 (Low-Angle Worm's Eye)",
        "keyword": "dramatic low-angle shot, worm's-eye view, towering perspective, epic scale",
        "desc": "바닥에서 위를 올려다보는 구도로 피사체를 압도적이고 거대하게 만듭니다."
    },
    {
        "name": "🦅 버드아이 탑다운 뷰 (Bird's Eye Top-Down)",
        "keyword": "high bird's eye view, top-down drone perspective, expansive landscape",
        "desc": "수직 상공에서 내려다보는 구도로 신비롭고 기하학적인 장면을 구성합니다."
    },
    {
        "name": "🔄 360도 오빗 회전 (360-Degree Orbit Shot)",
        "keyword": "360-degree rotating orbit shot around the subject, volumetric lighting",
        "desc": "정지하거나 움직이는 피사체 주변을 360도로 돌며 입체감을 극대화합니다."
    },
    {
        "name": "🏃 다이내믹 트래킹 샷 (Dynamic Tracking Shot)",
        "keyword": "side tracking shot moving at the same speed as subject, smooth motion",
        "desc": "달리는 인물이나 질주하는 차량을 일정한 거리에서 옆으로 따라가는 영화적 연출입니다."
    },
    {
        "name": "🌌 돌리 줌 / 버티고 효과 (Dolly Zoom / Vertigo)",
        "keyword": "dramatic dolly zoom effect, vertigo distortion, background warping",
        "desc": "피사체 크기는 유지되면서 배경만 급격히 왜곡되어 충격과 반전을 표현합니다."
    },
    {
        "name": "📐 더치 앵글 (Dutch / Tilted Angle)",
        "keyword": "tilted dutch angle, tense atmosphere, dynamic diagonal composition",
        "desc": "카메라를 비스듬히 기울여 불안감, 스릴, 위험한 분위기를 전달합니다."
    }
]

# 사이드바: 카메라 구도 예제 스크롤 탐색기
with st.sidebar:
    st.markdown("### 🎥 카메라 구도 예제 도감")
    st.markdown("원하는 연출을 클릭하여 씬 기획에 반영하세요.")
    
    selected_camera_keywords = []
    with st.container(height=500):
        for idx, preset in enumerate(CAMERA_PRESETS):
            checked = st.checkbox(f"**{preset['name']}**", key=f"cam_{idx}")
            st.caption(preset["desc"])
            st.markdown(f"`{preset['keyword']}`")
            st.divider()
            if checked:
                selected_camera_keywords.append(preset["keyword"])

# 메인 헤더
st.markdown("<div class='main-title'>🎬 AI 영상 기획 & Colab 렌더링 스튜디오</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>아이디어와 필수 요소를 입력하면 CrewAI가 시각적 일관성이 유지된 비디오 프롬프트를 자동 가공합니다.</div>", unsafe_allow_html=True)

# 1. 입력 영역 (2컬럼)
col1, col2 = st.columns([1.2, 1])

with col1:
    topic = st.text_input(
        "📌 영상 전체 주제 (Topic)",
        value="사이버펑크 네온 도시를 질주하는 미래형 비행 바이크와 이를 추격하는 자율 드론",
        help="영상 전체의 큰 스토리 콘셉트를 입력하세요."
    )
    
    key_elements = st.text_area(
        "✨ 영상에 꼭 담아야 할 핵심 요소 (Key Elements)",
        value="1. 빨간색 네온 가죽 자켓을 입은 여성 라이더 (모든 씬 외형 고정)\n2. 빗물에 젖은 아스팔트에 반사되는 보라색 네온사인\n3. 바이크 후방의 시안(Cyan) 색상 제트 배기 화염\n4. 붉은색 스캔 레이저를 발사하며 급강하하는 드론",
        height=130,
        help="주인공의 외형, 의상, 색감 등 씬 전체에서 유지되어야 할 일관성 요소들을 적어주세요."
    )

with col2:
    mood = st.selectbox(
        "🎨 영상 분위기 및 톤앤매너",
        ["시네마틱 실사 SF (Photorealistic 8K, Anamorphic Lens)", 
         "다크 느와르 사이버펑크 (Neon Noir, Heavy Rain, Fog)", 
         "스튜디오 지브리 애니메이션 (Ghibli Style, Vibrant Colors, Hand-drawn)", 
         "에픽 판타지 영화 (Unreal Engine 5, Volumetric God Rays, Masterpiece)"]
    )
    
    num_scenes = st.slider("🎬 기획할 씬(Scene) 개수", min_value=2, max_value=5, value=3)
    
    if selected_camera_keywords:
        st.success(f"선택된 카메라 구도: {len(selected_camera_keywords)}개 적용됨")
    else:
        st.info("💡 좌측 사이드바에서 원하는 카메라 구도를 선택하면 자동으로 반영됩니다.")

st.markdown("---")

# 2. AI 가공 실행 버튼
if st.button("🚀 AI 멀티 에이전트로 씬 기획 및 프롬프트 가공 시작", type="primary", use_container_width=True):
    # 합성 프롬프트 생성
    camera_instruction = f"반드시 다음 카메라 구도들을 각 씬에 분배하여 적용하세요: {', '.join(selected_camera_keywords)}" if selected_camera_keywords else "다양한 시네마틱 카메라 구도(와이드, 클로즈업, 트래킹)를 적용하세요."
    
    full_prompt = (
        f"영상 주제: {topic}\n"
        f"스타일/분위기: {mood}\n"
        f"반드시 포함해야 할 시각적 일관성 요소(모든 씬 앵커 고정):\n{key_elements}\n"
        f"카메라 디렉팅: {camera_instruction}\n"
        f"총 {num_scenes}개의 연속된 씬으로 분할하여 기획하세요."
    )
    
    with st.spinner("🤖 CrewAI 에이전트들이 스토리보드를 구성하고 AnimateDiff 프롬프트를 최적화하는 중입니다... (약 20~40초 소요)"):
        try:
            crew_instance = VideoPipelineCrew()
            crew_instance.crew().kickoff(inputs={"topic": full_prompt})
            clean_and_validate_json("scenes.json")
            st.session_state["scenes_generated"] = True
            st.success("🎉 AI 기획 및 scenes.json 가공이 완료되었습니다!")
        except Exception as e:
            st.error(f"기획 중 오류 발생: {e}")

# 3. 씬 미리보기 및 편집 섹션
if os.path.exists("scenes.json"):
    st.markdown("### 📋 생성된 씬 목록 (검토 및 수정)")
    
    with open("scenes.json", "r", encoding="utf-8") as f:
        scenes_data = json.load(f)
    
    updated_scenes = []
    for idx, sc in enumerate(scenes_data):
        with st.expander(f"🎬 씬 {sc.get('scene_id', idx+1)}: {sc.get('file_name', f'scene_{idx+1}.mp4')}", expanded=True):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                prompt_val = st.text_area(f"영문 프롬프트 (Scene {sc.get('scene_id', idx+1)})", value=sc.get("prompt", ""), height=80, key=f"prompt_{idx}")
                neg_val = st.text_input(f"네거티브 프롬프트", value=sc.get("negative_prompt", "blurry, deformed, flickering, low quality"), key=f"neg_{idx}")
            with col_b:
                frames_val = st.number_input(f"프레임 수", value=sc.get("num_frames", 16), step=8, key=f"frames_{idx}")
                steps_val = st.number_input(f"추론 스텝", value=sc.get("num_inference_steps", 25), step=5, key=f"steps_{idx}")
            
            sc["prompt"] = prompt_val
            sc["negative_prompt"] = neg_val
            sc["num_frames"] = frames_val
            sc["num_inference_steps"] = steps_val
            updated_scenes.append(sc)

    # 수정사항 저장
    if st.button("💾 수정한 씬 프롬프트 저장하기"):
        with open("scenes.json", "w", encoding="utf-8") as f:
            json.dump(updated_scenes, f, indent=2, ensure_ascii=False)
        st.success("✓ scenes.json 파일에 수정사항이 저장되었습니다!")

    st.markdown("---")

    # 4. GitHub 푸시 및 Colab 연결 버튼
    col_git, col_colab = st.columns(2)
    
    with col_git:
        if st.button("📤 GitHub로 scenes.json 자동 푸시", type="secondary", use_container_width=True):
            with st.spinner("GitHub 원격 저장소로 푸시 중..."):
                ok = push_scenes_to_github("scenes.json", commit_message=f"Update scenes for: {topic[:30]}")
                if ok:
                    st.success("✓ GitHub에 성공적으로 푸시되었습니다! 이제 Colab에서 렌더링을 시작하세요.")
                else:
                    st.error("GitHub 푸시 실패. 터미널 권한을 확인하세요.")

    with col_colab:
        colab_url = "https://colab.research.google.com/github/Maillis-kei/CrewAI/blob/main/colab_runner.ipynb"
        st.link_button("🚀 Google Colab 열기 (GPU 렌더링)", colab_url, use_container_width=True)
