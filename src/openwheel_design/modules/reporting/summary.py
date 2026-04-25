def create_analysis_summary(analyses_dict):
    summary = {
        "total_analyses": len(analyses_dict),
        "passed": sum(1 for a in analyses_dict.values() if a.get("passed", False)),
        "failed": sum(1 for a in analyses_dict.values() if not a.get("passed", True)),
    }
    return summary

def generate_recommendations(analysis_results):
    recs = []
    
    if analysis_results.get("weight", 0) > 230:
        recs.append("Vehicle weight exceeds optimal - consider weight reduction")
    if analysis_results.get("power_to_weight", 0) < 0.5:
        recs.append("Low power-to-weight ratio - consider motor upgrade or weight reduction")
    if analysis_results.get("cog_height", 0) > 320:
        recs.append("High CoG affects handling - lower component placement")
    if analysis_results.get("brake_bias", 0) < 55:
        recs.append("Front brake bias may be too aggressive")
    if analysis_results.get("tire_temp", 0) > 110:
        recs.append("Tire temperature too high - check cooling or compound")
    
    return recs

def highlight_critical_issues(results):
    critical = []
    for key, val in results.items():
        if isinstance(val, dict) and val.get("critical"):
            critical.append(key)
        elif key in ["safety_factor", "temperature", "pressure"]:
            if isinstance(val, (int, float)) and val < 1:
                critical.append(key)
    return critical

def suggest_next_steps(recommendations, priorities):
    steps = []
    for rec in recommendations[:priorities]:
        steps.append({
            "action": rec,
            "priority": recommendations.index(rec) + 1,
            "estimated_impact": "high"
        })
    return steps

def export_summary_markdown(summary, recommendations):
    md = ["# Analysis Summary\n"]
    md.append(f"- Total Analyses: {summary['total_analyses']}")
    md.append(f"- Passed: {summary['passed']}")
    md.append(f"- Failed: {summary['failed']}\n")
    
    if recommendations:
        md.append("## Recommendations\n")
        for rec in recommendations:
            md.append(f"- {rec}")
    
    return "\n".join(md)