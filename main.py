import os
from crewai import Agent, Task, Crew, Process, LLM

# 1. 최신 CrewAI 문법에 맞춘 공식 LLM 객체 사용
llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.environ.get("GEMINI_API_KEY")
)

# 2. 기획자 에이전트 만들기
writer = Agent(
    role='유튜브 대본 작가',
    goal='주어진 주제로 1분짜리 쇼츠 대본을 재미있게 작성한다.',
    backstory='당신은 100만 유튜버를 키워낸 천재 작가입니다.',
    llm=llm,
    verbose=True
)

# 3. 할 일(Task) 주어주기
task1 = Task(
    description='주제: "아이패드로 코딩하는 방법"에 대한 흥미로운 쇼츠 대본 작성',
    expected_output='시선 끌기, 본론, 결론이 포함된 1분 분량의 대본 텍스트',
    agent=writer
)

# 4. 크루(Crew) 결성 및 실행
crew = Crew(
    agents=[writer],
    tasks=[task1],
    process=Process.sequential
)

print("작업을 시작합니다...")
result = crew.kickoff()
print("######################")
print("최종 결과물:")
print(result)
