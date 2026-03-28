"""
Incident Response grader - Advanced semantic evaluation.

Weights:
  - Detection: 20%
  - Analysis (IoCs): 25%
  - Containment: 25%
  - Remediation: 20%
  - Documentation: 10%
  
Time penalties apply for slow response.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from grading.utils import (
    fuzzy_keyword_match,
    semantic_similarity,
    normalize_text
)


def grade_detection(detected: Optional[str], ground_truth_type: str) -> float:
    """
    Score attack type detection.
    Exact match = 1.0, related types get partial credit.
    """
    if not detected:
        return 0.0
    
    det_norm = normalize_text(detected)
    gt_norm = normalize_text(ground_truth_type)
    
    # Exact match
    if det_norm == gt_norm:
        return 1.0
    
    # Check for partial matches and synonyms
    attack_families = {
        "sql_injection": ["sql", "injection", "sqli", "database attack"],
        "ransomware": ["ransom", "encryption", "crypto", "file locker"],
        "insider_threat": ["insider", "internal", "employee", "data theft"],
        "ddos": ["ddos", "dos", "denial of service", "flood"],
        "privilege_escalation": ["privilege", "escalation", "priv esc", "root", "admin"]
    }
    
    # Get keywords for ground truth type
    gt_keywords = attack_families.get(gt_norm, [gt_norm])
    
    # Check if detected type contains any keywords
    for keyword in gt_keywords:
        if keyword in det_norm:
            return 0.8
    
    # Fuzzy match as fallback
    all_keywords = []
    for keywords in attack_families.values():
        all_keywords.extend(keywords)
    
    similarity = fuzzy_keyword_match(det_norm, all_keywords)
    return max(0.0, similarity * 0.6)


def grade_indicators(
    identified: Optional[List[str]],
    ground_truth_indicators: List[str]
) -> float:
    """
    Score indicator identification using semantic matching.
    Rewards finding multiple correct indicators.
    """
    if not identified:
        return 0.0
    
    if not ground_truth_indicators:
        return 0.5  # Some credit for trying
    
    matches = 0
    for gt_indicator in ground_truth_indicators:
        gt_norm = normalize_text(gt_indicator)
        for identified_ioc in identified:
            id_norm = normalize_text(identified_ioc)
            # Use semantic similarity for flexible matching
            similarity = semantic_similarity(id_norm, gt_norm)
            if similarity > 0.5:  # Threshold for match
                matches += 1
                break
    
    # Score based on recall
    recall = matches / len(ground_truth_indicators)
    
    # Bonus for finding all indicators
    if matches == len(ground_truth_indicators):
        recall += 0.1
    
    return min(1.0, recall)


def grade_containment(
    actions: Optional[List[str]],
    ground_truth_actions: List[str]
) -> float:
    """
    Score containment actions.
    Checks if critical actions are included.
    """
    if not actions:
        return 0.0
    
    if not ground_truth_actions:
        return 0.5
    
    # Critical actions (higher weight)
    critical_keywords = {
        "block", "isolate", "disable", "disconnect", "quarantine",
        "kill", "stop", "terminate", "suspend"
    }
    
    matches = 0
    critical_matches = 0
    
    for gt_action in ground_truth_actions:
        gt_norm = normalize_text(gt_action)
        for action in actions:
            action_norm = normalize_text(action)
            
            # Check semantic similarity
            similarity = semantic_similarity(action_norm, gt_norm)
            if similarity > 0.4:
                matches += 1
                # Check if it's a critical action
                if any(kw in action_norm for kw in critical_keywords):
                    critical_matches += 1
                break
    
    # Calculate score
    base_score = matches / len(ground_truth_actions)
    critical_bonus = (critical_matches / len([a for a in ground_truth_actions 
                                               if any(kw in normalize_text(a) for kw in critical_keywords)])) * 0.2 \
                      if any(kw in normalize_text(a) for kw in critical_keywords for a in ground_truth_actions) else 0
    
    return min(1.0, base_score + critical_bonus)


def grade_remediation(
    steps: Optional[List[str]],
    ground_truth_actions: List[str],
    attack_type: str
) -> float:
    """
    Score remediation steps.
    Looks for long-term fixes, not just immediate containment.
    """
    if not steps:
        return 0.0
    
    # Remediation keywords (different from containment)
    remediation_keywords = {
        "patch", "update", "fix", "restore", "backup", "implement",
        "enable", "configure", "audit", "review", "monitor", "scan",
        "reset", "change password", "upgrade"
    }
    
    matches = 0
    remediation_quality = 0
    
    for step in steps:
        step_norm = normalize_text(step)
        
        # Check for remediation keywords
        has_remediation = any(kw in step_norm for kw in remediation_keywords)
        if has_remediation:
            remediation_quality += 1
        
        # Match against ground truth
        for gt_action in ground_truth_actions:
            gt_norm = normalize_text(gt_action)
            if semantic_similarity(step_norm, gt_norm) > 0.4:
                matches += 1
                break
    
    # Score based on both matches and remediation quality
    if len(ground_truth_actions) > 0:
        match_score = matches / len(ground_truth_actions)
    else:
        match_score = 0.5
    
    quality_bonus = min(0.2, (remediation_quality / max(len(steps), 3)) * 0.2)
    
    return min(1.0, match_score + quality_bonus)


def grade_documentation(
    report: Optional[str],
    attack_type: str,
    severity: str
) -> float:
    """
    Score incident documentation quality.
    Checks for completeness and structure.
    """
    if not report or not report.strip():
        return 0.0
    
    report_norm = normalize_text(report)
    word_count = len(report.split())
    
    score = 0.0
    
    # Length check (minimum substance required)
    if word_count < 20:
        return 0.1
    if word_count >= 50:
        score += 0.2
    elif word_count >= 30:
        score += 0.1
    
    # Check for key sections
    key_sections = {
        "summary": ["summary", "overview", "incident", "what happened"],
        "impact": ["impact", "affected", "damage", "loss", "consequence"],
        "timeline": ["timeline", "when", "time", "duration", "minutes"],
        "lessons": ["lesson", "learn", "improve", "prevent", "future", "recommendation"]
    }
    
    sections_found = 0
    for section, keywords in key_sections.items():
        if any(kw in report_norm for kw in keywords):
            sections_found += 1
    
    score += (sections_found / len(key_sections)) * 0.5
    
    # Check for technical details
    technical_terms = {
        "technical": ["ip", "system", "log", "cve", "vulnerability", "exploit", 
                     "malware", "network", "firewall", "patch"],
        "actions": ["blocked", "contained", "remediated", "restored", "fixed", "implemented"]
    }
    
    technical_score = 0
    for category, terms in technical_terms.items():
        if any(term in report_norm for term in terms):
            technical_score += 1
    
    score += (technical_score / len(technical_terms)) * 0.3
    
    return min(1.0, score)


def grade_incident_response(
    detected_type: Optional[str],
    indicators: Optional[List[str]],
    containment: Optional[List[str]],
    remediation: Optional[List[str]],
    report: Optional[str],
    ground_truth: Dict,
    time_elapsed: int = 0
) -> Dict[str, float]:
    """
    Grade complete incident response.
    
    Returns dictionary with individual scores and overall score.
    """
    gt_type = ground_truth["attack_type"]
    gt_indicators = ground_truth["indicators"]
    gt_actions = ground_truth["recommended_actions"]
    gt_severity = ground_truth["severity"]
    
    # Individual phase scores
    detection_score = grade_detection(detected_type, gt_type) if detected_type else 0.0
    analysis_score = grade_indicators(indicators, gt_indicators) if indicators else 0.0
    containment_score = grade_containment(containment, gt_actions) if containment else 0.0
    remediation_score = grade_remediation(remediation, gt_actions, gt_type) if remediation else 0.0
    documentation_score = grade_documentation(report, gt_type, gt_severity) if report else 0.0
    
    # Weighted overall score
    overall = (
        detection_score * 0.20 +
        analysis_score * 0.25 +
        containment_score * 0.25 +
        remediation_score * 0.20 +
        documentation_score * 0.10
    )
    
    # Time penalty for slow response
    if time_elapsed > ground_truth.get("time_to_contain_minutes", 999) * 2:
        time_penalty = 0.1
        overall = max(0.0, overall - time_penalty)
    
    return {
        "detection_score": detection_score,
        "analysis_score": analysis_score,
        "containment_score": containment_score,
        "remediation_score": remediation_score,
        "documentation_score": documentation_score,
        "overall_score": overall,
        "time_elapsed": time_elapsed
    }
