import subprocess
import sys
import os

def run_git_command(command: list[str]) -> tuple[bool, str]:
    """Git 명령어 실행 도우미"""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def push_scenes_to_github(file_path: str = "scenes.json", commit_message: str = "Update scenes.json from CrewAI") -> bool:
    """생성된 scenes.json을 원격 GitHub 저장소에 푸시"""
    if not os.path.exists(file_path):
        print(f"[!] 오류: '{file_path}' 파일이 존재하지 않습니다.")
        return False

    print("\n" + "="*50)
    print("🚀 GitHub 자동 푸시 파이프라인 시작")
    print("="*50)

    # 1. git status 확인
    ok, current_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if not ok:
        print(f"[!] Git 저장소 확인 실패: {current_branch}")
        print("💡 안내: 먼저 'git init' 및 'git remote add origin <저장소_URL>'을 설정하세요.")
        return False

    # 2. git add
    print(f"[*] 변경 사항 스테이징: {file_path}")
    ok, out = run_git_command(["git", "add", file_path])
    if not ok:
        print(f"[!] git add 실패: {out}")
        return False

    # 3. git commit
    print(f"[*] 커밋 생성 중: '{commit_message}'")
    ok, out = run_git_command(["git", "commit", "-m", commit_message])
    if not ok:
        if "nothing to commit" in out or "working tree clean" in out:
            print("[*] 변경 사항이 없습니다 (이미 최신 커밋 상태).")
        else:
            print(f"[!] git commit 실패: {out}")
            return False
    else:
        print(f"[✓] 커밋 완료: {out}")

    # 4. git push
    print(f"[*] 원격 저장소로 푸시 중 (origin {current_branch})...")
    ok, out = run_git_command(["git", "push", "origin", current_branch])
    if not ok:
        print(f"[!] git push 실패: {out}")
        print("💡 팁: 원격 저장소 권한 및 SSH 키 또는 Personal Access Token을 확인하세요.")
        return False

    print(f"[✓] GitHub 푸시 성공! Colab에서 '!git pull'로 최신 scenes.json을 받을 수 있습니다.")
    return True

if __name__ == "__main__":
    push_scenes_to_github()
