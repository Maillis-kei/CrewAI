import os
from crewai import Agent, Task, Crew, Process, LLM

def main():
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINIAPIKEY")
    )

    if not api_key:
        raise ValueError("GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")

    # 최신 Google Gemini 모델: gemini-3.8-flash
    llm = LLM(
        model="gemini/gemini-3.8-flash",
        api_key=api_key,
        temperature=0.7
    )

    writer = Agent(
        role="유튜브 대본 작가",
        goal="주어진 주제로 1분짜리 쇼츠 대본을 재미있고 몰입감 있게 작성한다.",
        backstory="당신은 수많은 100만 유튜버들의 쇼츠와 릴스를 기획하고 제작해온 베테랑 대본 작가입니다.",
        llm=llm,
        verbose=True
    )

    task1 = Task(
        description='주제: "아이패드로 코딩하는 방법"에 대한 흥미진진한 1분 유튜브 쇼츠 대본 작성',
        expected_output="오프닝(3초 후킹), 본론(핵심 팁 2~3개), 결론(행동 유도/구독 요청) 구조의 완성된 쇼츠 대본",
        agent=writer
    )

    crew = Crew(
        agents=[writer],
        tasks=[task1],
        process=Process.sequential,
        verbose=True
    )

    print("대본 생성을 시작합니다...")
    result = crew.kickoff()
    print("\n" + "=" * 50)
    print("🎬 [생성된 유튜브 쇼츠 대본]")
    print("=" * 50 + "\n")
    print(result)

if __name__ == "__main__":
    main()
