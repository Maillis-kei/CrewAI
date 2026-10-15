import os
from crewai import Agent, Task, Crew, Process, LLM

# 1. 환경 변수 확실하게 고정 (내장 라이브러리가 자동으로 읽도록 강제 세팅)
os.environ["GEMINI_API_KEY"] = os.environ.get("geminiapikey")

# 2. CrewAI의 최신 표준에 맞춘 모델 호출 방식
llm = LLM(
    model="gemini/gemini-1.5-flash",  # 구글 1.5 플래시 모델의 공식 호출명
    temperature=0.7
)

# 3. 기획자 에이전트 만들기
writer = Agent(
    role='유튜브 대본 작가',
    goal='주어진 주제로 1분짜리 쇼츠 대본을 재미있게 작성한다.',
    backstory='당신은 100만 유튜버를 키워낸 천재 작가입니다.',
    llm=llm,
    verbose=True
)

# 4. 할 일(Task) 주어주기
task1 = Task(
    description='주제: "아이패드로 코딩하는 방법"에 대한 흥미로운 쇼츠 대본 작성',
    expected_output='시선 끌기, 본론, 결론이 포함된 1분 분량의 대본 텍스트',
    agent=writer
)

# 5. 크루(Crew) 결성 및 실행
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
