#page1/streamlit_app.py
import streamlit as st
import streamlit.components.v1 as components
import csv
import base64
import os
import re
import sys
import json
from .widget1 import main as widget1
from .widget2 import main as widget2
from .widget3 import main as widget3
from .indxyz_utils.indxyz_utils.widgetbox import main as wb
from  .debug_tweets import show_recent_tweet_urls


# # Add the absolute path to central-pipeline to sys.path
# central_pipeline_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..', 'central-pipeline'))
# sys.path.append(central_pipeline_path)
# from indxyz_utils.widgetbox import main as wb


def main(): 


    def get_base64_image(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()

    pew6_base64= get_base64_image("images/social/pew6.png")
    pew7_base64= get_base64_image("images/social/pew7.png") 

    # === State Initialization ===
    if "time_selection" not in st.session_state:
        st.session_state["time_selection"] = "Past Week"

    # # === Sidebar Layout ===
    # with st.sidebar:
    #     st.title("Dashboard Filters")
    #     # === Toggle for Source Type ===
    #     source_type = st.radio("Media Types:", ["News+Social Media", "News Media", "Social Media"], horizontal=False)
    #     time_options = st.radio("Timeframe:", ["Past 24 hr", "Past Week", "Past Month"], horizontal=False)

    # === JS Listener for Updating Time Filter ===
    components.html("""
        <script>
        window.addEventListener("message", (event) => {
            if (event.data.time) {
                const streamlitEvent = new CustomEvent("streamlit:setComponentValue", {
                    detail: {key: "time_selection", value: event.data.time}
                });
                window.dispatchEvent(streamlitEvent);
            }
        });
        </script>
    """, height=0)


    #ISSUES
    issue_widget_html = widget1()

    #NEWS
    news_widget_html = widget2()

    #SOCIAL
    social_widget_html= widget3()

    #PUBLIC OPINION


    html_public_opinion = [wb(" Public Opinion", "chat-text")]
    html_public_opinion.append(f"""
             </div>
    <div style="
        height: 250px;
        overflow-y: auto;
        padding: 10px 15px;
        background-color: #f9f9f9;
    ">
            <div style='margin-bottom: 20px;'>
            <center>
            <a href="https://www.pewresearch.org/science/2024/02/26/how-americans-view-weight-loss-drugs-and-their-potential-impact-on-obesity-in-the-u-s/" target="_blank" rel="noopener noreferrer">
            <img src="data:image/png;base64,{pew6_base64}"
                style="max-width:100%; height:auto; display:block; cursor:pointer;">
            </a>
            </center>
            </div>
    """)


    opinion_widget_html="".join(html_public_opinion)




     #VULNERABILITIES
    # === Dummy Data Refresh (on every interaction) ===
    vulnerabilities = get_vulnerabilities("","")

    # === News Widget HTML ===
    html_parts_vulnerabilities = [wb(" Vulnerabilities", "exclamation-triangle")]
    html_parts_vulnerabilities.append("""
            </div>
            <div style="
                height: 250px;
                overflow-y: auto;
                padding: 10px 40px;
                background-color: #f9f9f9;
                font-family: Arial, sans-serif; /* ← Added font family */

            ">
        """)
    for title, desc, implication in vulnerabilities:
        html_parts_vulnerabilities.append(f"""
            <li style="margin-left: -30px; margin-bottom: 10px; list-style-type:none;">
                <strong>{title}</strong>
                <ul style="padding-left: 46px; margin-top: 5px;">
                    <li>
                        <span class="desc">{desc}</span><br>
        """)
        html_parts_vulnerabilities.append(f'{implication}')
        html_parts_vulnerabilities.append("""</li></ul></li>""")
    
    vulnerabilities_widget_html = "".join(html_parts_vulnerabilities)


    # # EXECUTIVE SUMMARY WIDGET
    #with open("static/exec_sum.pdf", "rb") as f:
    #    b64_pdf = base64.b64encode(f.read()).decode()

    #href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="Executive_Summary.pdf" class="summary-link">Full Report</a>'
    pdf_url="http://3.85.37.226:9000/exec_sum.pdf"
    href = f'<a href="{pdf_url}" target="_blank" class="summary-link", color="#1396cc">Full Report</a>'

    html_executive_summary = [wb(" Real-Time AI Reporting", "robot")]
    html_executive_summary.append("""
        </div>
        <div style="
            height: 250px;
            overflow-y: auto;
            padding: 18px 15px;
            background-color: #f9f9f9;
            font-family: Arial, sans-serif; /* ← Added font family */
        ">
    """)
    html_executive_summary.append(f"""
        <ul style="padding-left: 18px; margin: 0;">
        Recent shifts in public behavior related to GLP-1 drugs (e.g., Ozempic, Wegovy, Mounjaro) are signaling a notable decline in snack food consumption across key demographics. Analysis of social media conversations, influencer commentary, and digital news articles from January–June 2025 suggests an accelerating cultural association between GLP-1 usage and "mindful eating" or reduced snacking behavior...        {href}
        </ul>
    </div>
    </div>
    """)
    summary_widget_html="".join(html_executive_summary)

    st.markdown("""
            <style>
                [data-testid="stVerticalBlock"] { gap: 0rem; }
                section.main > div.block-container { padding-top: 0px; }
            </style>
        """, unsafe_allow_html=True)
    row1 = st.columns(3)




    # === Layout ROW 1===
    with st.container():
        st.markdown("<div style='margin-bottom: 0px; margin-top: 0px'>", unsafe_allow_html=True)

        with row1[0]:
            components.html(issue_widget_html, height=365, scrolling=False)
        with row1[1]:
            components.html(news_widget_html, height=365, scrolling=False)

        with row1[2]:
            components.html(social_widget_html, height=365, scrolling=False)



    # Construct a download/open link (assumes you're running Streamlit locally)
    # === Layout ROW 2===
    with st.container():
        row2 = st.columns(3)
        with row2[0]:
            components.html(opinion_widget_html, height=370, scrolling=False)
        with row2[1]:
            components.html(vulnerabilities_widget_html, height=370, scrolling=False)
        with row2[2]:
            components.html(summary_widget_html, height=370, scrolling=False)


def get_vulnerabilities(source_type, time_selection):
    return [  
        (
            "⚠️ 1. Cost and Accessibility",
            "GLP-1 medications remain prohibitively expensive for many, especially without insurance coverage — costing upwards of $1,000/month in the U.S.",
            "Limits adoption to higher-income or well-insured populations, undermining equity and mass market penetration."
        ),
        (
            "⚠️ 2. Supply Constraints and Manufacturing Bottlenecks",
            "Demand has outpaced supply globally, leading to shortages, prescription delays, and rationing of doses.",
            "Unreliable availability creates frustration, erodes trust, and slows adoption — especially for new users or non-prioritized patients."
        ),
        (
            "⚠️ 3. Long-Term Safety Unknowns",
            "Many patients are now taking GLP-1s for years, but long-term health consequences (on organs, nutrient absorption, fertility, etc.) remain under-researched.",
            "Hesitation among doctors, regulators, and consumers may intensify as real-world longitudinal data comes in."
        ),
        (
            "⚠️ 4. Side Effects and Dropout Rates",
            "Nausea, vomiting, gallbladder issues, muscle loss, and even psychological side effects (e.g., depression or ED relapse) are increasingly reported.",
            "High dropout rates (up to 50% in some studies) could limit sustained benefit and raise concerns about over-reliance."
        ),
        (
            "⚠️ 5. Medicalization of Weight Loss & Ethical Backlash",
            "Critics argue GLP-1s promote a pharmacological solution to a social and systemic issue (obesity), while marginalizing those with eating disorders or body diversity.",
            "Cultural and ethical pushback (especially from younger or body-positive communities) could constrain reputational support and policy expansion."
        ),
        (
            "⚠️ 6. Rebound Weight Gain After Discontinuation",
            "Studies show most patients regain a significant portion of lost weight when they stop taking GLP-1s.",
            "Undermines perception of long-term efficacy and raises questions about creating drug dependency for metabolic control."
        ),
        (
            "⚠️ 7. Off-Label Use and Legal Risk",
            "Widespread use by people without diabetes or clinical obesity — especially via telehealth and influencer endorsements — raises liability concerns.",
            "Regulatory scrutiny, litigation, and insurer backlash may emerge as unintended consequences of overly aggressive adoption."
        ),
        (
            "⚠️ 8. Food & Beverage Industry Disruption",
            "Reduced appetite and food consumption among users is already impacting packaged food, beverage, and restaurant sectors.",
            "Broader economic ripple effects could provoke industry lobbying against coverage or promotion of GLP-1s at scale."
        ),
        (
            "⚠️ 9. Insurance Resistance and Coverage Gaps",
            "Payers are pushing back on non-diabetic prescriptions and weight-loss-only use; some states and plans have banned coverage altogether.",
            "Without systemic coverage, adoption remains slow or inequitable — especially in public or employer health plans."
        ),
        (
            "⚠️ 10. Social Inequality and Public Perception",
            "The drugs are increasingly seen as tools of affluent vanity rather than public health — especially in communities with limited access.",
            "Can drive stigma, resentment, and political backlash if adoption is seen as elitist or skewed."
        )
    ]


if __name__ == "__main__":
    main()