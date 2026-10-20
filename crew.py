import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

# 환경 변수 로드 (.env)
load_dotenv()

@CrewBase
class VideoPipelineCrew:
    """CrewAI 기반 AI 비디오 기획 및 Colab 디스패치 파이프라인"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        # Ollama 설정 로드
        ollama_model = os.getenv("OLLAMA_MODEL", "ollama/llama3.2")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # CrewAI LLM 설정
        self.llm = LLM(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.7,
        )

    @agent
    def story_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["story_writer"],
            llm=self.llm,
            verbose=True
        )

    @agent
    def prompt_director(self) -> Agent:
        return Agent(
            config=self.agents_config["prompt_director"],
            llm=self.llm,
            verbose=True
        )

    @agent
    def pipeline_dispatcher(self) -> Agent:
        return Agent(
            config=self.agents_config["pipeline_dispatcher"],
            llm=self.llm,
            verbose=True
        )

    @task
    def story_task(self) -> Task:
        return Task(
            config=self.tasks_config["story_task"]
        )

    @task
    def prompt_task(self) -> Task:
        return Task(
            config=self.tasks_config["prompt_task"]
        )

    @task
    def export_task(self) -> Task:
        return Task(
            config=self.tasks_config["export_task"],
            output_file="scenes.json"
        )

    @crew
    def crew(self) -> Crew:
        """비디오 생성 기획 크루 구성"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
