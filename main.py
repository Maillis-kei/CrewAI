import os
import sys
import json
import re
from crewai import Agent, Task, Crew, Process, LLM
from video_generator import generate_shorts_video

def extract_json_from_text(text):
    # Try finding json code block
    match = re.search(r'```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    # Try raw json array
    match = re.search(r'(\[\s*\{.*\}\s*\])', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    return None

def main():
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINIAPIKEY")
    )

    if not api_key:
        raise ValueError("GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")

    llm = LLM(
        model="gemini/gemini-3.8-flash",
        api_key=api_key,
        temperature=0.7
    )

    writer = Agent(
        role="유튜브 쇼츠 전문 작가 겸 비디오 디렉터",
        goal="주제에 맞춰 1분 분량의 유튜브 쇼츠 대본과 영상 씬(Scene)별 메타데이터를 구조화된 JSON 형식으로 생성한다.",
        backstory="수백만 조회수를 기록한 숏폼 전문 디렉터로서, 시선 끄는 훅과 핵심 팁 3가지, 명확한 콜투액션(CTA)을 완벽한 5개 씬으로 설계합니다.",
        llm=llm,
        verbose=True
    )

    task_prompt = """
주제: "아이패드로 코딩하는 방법"에 대한 1분 유튜브 쇼츠 비디오용 씬 목록을 JSON 배열로 작성하세요.

반드시 아래 5개 씬(INTRO, TIP 01, TIP 02, TIP 03, OUTRO)을 포함해야 하며, 정확히 아래 형식의 JSON 배열(Array)만 출력하세요:

```json
[
  {
    "badge": "INTRO",
    "title": "아이패드로 코딩이 불가능하다고?",
    "highlight": "맥북 당근하러 갈 준비하세요!",
    "narration": "아이패드는 유튜브 머신이다? 아직도 그런 소리 하시는 분들, 맥북 팔 준비하세요. 아이패드로 코딩하는 진짜 방법 딱 3가지만 알려드립니다!",
    "accent": "#f43f5e"
  },
  {
    "badge": "TIP 01",
    "title": "설치 필요 없는 웹 VS Code",
    "highlight": "사파리에서 vscode.dev 접속!",
    "narration": "첫 번째, 설치도 필요 없는 웹 VS Code입니다. 사파리 열고 브이스코드 닷 데브 딱 치면 여러분이 아는 그 VS Code가 그대로 열립니다. 깃허브만 연동하면 프론트엔드 작업은 3초 컷입니다.",
    "accent": "#0ea5e9"
  },
  {
    "badge": "TIP 02",
    "title": "풀스택 끝판왕: 클라우드 IDE",
    "highlight": "Gitpod & GitHub Codespaces",
    "narration": "두 번째, 서버 돌려야 하는 풀스택 개발자라면 깃팟이나 깃허브 코드스페이스를 쓰세요. 원격 서버를 빌려 쓰는 거라 빌드 속도가 구형 노트북보다 훨씬 빠르고 터미널도 완벽 지원됩니다.",
    "accent": "#a855f7"
  },
  {
    "badge": "TIP 03",
    "title": "오프라인 로컬 코딩 앱",
    "highlight": "Carnets & iSH 터미널",
    "narration": "세 번째, 비행기나 와이파이 없는 카페라면 파이썬 머신러닝 돌리는 카르네 앱이나 리눅스 터미널을 옮겨놓은 아이에스에이치(iSH) 앱을 쓰세요. 인터넷 없이도 코드가 바로 실행됩니다.",
    "accent": "#10b981"
  },
  {
    "badge": "OUTRO",
    "title": "가볍게 출근 & 구독 요청",
    "highlight": "댓글에 '아이패드'를 남겨주세요!",
    "narration": "이제 카페 갈 때 무거운 노트북 충전기 챙기지 마시고, 아이패드 하나만 들고 가볍게 출근하세요. 자세한 세팅법이 궁금하다면 구독 누르고 댓글에 아이패드라고 남겨주세요!",
    "accent": "#eab308"
  }
]
```
"""

    task1 = Task(
        description=task_prompt,
        expected_output="5개 씬의 badge, title, highlight, narration, accent 속성을 담은 유효한 JSON 배열 문자열",
        agent=writer
    )

    crew = Crew(
        agents=[writer],
        tasks=[task1],
        process=Process.sequential,
        verbose=True
    )

    print("CrewAI 에이전트가 쇼츠 대본 및 스토리보드 기획을 시작합니다...")
    raw_result = crew.kickoff()
    raw_text = str(raw_result)

    scenes = extract_json_from_text(raw_text)
    if not scenes or not isinstance(scenes, list) or len(scenes) == 0:
        print("LLM 응답에서 JSON 파싱이 원활하지 않아 최적화된 기본 스토리보드 씬으로 렌더링을 진행합니다.")
        scenes = [
            {
                "badge": "INTRO",
                "title": "아이패드로 코딩이 불가능하다고?",
                "highlight": "맥북 당근하러 갈 준비하세요!",
                "narration": "아이패드는 유튜브 머신이다? 아직도 그런 소리 하시는 분들, 맥북 팔 준비하세요. 아이패드로 코딩하는 진짜 방법 딱 3가지만 알려드립니다!",
                "accent": "#f43f5e"
            },
            {
                "badge": "TIP 01",
                "title": "설치 필요 없는 웹 VS Code",
                "highlight": "사파리에서 vscode.dev 접속!",
                "narration": "첫 번째, 설치도 필요 없는 웹 VS Code입니다. 사파리 열고 브이스코드 닷 데브 딱 치면 여러분이 아는 그 VS Code가 그대로 열립니다. 깃허브만 연동하면 작업은 3초 컷입니다.",
                "accent": "#0ea5e9"
            },
            {
                "badge": "TIP 02",
                "title": "풀스택 끝판왕: 클라우드 IDE",
                "highlight": "Gitpod & GitHub Codespaces",
                "narration": "두 번째, 서버 돌려야 하는 풀스택 개발자라면 깃팟이나 깃허브 코드스페이스를 쓰세요. 원격 서버를 빌려 쓰는 거라 빌드 속도가 노트북보다 훨씬 빠르고 터미널도 완벽 지원됩니다.",
                "accent": "#a855f7"
            },
            {
                "badge": "TIP 03",
                "title": "오프라인 로컬 코딩 앱",
                "highlight": "Carnets & iSH 터미널",
                "narration": "세 번째, 비행기나 와이파이 없는 카페라면 파이썬 머신러닝 돌리는 카르네 앱이나 리눅스 터미널을 옮겨놓은 아이에스에이치 앱을 쓰세요. 인터넷 없이도 코드가 바로 실행됩니다.",
                "accent": "#10b981"
            },
            {
                "badge": "OUTRO",
                "title": "가볍게 출근 & 구독 요청",
                "highlight": "댓글에 '아이패드'를 남겨주세요!",
                "narration": "이제 카페 갈 때 무거운 노트북 충전기 챙기지 마시고, 아이패드 하나만 들고 가볍게 출근하세요. 자세한 세팅법이 궁금하다면 구독 누르고 댓글에 아이패드라고 남겨주세요!",
                "accent": "#eab308"
            }
        ]

    # Save storyboard json (Google Flow 연동 겸용)
    with open("storyboard.json", "w", encoding="utf-8") as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)
    print("스토리보드 메타데이터가 storyboard.json에 저장되었습니다.")

    # Generate the actual YouTube Shorts video!
    output_video = "shorts_video.mp4"
    print("\n==================================================")
    print("🎬 [AI 비디오 자동 렌더링 시작]")
    print("==================================================")
    generate_shorts_video(scenes, output_video)
    print("\n==================================================")
    print(f"✅ 모든 작업 완료! 완성된 비디오: {output_video}")
    print("==================================================")

if __name__ == "__main__":
    main()
