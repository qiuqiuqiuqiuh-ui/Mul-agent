import time
from typing import List, Dict, Any

# ==========================================
# 1. 定义通信协议与基础模型
# ==========================================

class Message:
    """定义 Agent 之间的标准通信消息"""
    def __init__(self, sender: str, receiver: str, content: str, task_id: str = "default"):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.task_id = task_id
        self.timestamp = time.time()

    def __repr__(self):
        return f"[{self.sender} -> {self.receiver}] Task: {self.task_id} | Content: {self.content[:50]}..."

# ==========================================
# 2. 构建 Agent 基类及具体角色
# ==========================================

class BaseAgent:
    """Agent 抽象基类"""
    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role = role_description
        self.memory: List[Message] = []

    def receive_message(self, message: Message):
        """接收并记录消息"""
        self.memory.append(message)

    def _call_llm(self, prompt: str) -> str:
        """
        模拟大语言模型调用。
        在实际生产环境中，请接入具体的 LLM API (如 OpenAI, Gemini 等)。
        """
        # 针对 Planner 的模拟响应
        if self.name == "Planner":
            return '{"tasks": [{"id": "t1", "assignee": "Researcher", "instruction": "收集2025年全球新能源汽车销量数据"}, {"id": "t2", "assignee": "Researcher", "instruction": "分析排名前三的新能源车企的市场份额"}]}'
        # 针对 Researcher 的模拟响应
        elif self.name == "Researcher":
            if "销量数据" in prompt:
                return "已检索到数据：2025年全球新能源汽车总销量预计突破2000万辆。"
            elif "市场份额" in prompt:
                return "已完成分析：前三名车企占据了约45%的全球市场份额。"
        # 针对 Synthesizer 的模拟响应
        elif self.name == "Synthesizer":
            return "《2025全球新能源汽车市场洞察报告》\n1. 市场规模：总销量预计突破2000万辆。\n2. 竞争格局：头部效应显著，前三名占据45%份额。\n结论：市场保持高速增长，资源加速向头部集中。"
        
        return "无法处理的指令"

class PlannerAgent(BaseAgent):
    def plan(self, main_task: str) -> List[Dict[str, str]]:
        """将主任务拆解为可执行的子任务流"""
        print(f"\n[{self.name}] 正在分析并拆解主任务: {main_task}")
        prompt = f"你是规划专家。请将以下任务拆解为具体的执行步骤，并分配给相应的 Agent。任务：{main_task}"
        response = self._call_llm(prompt)
        
        # 实际应用中应增加严格的 JSON 解析异常处理
        import json
        try:
            plan_data = json.loads(response)
            return plan_data.get("tasks", [])
        except json.JSONDecodeError:
            print("任务拆解失败，返回数据格式异常。")
            return []

class WorkerAgent(BaseAgent):
    def execute(self, task_msg: Message) -> Message:
        """执行具体任务并返回结果"""
        print(f"[{self.name}] 正在执行任务 ({task_msg.task_id}): {task_msg.content}")
        prompt = f"你是专业执行者。请完成以下任务：{task_msg.content}"
        result = self._call_llm(prompt)
        
        # 将结果封装为消息返回给系统或调度方
        return Message(
            sender=self.name,
            receiver="Synthesizer",
            content=result,
            task_id=task_msg.task_id
        )

class SynthesizerAgent(BaseAgent):
    def summarize(self, reports: List[Message]) -> str:
        """汇总所有子任务的结果，生成最终报告"""
        print(f"\n[{self.name}] 正在汇总 {len(reports)} 份子任务结果，生成最终报告...")
        context = "\n".join([f"任务 {msg.task_id} 结果: {msg.content}" for msg in reports])
        prompt = f"你是资深分析师。请基于以下原始数据，撰写一份结构化的最终报告：\n{context}"
        final_report = self._call_llm(prompt)
        return final_report

# ==========================================
# 3. 构建多 Agent 协同调度引擎
# ==========================================

class MultiAgentSystem:
    """管理和调度多个 Agent 协同工作的系统环境"""
    def __init__(self):
        self.planner = PlannerAgent("Planner", "系统主脑，负责任务分解与资源调度")
        self.researcher = WorkerAgent("Researcher", "数据检索与数据分析专家")
        self.synthesizer = SynthesizerAgent("Synthesizer", "报告撰写与信息整合专家")
        self.message_bus: List[Message] = []

    def run(self, user_request: str) -> str:
        print("====== 自动化协同系统启动 ======")
        
        # 第一阶段：任务规划
        sub_tasks = self.planner.plan(user_request)
        if not sub_tasks:
            return "系统未能成功规划任务流程。"
            
        print(f"[{self.planner.name}] 成功拆解出 {len(sub_tasks)} 个子任务。")

        # 第二阶段：任务分发与执行
        task_results = []
        for task in sub_tasks:
            if task["assignee"] == "Researcher":
                # 创建任务消息
                task_msg = Message(
                    sender=self.planner.name,
                    receiver=self.researcher.name,
                    content=task["instruction"],
                    task_id=task["id"]
                )
                self.message_bus.append(task_msg)
                
                # 执行并获取结果
                result_msg = self.researcher.execute(task_msg)
                task_results.append(result_msg)
                self.message_bus.append(result_msg)

        # 第三阶段：结果汇总与输出
        final_output = self.synthesizer.summarize(task_results)
        
        print("\n====== 系统执行完毕 ======")
        return final_output

# ==========================================
# 4. 运行示例
# ==========================================
if __name__ == "__main__":
    orchestrator = MultiAgentSystem()
    query = "请帮我撰写一份关于2025年全球新能源汽车市场的行业分析报告。"
    
    final_result = orchestrator.run(query)
    print(f"\n[最终输出]\n{final_result}")