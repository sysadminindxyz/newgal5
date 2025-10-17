import streamlit as st
import streamlit.components.v1 as components
import csv
import base64
import os
import re
import sys
import json
from .indxyz_utils.indxyz_utils.widgetbox import main as wb

from .parse_rss import rss_as_tuples


def get_issues(source_type, time_selection):
    return [  
        (
            "GLP‑1 Drug Supply & Market Pressures",
            "Rising demand for Ozempic and related injections led to concerns about shortages, regulatory changes, and competitive pressures on manufacturers like Novo Nordisk.",
            [
                ("The Sun+15", "https://www.thesun.co.uk/health/36039142/fat-weight-loss-jab-supplies-running-out/"),
                ("Harvard Health+15", "#"),
                ("Axios+15", "#")
            ]
        ),
        (
            "Corporate Turmoil & Financial Downturn",
            "Novo Nordisk’s shares dropped sharply, profit forecasts were revised downward, and leadership changes were announced amid increasing competition.",
            [
                ("The Business of Fashion", "https://www.businessoffashion.com/articles/workplace-talent/plus-size-models-fashion-industry-slowdown-90s-thinness-ozempic"),
                ("The Times", "#")
            ]
        ),
        (
            "Health Risks & Legal Risks",
            "Patients report significant side effects (e.g. gallbladder issues, nausea), raising mounting legal claims and concerns around off-label usage.",
            [("ScienceDirect", "https://www.sciencedirect.com/science/article/pii/S2667118224000163")]
        ),
        (
            "Eating Disorders & Ethical Dilemmas",
            "GLP‑1 use off-label is linked with relapse or emergence of eating disorders, especially in patients previously diagnosed with body image issues.",
            [ ("Business Insider+15", "https://www.businessinsider.com/ozempic-driving-a-new-eating-disorder-crisis-in-the-us-2025-7")
             ,("AInvest+15", "#"), ("ScienceDirect+15", "#")]
        ),
        (
            "Promising Cognitive Benefits",
            "Emerging research suggests GLP‑1 drugs like Ozempic may reduce dementia risk and mortality in older adults with type 2 diabetes compared to metformin.",
            []
        ),
        (
            "Weight‑loss Testimonials & Before‑and‑Afters",
            "Influencers and consumers frequently post Ozempic success stories showing dramatic weight loss results and calorie tracking journeys.",
            [ ("Innova Market Insights+15", "https://www.innovamarketinsights.com/trends/weight-loss-trends/"), ("The Sun+15", "#"), ("The Wall Street Journal+15", "#")]
        ),
        (
            "DIY Dosages & Microdosing Trends",
            "A growing movement promotes microdosing routines based on influencer advice, despite medical professionals warning of risks.",
            [("EMARKETER", "https://www.emarketer.com/content/microdosing-latest-social-media-driven-ozempic-trend")]
        ),
        (
            "Insurance Frustrations & Access Barriers",
            "Many users discuss denied coverage for off-label use, lack of prescriptions without diabetes diagnosis, and high out-of-pocket cost concerns.",
            [("ScienceDirect+1", "https://www.sciencedirect.com/science/article/pii/S2667118224000163"), ("PMC+1", "#")]
        ),
        (
            "Side‑Effect Management & Real‑Life Tips",
            "Social media posts focus extensively on managing GI upset, nausea, and medication storage, with peer advice exchanged in forums.",
            [("FoodNavigator.com+5", "https://www.foodnavigator.com/Article/2024/06/19/trends-in-better-for-you-snacking-for-mars-nestle-mondelez-ferrero/"),
             ("Real California Milk+5", "#"), ("The Times of India+5", "#"), ("PMC+1", "#"), ("The Wall Street Journal+1", "#")]
        ),
        (
            "Ethical & Cosmetic Pressure",
            "Discussions critique how Ozempic is used culturally to promote extreme thinness and body aesthetic conformity beyond medical necessity.",
            [("Reddit+8", "https://www.reddit.com/r/TwoXChromosomes/comments/1h4gfmn/unpopular_opinion_but_i_feel_like_the_ozempic/"), ("The Independent", "#"), ("Innova Market Insights+8", "#"),  ("ScienceDirect+8", "#")]
        )

    ]


def main():

    data=get_issues("News+Social Media", "Past Week")

    #print(data)
    # === Render Top Issues Widget HTML ===
    html_parts = [wb(" Top Issues", "newspaper")]

    html_parts.append("""
            </div>
            <div style="
                height: 300px;
                overflow-y: auto;
                padding: 00px 15px;
                background-color: #f9f9f9;
                font-family: Arial, sans-serif; /* ← Added font family */

            ">
        """)
    html_parts.append("""
 
    <ol style="margin-left: -30px; margin-bottom: 10px;" type="1">
    """)

    for issue, desc, source in (
        ( row[0], row[1], row[2]) 
        for row in data
    ):
        html_parts.append(f"""
            <li style= "margin-top: 10px; margin-bottom: 10px;">
                <strong>{issue}</strong>
                <div style="padding-left: 16px; margin-top: 5px; margin-bottom: 15px;">
                    <div class="desc">{desc}</div>
                    <div>
        """)
        for sourcename, url in source:
            if url.startswith("#"):
                html_parts.append(f' {sourcename}')
            else:
                html_parts.append(f'<a class="source-link" href="{url}" target="_blank">{sourcename}</a>')

        html_parts.append("</div></div></li>")
    
    html_parts.append("</ol>")

    return("".join(html_parts))


if __name__ == "__main__":
    main()