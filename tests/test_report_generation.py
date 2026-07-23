from backend.agents.report_generation import build_structured_report


def test_build_structured_report_includes_expected_sections() -> None:
    report = build_structured_report(
        lead_name="Ava",
        company="Northwind Labs",
        website="https://northwindlabs.com",
        research={
            "description": "Northwind Labs helps manufacturers modernise operations with AI-driven analytics.",
            "industry": "Manufacturing technology",
        },
        analysis={
            "business_model": "B2B SaaS for industrial operations analytics",
            "pain_points": ["Manual reporting", "Fragmented customer data"],
            "strengths": ["Strong domain expertise", "Clear value proposition"],
        },
        insights={
            "website_audit": {
                "design_score": 7,
                "ux_score": 6,
                "content_score": 8,
                "seo_score": 6,
            },
            "recommendations": ["Improve onboarding conversion", "Launch a lead intelligence assistant"],
            "automation_opportunities": ["Proposal drafting", "Customer follow-up automation"],
            "priority_actions": ["Audit onboarding funnel", "Deploy AI assistant"],
        },
    )

    assert "# Executive Summary" in report
    assert "# Company Overview" in report
    assert "# Website Analysis" in report
    assert "# AI & Automation Opportunities" in report
    assert "# Strategic Recommendations" in report
    assert "# Next Steps" in report
    assert "Northwind Labs" in report
    assert "Ava" in report
    assert "built-in fallback content generator" not in report.lower()
