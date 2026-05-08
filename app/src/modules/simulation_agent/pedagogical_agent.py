import json
from typing import Dict, Any

from .agentic_models import AdaptiveLearningProfile, CognitiveProfile, PedagogicalStrategy

from .models import SimulationTopic
from .llm_client import call_llm


class PedagogicalAgent:
    """
    Agent responsible for determining the optimal educational strategy
    based on student cognitive profile and learning history.
    """

    def determine_strategy(
        self, 
        profile: AdaptiveLearningProfile, 
        topic: SimulationTopic
    ) -> PedagogicalStrategy:
        """
        Use LLM to reason about the best pedagogical approach.
        """
        
        reasoning_prompt = f"""
        # Task: Determine Pedagogical Strategy
        
        You are an expert pedagogical psychologist. Your goal is to choose the best teaching strategy for a student.
        
        ## Student Cognitive Profile
        Learning Style: {profile.cognitive.learning_style}
        Learning Speed: {profile.cognitive.learning_speed}
        Engagement: {profile.cognitive.engagement_score}
        Weak Topics: {profile.weak_topics}
        Retry Frequency: {profile.cognitive.retry_frequency}
        
        ## Topic
        {topic.topic} ({topic.subject})
        
        ## Strategy Requirements
        1. Instruction Mode: guided (for beginners/struggling), discovery (for medium), challenge (for advanced).
        2. Visualization Complexity: simple, medium, or complex.
        3. Animation Speed: scale factor (e.g., 0.5 for slower, 1.5 for faster).
        4. Label Density: how many annotations and labels to show.
        5. Explanation Style: technical, analogical, or step-by-step.
        
        ## Output Format
        Return ONLY a JSON object:
        {{
            "instruction_mode": "string",
            "visualization_complexity": "string",
            "animation_speed_scale": float,
            "label_density": "string",
            "explanation_style": "string"
        }}
        """

        try:
            response_text = call_llm(
                reasoning_prompt, 
                temperature=0.2, 
                response_mime_type="application/json"
            )
            strategy_data = json.loads(response_text)
            return PedagogicalStrategy(**strategy_data)
            
        except Exception as e:
            print(f"Pedagogical reasoning failed: {e}. Falling back to default.")
            return self._get_fallback_strategy(profile)

    def suggest_next_steps(self, profile: AdaptiveLearningProfile, current_topic: str) -> Dict[str, Any]:
        """
        Suggest personalized next steps in the learning path.
        """
        recommendation_prompt = f"""
        # Task: Suggest Learning Path Next Steps
        
        Student Mastery: {profile.mastery}
        Weak Topics: {profile.weak_topics}
        Current Topic: {current_topic}
        
        ## Output Format
        Return ONLY a JSON object:
        {{
            "next_simulation": "string",
            "revision_topics": ["string"],
            "challenge_problem": "string",
            "learning_goal": "string"
        }}
        """
        
        try:
            response_text = call_llm(recommendation_prompt, temperature=0.3, response_mime_type="application/json")
            return json.loads(response_text)
        except Exception:
            return {
                "next_simulation": "Advanced " + current_topic,
                "revision_topics": profile.weak_topics[:2],
                "learning_goal": "Deepen understanding of " + current_topic
            }

# Global instance
pedagogical_agent = PedagogicalAgent()

