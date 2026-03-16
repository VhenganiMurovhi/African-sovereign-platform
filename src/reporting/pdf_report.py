from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
import pandas as pd


def _safe_fmt(value, decimals=2):
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def build_country_risk_report(
    latest_row: pd.Series,
    country_history: pd.DataFrame,
    output_path: str
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#13315C"),
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=18
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#13315C"),
        spaceAfter=8,
        spaceBefore=10
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    story = []

    country_name = latest_row.get("country_name", "Unknown Country")
    year = latest_row.get("year", "N/A")

    story.append(Paragraph("African Sovereign Risk Intelligence Platform", title_style))
    story.append(
        Paragraph(
            f"Country Risk Report — {country_name} | Latest scored year: {year}",
            subtitle_style
        )
    )

    story.append(Paragraph("Executive Summary", section_style))

    risk_score = _safe_fmt(latest_row.get("sovereign_risk_score"))
    risk_band = latest_row.get("risk_band", "Unknown")

    summary_text = (
        f"This report provides a snapshot of sovereign macroeconomic risk for "
        f"<b>{country_name}</b>. The latest available sovereign risk score is "
        f"<b>{risk_score}</b>, classified as <b>{risk_band}</b>. "
        f"The assessment is based on macroeconomic indicators, structural conditions, "
        f"and a composite weighted risk scoring framework."
    )
    story.append(Paragraph(summary_text, body_style))

    story.append(Paragraph("Latest Macro Snapshot", section_style))

    snapshot_data = [
        ["Metric", "Value"],
        ["Latest Scored Year", str(year)],
        ["Sovereign Risk Score", risk_score],
        ["Risk Band", str(risk_band)],
        ["GDP Growth (%)", _safe_fmt(latest_row.get("gdp_growth"))],
        ["Inflation (%)", _safe_fmt(latest_row.get("inflation"))],
        ["Debt to GDP (%)", _safe_fmt(latest_row.get("debt_to_gdp"))],
        ["Exports to GDP (%)", _safe_fmt(latest_row.get("exports_to_gdp"))],
        ["Imports to GDP (%)", _safe_fmt(latest_row.get("imports_to_gdp"))],
        ["FDI % GDP", _safe_fmt(latest_row.get("fdi_pct_gdp"))],
        ["Electricity Access (%)", _safe_fmt(latest_row.get("electricity_access"))],
        ["Unemployment (%)", _safe_fmt(latest_row.get("unemployment"))],
    ]

    snapshot_table = Table(snapshot_data, colWidths=[75 * mm, 75 * mm])
    snapshot_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#13315C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D0D9")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7F9FC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7F9FC"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(snapshot_table)

    story.append(Paragraph("Risk Pillar Breakdown", section_style))

    pillar_data = [
        ["Pillar", "Score"],
        ["Debt Sustainability", _safe_fmt(latest_row.get("debt_sustainability"))],
        ["Macro Stability", _safe_fmt(latest_row.get("macro_stability"))],
        ["External Vulnerability", _safe_fmt(latest_row.get("external_vulnerability"))],
        ["Growth Capacity", _safe_fmt(latest_row.get("growth_capacity"))],
        ["Development Capacity", _safe_fmt(latest_row.get("development_capacity"))],
    ]

    pillar_table = Table(pillar_data, colWidths=[95 * mm, 55 * mm])
    pillar_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4E89")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D0D9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EEF4FA"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(pillar_table)

    story.append(Paragraph("Recent Historical View", section_style))

    history_cols = [
        "year",
        "sovereign_risk_score",
        "risk_band",
        "gdp_growth",
        "inflation",
        "debt_to_gdp"
    ]

    history_df = country_history[history_cols].copy().sort_values("year", ascending=False).head(8)

    history_rows = [["Year", "Risk Score", "Risk Band", "GDP", "Inflation", "Debt/GDP"]]
    for _, row in history_df.iterrows():
        history_rows.append([
            str(int(row["year"])) if pd.notna(row["year"]) else "N/A",
            _safe_fmt(row.get("sovereign_risk_score")),
            str(row.get("risk_band", "Unknown")),
            _safe_fmt(row.get("gdp_growth")),
            _safe_fmt(row.get("inflation")),
            _safe_fmt(row.get("debt_to_gdp")),
        ])

    history_table = Table(
        history_rows,
        colWidths=[20 * mm, 28 * mm, 32 * mm, 22 * mm, 24 * mm, 24 * mm]
    )
    history_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#13315C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D0D9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7F9FC"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(history_table)

    story.append(Spacer(1, 12))

    methodology = (
        "Methodology note: The sovereign risk score is a composite indicator built "
        "from macroeconomic and structural variables. Higher scores indicate higher "
        "relative risk within the selected country set. Scores should be interpreted "
        "as analytical signals rather than official sovereign ratings."
    )
    story.append(Paragraph("Methodology Note", section_style))
    story.append(Paragraph(methodology, body_style))

    doc.build(story)
    return str(output_path)