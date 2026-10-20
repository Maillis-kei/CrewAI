import argparse
import json
import os
import re
import sys
from crew import VideoPipelineCrew
from git_sync import push_scenes_to_github

def clean_and_validate_json(file_path: str = "scenes.json") -> bool:
    """LLM이 생성한 scenes.json 파일의 마크다운 백틱 제거 및 유효성 검증"""
    if not os.path.exists(file_path):
        print(f"[!] '{file_path}' 파일이 생성되지 않았습니다.")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # 마크다운 코드 블록 제거 (```json ... ```)
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if match:
        content = match.group(1).strip()

    try:
        data = json.loads(content)
        # 딕셔너리로 감싸진 경우(예: {"scenes": [...]}) 배열만 추출
        if isinstance(data, dict) and "scenes" in data:
            data = data["scenes"]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[✓] '{file_path}' 검증 및 포맷팅 완료 ({len(data)}개 씬 확인)")
        return True
    except json.JSONDecodeError as e:
        print(f"[!] JSON 파싱 오류: {e}")
        print("내용:\n", content)
        return False

def main():
    parser = argparse.ArgumentParser(description="CrewAI 기반 비디오 기획 및 Colab 연계 파이프라인")
    parser.add_argument(
        "-t", "--topic",
        type=str,
        default="사이버펑크 네온 도시를 질주하는 미래형 비행 바이크와 이를 추격하는 드론",
        help="영상 스토리 기획 주제"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="scenes.json 생성 후 GitHub에 자동으로 커밋 및 푸시"
    )

    args = parser.parse_args()

    print("="*60)
    print("🎬 CrewAI 영상 기획 멀티 에이전트 시작")
    print(f"📌 기획 주제: {args.topic}")
    print("="*60)

    # CrewAI 실행
    crew_instance = VideoPipelineCrew()
    result = crew_instance.crew().kickoff(inputs={"topic": args.topic})

    print("\n" + "="*60)
    print("✨ 멀티 에이전트 작업 완료")
    print("="*60)

    # scenes.json 파일 정제 및 검증
    is_valid = clean_and_validate_json("scenes.json")

    # GitHub 푸시 처리
    if is_valid and args.push:
        push_scenes_to_github("scenes.json", commit_message=f"Auto-generate scenes for: {args.topic[:30]}")
    elif is_valid:
        print("\n💡 알림: GitHub로 즉시 푸시하려면 다음 명령을 실행하세요:")
        print("   python git_sync.py")
        print("   (또는 실행 시 --push 플래그 사용: python main.py --push -t \"주제\")")

if __name__ == "__main__":
    main()
