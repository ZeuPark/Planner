"""
Plan generation logic for Long Plan Desktop App.

Generates a structured plan with 3-5 phases based on user input.
"""
from models import Plan, Phase, Item, Duration


class PlanGenerator:
    """Generates structured plans based on goal and duration."""

    # Default phase templates (can be customized based on goal keywords)
    DEFAULT_PHASES = [
        ("준비", ["목표 구체화하기", "필요한 자료 수집하기", "환경 세팅하기", "기초 개념 파악하기"]),
        ("기초", ["핵심 개념 학습하기", "기본 스킬 익히기", "간단한 예제 따라하기", "기초 연습하기"]),
        ("심화", ["심화 내용 학습하기", "실전 프로젝트 시작하기", "어려운 부분 집중 학습하기", "피드백 반영하기"]),
        ("실전", ["실제 적용하기", "완성도 높이기", "부족한 부분 보완하기", "결과물 정리하기"]),
        ("마무리", ["전체 복습하기", "결과 정리하기", "다음 단계 계획하기"]),
    ]

    # Keyword-based phase templates
    STUDY_PHASES = [
        ("준비", ["학습 목표 정리하기", "교재/자료 선정하기", "학습 환경 세팅하기"]),
        ("기초 학습", ["기초 이론 공부하기", "핵심 개념 정리하기", "기본 문제 풀기", "노트 정리하기"]),
        ("심화 학습", ["심화 이론 공부하기", "응용 문제 풀기", "모르는 부분 집중 학습하기"]),
        ("실전 연습", ["실전 문제 풀기", "시간 제한 연습하기", "오답 분석하기", "취약점 보완하기"]),
        ("마무리", ["전체 복습하기", "최종 점검하기", "결과 정리하기"]),
    ]

    PROJECT_PHASES = [
        ("기획", ["프로젝트 범위 정의하기", "요구사항 정리하기", "구조 설계하기"]),
        ("준비", ["개발 환경 세팅하기", "필요한 기술 학습하기", "프로토타입 만들기"]),
        ("개발", ["핵심 기능 구현하기", "세부 기능 구현하기", "테스트하기", "버그 수정하기"]),
        ("완성", ["UI/UX 다듬기", "문서화하기", "최종 테스트하기"]),
        ("배포", ["배포 준비하기", "배포하기", "피드백 수집하기"]),
    ]

    SKILL_PHASES = [
        ("탐색", ["스킬 분석하기", "학습 자료 찾기", "목표 수준 정하기"]),
        ("기초", ["기초 동작 익히기", "기본 패턴 연습하기", "매일 짧게 연습하기"]),
        ("발전", ["중급 기술 배우기", "다양한 상황 연습하기", "피드백 받기"]),
        ("숙달", ["고급 기술 배우기", "실전 적용하기", "꾸준히 유지하기"]),
    ]

    HEALTH_PHASES = [
        ("준비", ["현재 상태 점검하기", "목표 설정하기", "계획 세우기"]),
        ("적응", ["가볍게 시작하기", "루틴 만들기", "몸 적응시키기"]),
        ("강화", ["강도 높이기", "새로운 도전하기", "기록 측정하기"]),
        ("유지", ["루틴 유지하기", "컨디션 관리하기", "목표 달성 확인하기"]),
    ]

    def __init__(self):
        self.keywords = {
            "study": ["공부", "학습", "시험", "자격증", "언어", "영어", "수학", "코딩"],
            "project": ["프로젝트", "개발", "만들기", "앱", "웹", "사이트", "서비스"],
            "skill": ["스킬", "기술", "악기", "그림", "운동", "요리", "피아노", "기타"],
            "health": ["운동", "다이어트", "건강", "체력", "근육", "달리기", "헬스"],
        }

    def _detect_category(self, goal: str) -> str:
        """Detect the category of the goal based on keywords."""
        goal_lower = goal.lower()
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in goal_lower:
                    return category
        return "default"

    def _get_phase_template(self, category: str) -> list[tuple[str, list[str]]]:
        """Get the appropriate phase template based on category."""
        templates = {
            "study": self.STUDY_PHASES,
            "project": self.PROJECT_PHASES,
            "skill": self.SKILL_PHASES,
            "health": self.HEALTH_PHASES,
            "default": self.DEFAULT_PHASES,
        }
        return templates.get(category, self.DEFAULT_PHASES)

    def _adjust_items_for_duration(
        self, phases: list[tuple[str, list[str]]], duration: Duration, weekly_hours: int
    ) -> list[tuple[str, list[str]]]:
        """Adjust the number of items based on duration and weekly hours."""
        total_weeks = duration.weeks
        total_hours = total_weeks * weekly_hours

        # Estimate ~2-4 hours per item depending on complexity
        hours_per_item = 3
        target_items = max(10, total_hours // hours_per_item)

        # Calculate current total items
        current_total = sum(len(items) for _, items in phases)

        # If we need more items, expand each phase
        if target_items > current_total:
            multiplier = target_items / current_total
            adjusted = []
            for phase_name, items in phases:
                expanded_items = items.copy()
                if multiplier > 1.5:
                    # Add "심화" versions of existing items
                    for item in items[:int(len(items) * (multiplier - 1))]:
                        expanded_items.append(f"{item} (심화)")
                adjusted.append((phase_name, expanded_items))
            return adjusted

        return phases

    def generate(self, goal: str, duration: Duration, weekly_hours: int) -> Plan:
        """Generate a complete plan based on input parameters."""
        plan = Plan.create(goal, duration, weekly_hours)

        # Detect category and get template
        category = self._detect_category(goal)
        phase_template = self._get_phase_template(category)

        # Adjust for duration
        adjusted_template = self._adjust_items_for_duration(
            phase_template, duration, weekly_hours
        )

        # Create phases and items
        for phase_order, (phase_name, item_names) in enumerate(adjusted_template):
            phase = Phase.create(phase_name, phase_order)

            for item_order, item_name in enumerate(item_names):
                item = Item.create(item_name, phase.id, item_order)
                phase.items.append(item)

            plan.phases.append(phase)

        return plan
