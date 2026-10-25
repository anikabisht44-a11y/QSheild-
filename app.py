"""QShield Streamlit Application."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

from qshield.models import (
    Asset, Settings, VALID_ALGORITHMS, MIGRATION_COMPLEXITY_OPTIONS,
    ORG_TYPE_OPTIONS, MILESTONE_OPTIONS,
)
from qshield.risk import (
    calculate_all_profiles, calculate_exposure_sum, validate_asset,
    get_required_completion_text,
)
from qshield.db import (
    init_db, get_settings, save_settings, get_assets, save_assets,
    reset_database,
)
from qshield.report import (
    generate_markdown_report, generate_pdf_report,
    SCENARIO_DISCLAIMER, GENERAL_DISCLAIMER, DPDP_NOTE, STANDARDS_NOTE,
)
from qshield.roadmap import generate_roadmap, format_roadmap_markdown
from qshield.milestones import (
    compare_with_milestone, calculate_planned_completion_year, MILESTONE_NOTE,
)
from qshield.discovery import check_tls, map_to_algorithm, format_tls_result, ETHICS_NOTE


# Initialize database
init_db()


def load_sample_data(sample_type: str) -> None:
    """Load sample data from CSV."""
    import pandas as pd
    from pathlib import Path
    
    if sample_type == "college":
        csv_path = Path(__file__).parent / "data" / "sample_college.csv"
        org_type = "Education"
    else:  # hospital
        csv_path = Path(__file__).parent / "data" / "sample_hospital.csv"
        org_type = "Healthcare"
    
    df = pd.read_csv(csv_path)
    assets = []
    for _, row in df.iterrows():
        assets.append(Asset(
            asset_name=row["asset_name"],
            data_category=row["data_category"],
            confidentiality_years=row["confidentiality_years"],
            algorithm=row["algorithm"],
            migration_complexity=row["migration_complexity"],
            migration_years=row["migration_years"],
            algorithm_source=row["algorithm_source"],
        ))
    
    save_assets(assets)
    
    # Update org type
    settings = get_settings()
    settings.org_type = org_type
    save_settings(settings)
    
    st.success(f"Loaded {sample_type} sample data ({len(assets)} assets)")


def main():
    """Main application."""
    st.set_page_config(
        page_title="QShield - Quantum-Safe Migration Planner",
        page_icon="🛡️",
        layout="wide",
    )
    
    st.title("🛡️ QShield: Quantum-Safe Migration Planner")
    st.markdown(
        "A planning tool to assess data asset exposure to hypothetical quantum threats "
        "and prioritize migration efforts."
    )
    
    # Initialize session state
    if "assets" not in st.session_state:
        st.session_state.assets = get_assets()
    if "settings" not in st.session_state:
        st.session_state.settings = get_settings()
    
    # Sidebar
    with st.sidebar:
        st.header("Organization")
        
        org_name = st.text_input(
            "Organization Name",
            value=st.session_state.settings.org_name,
        )
        
        org_type = st.selectbox(
            "Organization Type",
            ORG_TYPE_OPTIONS,
            index=ORG_TYPE_OPTIONS.index(st.session_state.settings.org_type),
        )
        
        st.divider()
        
        st.header("Sample Data")
        if st.button("Load sample: college"):
            load_sample_data("college")
            st.session_state.assets = get_assets()
            st.rerun()
        
        if st.button("Load sample: hospital"):
            load_sample_data("hospital")
            st.session_state.assets = get_assets()
            st.rerun()
        
        st.divider()
        
        st.header("Reset")
        reset_confirm = st.checkbox("Confirm reset all data")
        if st.button("Reset all data"):
            if reset_confirm:
                reset_database()
                st.session_state.assets = []
                st.session_state.settings = Settings()
                st.success("All data has been reset")
                st.rerun()
        
        # Update settings if changed
        if (org_name != st.session_state.settings.org_name or 
            org_type != st.session_state.settings.org_type):
            st.session_state.settings.org_name = org_name
            st.session_state.settings.org_type = org_type
            save_settings(st.session_state.settings)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Assets", "Scenarios", "Results", "Roadmap", "Report",
    ])
    
    # Tab 1: Assets
    with tab1:
        st.header("Data Assets")
        st.markdown("Enter or edit your organization's data assets.")
        
        # Convert assets to DataFrame for editing
        if st.session_state.assets:
            df_data = []
            for asset in st.session_state.assets:
                df_data.append({
                    "asset_name": asset.asset_name,
                    "data_category": asset.data_category,
                    "confidentiality_years": asset.confidentiality_years,
                    "algorithm": asset.algorithm,
                    "migration_complexity": asset.migration_complexity,
                    "migration_years": asset.migration_years,
                    "algorithm_source": asset.algorithm_source,
                })
            df = pd.DataFrame(df_data)
        else:
            df = pd.DataFrame(columns=[
                "asset_name", "data_category", "confidentiality_years",
                "algorithm", "migration_complexity", "migration_years",
                "algorithm_source",
            ])
        
        edited_df = st.data_editor(
            df,
            column_config={
                "asset_name": st.column_config.TextColumn("Asset Name", required=True),
                "data_category": st.column_config.TextColumn("Data Category", required=True),
                "confidentiality_years": st.column_config.NumberColumn(
                    "Confidentiality (X years)", min_value=0.5, max_value=100, step=0.5,
                ),
                "algorithm": st.column_config.SelectboxColumn(
                    "Algorithm", options=VALID_ALGORITHMS,
                ),
                "migration_complexity": st.column_config.SelectboxColumn(
                    "Complexity", options=MIGRATION_COMPLEXITY_OPTIONS,
                ),
                "migration_years": st.column_config.NumberColumn(
                    "Migration (Y years)", min_value=0.5, max_value=30, step=0.5,
                ),
                "algorithm_source": st.column_config.SelectboxColumn(
                    "Source", options=["user_estimate", "confirmed"],
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
        )
        
        # Validation
        validation_errors = []
        assets_to_save = []
        
        for _, row in edited_df.iterrows():
            try:
                asset = Asset(
                    asset_name=row["asset_name"],
                    data_category=row["data_category"],
                    confidentiality_years=row["confidentiality_years"],
                    algorithm=row["algorithm"],
                    migration_complexity=row["migration_complexity"],
                    migration_years=row["migration_years"],
                    algorithm_source=row["algorithm_source"],
                )
                errors = validate_asset(asset)
                if errors:
                    validation_errors.append((row["asset_name"], errors))
                else:
                    assets_to_save.append(asset)
            except Exception as e:
                validation_errors.append((row.get("asset_name", "Unknown"), [str(e)]))
        
        if validation_errors:
            st.error("Validation errors:")
            for name, errors in validation_errors:
                st.error(f"{name}: {', '.join(errors)}")
        else:
            if st.button("Save Assets"):
                save_assets(assets_to_save)
                st.session_state.assets = assets_to_save
                st.success("Assets saved successfully")
                st.rerun()
        
        # TLS Check (P2)
        st.divider()
        st.subheader("TLS Algorithm Check (Optional)")
        st.markdown(ETHICS_NOTE)
        
        hostname = st.text_input("Hostname (e.g., example.com)")
        allow_untrusted = st.checkbox("Allow untrusted certificate (localhost lab only)", value=False)
        
        if st.button("Check TLS"):
            if hostname:
                with st.spinner("Checking TLS..."):
                    result = check_tls(hostname, allow_untrusted=allow_untrusted)
                    st.text(format_tls_result(result))
                    
                    if result.get("success"):
                        mapped_algorithm = map_to_algorithm(result)
                        if mapped_algorithm:
                            st.info(f"Mapped algorithm: {mapped_algorithm}")
                            if st.button(f"Apply to asset"):
                                # Find asset to update (simplified - in real app would select specific asset)
                                st.info("Select an asset in the table above to apply this algorithm.")
                        else:
                            st.warning("Could not map certificate to a known algorithm. Manual entry required.")
            else:
                st.warning("Please enter a hostname")
    
    # Tab 2: Scenarios
    with tab2:
        st.header("Planning Scenarios")
        st.markdown("Set hypothetical timelines for when a cryptographically relevant quantum computer might exist.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            scenario_a = st.number_input(
                "Scenario A (years)",
                min_value=1.0,
                max_value=50.0,
                value=st.session_state.settings.scenario_a,
                step=1.0,
            )
        
        with col2:
            scenario_b = st.number_input(
                "Scenario B (years)",
                min_value=1.0,
                max_value=50.0,
                value=st.session_state.settings.scenario_b,
                step=1.0,
            )
        
        with col3:
            scenario_c = st.number_input(
                "Scenario C (years)",
                min_value=1.0,
                max_value=50.0,
                value=st.session_state.settings.scenario_c,
                step=1.0,
            )
        
        st.warning(SCENARIO_DISCLAIMER)
        
        # Milestone overlay (P1)
        st.divider()
        st.subheader("India Milestone Overlay (P1)")
        milestone = st.selectbox(
            "Milestone",
            MILESTONE_OPTIONS,
            index=MILESTONE_OPTIONS.index(st.session_state.settings.milestone),
        )
        if milestone != "none":
            st.info(MILESTONE_NOTE)
        
        # Update settings if changed
        if (scenario_a != st.session_state.settings.scenario_a or
            scenario_b != st.session_state.settings.scenario_b or
            scenario_c != st.session_state.settings.scenario_c or
            milestone != st.session_state.settings.milestone):
            st.session_state.settings.scenario_a = scenario_a
            st.session_state.settings.scenario_b = scenario_b
            st.session_state.settings.scenario_c = scenario_c
            st.session_state.settings.milestone = milestone
            save_settings(st.session_state.settings)
    
    # Tab 3: Results
    with tab3:
        st.header("Risk Analysis Results")
        
        if not st.session_state.assets:
            st.info("No assets loaded. Add assets in the Assets tab or load sample data.")
        else:
            scenarios = (scenario_a, scenario_b, scenario_c)
            profiles = calculate_all_profiles(
                st.session_state.assets, *scenarios
            )
            
            # Summary counts
            ranked_profiles = [p for p in profiles if p.asset.is_ranked]
            priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Lower": 0}
            for p in ranked_profiles:
                priority_counts[p.priority_label] += 1
            
            st.subheader("Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Critical", priority_counts["Critical"])
            col2.metric("High", priority_counts["High"])
            col3.metric("Medium", priority_counts["Medium"])
            col4.metric("Lower", priority_counts["Lower"])
            
            # Ranked table
            st.subheader("Ranked Assets")
            ranked_data = []
            for p in sorted(ranked_profiles, key=lambda x: x.rank or 0):
                ranked_data.append({
                    "Rank": p.rank,
                    "Asset": p.asset.asset_name,
                    "Category": p.asset.data_category,
                    "X": p.asset.confidentiality_years,
                    "Y": p.asset.migration_years,
                    "X+Y": p.results_a.exposure_sum,
                    "Algorithm": p.asset.algorithm,
                    "Exposed in": f"{p.exposed_count} of 3",
                    "Priority": p.priority_label,
                    "Margin A": p.results_a.margin,
                    "Margin B": p.results_b.margin,
                    "Margin C": p.results_c.margin,
                })
            
            if ranked_data:
                st.data_editor(
                    pd.DataFrame(ranked_data),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No ranked assets (all assets use post-quantum or symmetric algorithms).")
            
            # Break-even chart
            st.subheader("Break-Even Chart")
            if ranked_data:
                chart_data = pd.DataFrame(ranked_data)
                fig = px.bar(
                    chart_data,
                    x="X+Y",
                    y="Asset",
                    orientation="h",
                    title="Exposure Sum (X + Y) vs Scenario Thresholds",
                    labels={"X+Y": "Years", "Asset": ""},
                )
                fig.add_vline(x=scenario_a, line_dash="dash", line_color="red", annotation_text="Scenario A")
                fig.add_vline(x=scenario_b, line_dash="dash", line_color="orange", annotation_text="Scenario B")
                fig.add_vline(x=scenario_c, line_dash="dash", line_color="green", annotation_text="Scenario C")
                st.plotly_chart(fig, use_container_width=True)
            
            # Not ranked
            not_ranked_profiles = [p for p in profiles if not p.asset.is_ranked]
            if not_ranked_profiles:
                st.subheader("Not Ranked Assets")
                not_ranked_data = []
                for p in not_ranked_profiles:
                    not_ranked_data.append({
                        "Asset": p.asset.asset_name,
                        "Category": p.asset.data_category,
                        "Algorithm": p.asset.algorithm,
                        "Reason": p.asset.not_ranked_reason,
                    })
                st.data_editor(
                    pd.DataFrame(not_ranked_data),
                    use_container_width=True,
                    hide_index=True,
                )
            
            # Per-asset explanations
            st.subheader("Per-Asset Explanations")
            for p in profiles:
                with st.expander(f"{p.asset.asset_name}"):
                    from qshield.report import generate_asset_explanation
                    explanation = generate_asset_explanation(p.asset, scenarios)
                    st.text(explanation)
                    
                    # Milestone overlay (P1)
                    if milestone != "none":
                        planned_year = calculate_planned_completion_year(p.asset.migration_years)
                        comparison = compare_with_milestone(planned_year, milestone)
                        if comparison:
                            st.info(f"{p.asset.asset_name}: {comparison}")
    
    # Tab 4: Roadmap
    with tab4:
        st.header("Migration Roadmap")
        
        if not st.session_state.assets:
            st.info("No assets loaded. Add assets in the Assets tab or load sample data.")
        else:
            scenarios = (scenario_a, scenario_b, scenario_c)
            roadmap = generate_roadmap(st.session_state.assets, scenarios)
            roadmap_md = format_roadmap_markdown(roadmap)
            st.markdown(roadmap_md)
            
            st.divider()
            st.info(STANDARDS_NOTE)
            
            if st.session_state.settings.org_type in ["Healthcare", "Banking and finance", "Government services"]:
                st.warning(DPDP_NOTE)
    
    # Tab 5: Report
    with tab5:
        st.header("Migration Planning Report")
        
        if not st.session_state.assets:
            st.info("No assets loaded. Add assets in the Assets tab or load sample data.")
        else:
            scenarios = (scenario_a, scenario_b, scenario_c)
            report_md = generate_markdown_report(
                org_name=st.session_state.settings.org_name,
                org_type=st.session_state.settings.org_type,
                assets=st.session_state.assets,
                scenarios=scenarios,
                milestone=st.session_state.settings.milestone,
            )
            
            st.subheader("Preview")
            st.markdown(report_md)
            
            st.subheader("Download")
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="Download Markdown Report",
                    data=report_md,
                    file_name=f"qshield_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                )
            
            with col2:
                if st.button("Download PDF Report"):
                    try:
                        pdf_path = f"qshield_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        generate_pdf_report(report_md, pdf_path)
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="Download PDF",
                                data=f,
                                file_name=pdf_path,
                                mime="application/pdf",
                            )
                    except ImportError:
                        st.error("PDF export requires fpdf2 and markdown packages. Install with: pip install fpdf2 markdown")


if __name__ == "__main__":
    main()
