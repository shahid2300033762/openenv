"""
Incident Response Environment - OpenEnv compliant.

Phases: detect → analyze → contain → remediate → document
ideal_steps=5, max_steps=10

This environment simulates real-world cybersecurity incident response with:
- Realistic security logs
- Time pressure (attacks spreading)
- Decision trees with consequences
- Multiple valid approaches
"""

from __future__ import annotations
from grading.utils import clamp_score

from typing import Dict, List, Optional, Tuple

from models import Action, Observation, Reward, RewardBreakdown, RewardPenalties
from tasks.base_environment import BaseEnvironment
from tasks.incident_response.data import get_incident_by_index
from tasks.incident_response.grader import grade_incident_response


class IncidentResponseEnvironment(BaseEnvironment):
    """Simulate cybersecurity incident response."""

    TASK_NAME = "incident_response"
    MAX_STEPS = 10
    IDEAL_STEPS = 5

    def __init__(self, incident_index: int = 0) -> None:
        super().__init__(self.TASK_NAME, self.MAX_STEPS, self.IDEAL_STEPS)
        self._incident_index = incident_index
        self._incident: Dict = {}

        # Accumulated response actions
        self._detected_attack_type: Optional[str] = None
        self._identified_indicators: List[str] = []
        self._containment_actions: List[str] = []
        self._remediation_steps: List[str] = []
        self._incident_report: Optional[str] = None

        # Time pressure simulation
        self._minutes_elapsed = 0
        self._attack_spreading = False

    def _get_phase_order(self) -> List[str]:
        return ["detect", "analyze", "contain", "remediate", "document"]

    def _get_valid_action_types(self) -> List[str]:
        phase = self._current_phase
        # Incident response allows some flexibility but encourages order
        if phase == "detect":
            return ["detect"]
        elif phase == "analyze":
            return ["analyze", "contain"]  # Can start containing while analyzing
        elif phase == "contain":
            return ["analyze", "contain", "remediate"]
        elif phase == "remediate":
            return ["contain", "remediate", "document"]
        elif phase == "document":
            return ["document"]
        return ["detect", "analyze", "contain", "remediate", "document"]

    def _get_initial_observation(self) -> Observation:
        self._incident = get_incident_by_index(self._incident_index)
        self._minutes_elapsed = 0
        self._attack_spreading = False

        return Observation(
            task_name=self.TASK_NAME,
            step=0,
            instructions=(
                f"🚨 SECURITY INCIDENT: {self._incident['title']}\n"
                f"Severity: {self._incident['severity'].upper()}\n"
                f"{self._incident['description']}\n\n"
                "**Your Mission (5 phases):**\n"
                "1. **DETECT** - Identify the attack type from logs\n"
                "2. **ANALYZE** - Find indicators of compromise (IoCs)\n"
                "3. **CONTAIN** - Stop the attack from spreading\n"
                "4. **REMEDIATE** - Fix vulnerabilities and restore services\n"
                "5. **DOCUMENT** - Create incident report with lessons learned\n\n"
                "⏰ Time is critical - attacks can spread while you investigate!\n"
                f"Affected Systems: {', '.join(self._incident['affected_systems'])}"
            ),
            context=f"Incident ID: {self._incident['id']} | Severity: {self._incident['severity']}",
            data=self._incident['logs'],
            feedback="",
            available_actions=["detect"],
            phase="detect",
        )

    def _execute_action(
        self, action: Action
    ) -> Tuple[Observation, Reward, bool]:
        incident = self._incident
        gt = incident["ground_truth"]
        
        # Simulate time passing
        self._minutes_elapsed += 2
        
        # Detect phase
        if action.action_type == "detect":
            self._detected_attack_type = action.value
            grades = grade_incident_response(
                detected_type=self._detected_attack_type,
                indicators=None,
                containment=None,
                remediation=None,
                report=None,
                ground_truth=gt,
                time_elapsed=self._minutes_elapsed
            )
            
            correctness = grades["detection_score"]
            if correctness > 0.7:
                feedback = (
                    f"✅ Correct! Attack type: {action.value}\n"
                    f"Proceed to ANALYZE phase to identify indicators of compromise."
                )
            else:
                feedback = (
                    f"⚠️ Detection accuracy: {correctness*100:.0f}%\n"
                    f"Review the logs more carefully. Look for specific attack patterns."
                )
            
            return (
                Observation(
                    task_name=self.TASK_NAME,
                    step=self._step_count,
                    instructions="Analyze the logs to identify specific indicators of compromise (IoCs)",
                    context=f"Time elapsed: {self._minutes_elapsed} minutes | Attack type: {action.value}",
                    data=self._incident['logs'],
                    feedback=feedback,
                    available_actions=["analyze", "contain"],
                    phase="analyze"
                ),
                Reward(
                    score=clamp_score(correctness),
                    feedback=feedback,
                    breakdown=RewardBreakdown(
                        correctness=clamp_score(correctness),
                        progress=clamp_score(0.2),
                    )
                ),
                False
            )
        
        # Analyze phase
        elif action.action_type == "analyze":
            self._identified_indicators.append(action.value)
            grades = grade_incident_response(
                detected_type=self._detected_attack_type,
                indicators=self._identified_indicators,
                containment=None,
                remediation=None,
                report=None,
                ground_truth=gt,
                time_elapsed=self._minutes_elapsed
            )
            
            correctness = grades["analysis_score"]
            feedback = (
                f"📊 Indicator logged: {action.value}\n"
                f"Total indicators found: {len(self._identified_indicators)}/{len(gt['indicators'])}\n"
                f"Analysis quality: {correctness*100:.0f}%\n"
                "Continue to CONTAIN phase when ready."
            )
            
            return (
                Observation(
                    task_name=self.TASK_NAME,
                    step=self._step_count,
                    instructions="Implement containment actions to stop the attack",
                    context=f"Time elapsed: {self._minutes_elapsed} minutes | IoCs found: {len(self._identified_indicators)}",
                    data=f"Affected systems: {', '.join(self._incident['affected_systems'])}",
                    feedback=feedback,
                    available_actions=["analyze", "contain", "remediate"],
                    phase="contain"
                ),
                Reward(
                    score=clamp_score(correctness),
                    feedback=feedback,
                    breakdown=RewardBreakdown(
                        correctness=clamp_score(correctness),
                        progress=clamp_score(0.4),
                    )
                ),
                False
            )
        
        # Contain phase
        elif action.action_type == "contain":
            self._containment_actions.append(action.value)
            grades = grade_incident_response(
                detected_type=self._detected_attack_type,
                indicators=self._identified_indicators,
                containment=self._containment_actions,
                remediation=None,
                report=None,
                ground_truth=gt,
                time_elapsed=self._minutes_elapsed
            )
            
            correctness = grades["containment_score"]
            
            # Time pressure: slow containment allows attack to spread
            if self._minutes_elapsed > gt["time_to_contain_minutes"] and not self._attack_spreading:
                self._attack_spreading = True
                feedback = (
                    f"⚠️ WARNING: Attack is spreading! {self._minutes_elapsed} minutes elapsed.\n"
                    f"Containment action: {action.value}\n"
                    f"Speed is critical in incident response!"
                )
            else:
                feedback = (
                    f"🛡️ Containment action implemented: {action.value}\n"
                    f"Actions taken: {len(self._containment_actions)}\n"
                    f"Containment effectiveness: {correctness*100:.0f}%"
                )
            
            return (
                Observation(
                    task_name=self.TASK_NAME,
                    step=self._step_count,
                    instructions="Apply remediation steps to fix vulnerabilities and restore services",
                    context=f"Time: {self._minutes_elapsed}min | Containment: {len(self._containment_actions)} actions",
                    data=f"Recommended: {', '.join(gt['recommended_actions'][:3])}...",
                    feedback=feedback,
                    available_actions=["contain", "remediate", "document"],
                    phase="remediate"
                ),
                Reward(
                    score=clamp_score(correctness * (0.8 if self._attack_spreading else 1.0)),
                    feedback=feedback,
                    breakdown=RewardBreakdown(
                        correctness=clamp_score(correctness),
                        progress=clamp_score(0.6),
                    )
                ),
                False
            )
        
        # Remediate phase
        elif action.action_type == "remediate":
            self._remediation_steps.append(action.value)
            grades = grade_incident_response(
                detected_type=self._detected_attack_type,
                indicators=self._identified_indicators,
                containment=self._containment_actions,
                remediation=self._remediation_steps,
                report=None,
                ground_truth=gt,
                time_elapsed=self._minutes_elapsed
            )
            
            correctness = grades["remediation_score"]
            feedback = (
                f"🔧 Remediation step applied: {action.value}\n"
                f"Steps completed: {len(self._remediation_steps)}\n"
                f"System recovery: {correctness*100:.0f}%\n"
                "Proceed to DOCUMENT phase to finalize incident response."
            )
            
            return (
                Observation(
                    task_name=self.TASK_NAME,
                    step=self._step_count,
                    instructions="Document the incident with summary, timeline, impact, and lessons learned",
                    context=f"Total time: {self._minutes_elapsed} minutes | Ready for documentation",
                    data="",
                    feedback=feedback,
                    available_actions=["document"],
                    phase="document"
                ),
                Reward(
                    score=clamp_score(correctness),
                    feedback=feedback,
                    breakdown=RewardBreakdown(
                        correctness=clamp_score(correctness),
                        progress=clamp_score(0.8),
                    )
                ),
                False
            )
        
        # Document phase
        elif action.action_type == "document":
            self._incident_report = action.value
            grades = grade_incident_response(
                detected_type=self._detected_attack_type,
                indicators=self._identified_indicators,
                containment=self._containment_actions,
                remediation=self._remediation_steps,
                report=self._incident_report,
                ground_truth=gt,
                time_elapsed=self._minutes_elapsed
            )
            
            correctness = grades["overall_score"]
            
            # Final assessment
            if correctness > 0.85:
                assessment = "🌟 EXCELLENT RESPONSE"
            elif correctness > 0.70:
                assessment = "✅ GOOD RESPONSE"
            elif correctness > 0.50:
                assessment = "⚠️ ADEQUATE RESPONSE"
            else:
                assessment = "❌ NEEDS IMPROVEMENT"
            
            feedback = (
                f"{assessment}\n"
                f"Overall Score: {correctness*100:.0f}%\n"
                f"Time: {self._minutes_elapsed} minutes\n"
                f"Detection: {grades['detection_score']*100:.0f}%\n"
                f"Analysis: {grades['analysis_score']*100:.0f}%\n"
                f"Containment: {grades['containment_score']*100:.0f}%\n"
                f"Remediation: {grades['remediation_score']*100:.0f}%\n"
                f"Documentation: {grades['documentation_score']*100:.0f}%\n"
                f"{'⏱️ Time penalty applied - exceeded recommended response time' if self._minutes_elapsed > gt['time_to_contain_minutes'] * 2 else ''}"
            )
            
            return (
                Observation(
                    task_name=self.TASK_NAME,
                    step=self._step_count,
                    instructions="Incident response complete",
                    context=f"Incident {self._incident['id']} closed",
                    data="",
                    feedback=feedback,
                    available_actions=[],
                    phase="completed"
                ),
                Reward(
                    score=clamp_score(correctness),
                    feedback=feedback,
                    breakdown=RewardBreakdown(
                        correctness=clamp_score(correctness),
                        progress=clamp_score(1.0),
                    )
                ),
                True
            )
        
        # Fallback
        return (
            self._last_observation or self._get_initial_observation(),
            Reward(score=clamp_score(0.0), feedback="Invalid action"),
            False
        )
