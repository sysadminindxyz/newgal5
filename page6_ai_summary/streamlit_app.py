import json
import streamlit as st
from pathlib import Path
from streamlit import session_state as state
from types import SimpleNamespace
from streamlit.components.v1 import html
import streamlit.components.v1 as components
from streamlit_elements import elements, mui, html, nivo, sync
import base64
from streamlit_elements import dashboard
from collections import defaultdict
from page1.indxyz_utils.indxyz_utils.widgetbox import main as wb

import feedparser
import base64

# topics=[
#     "Climate Change",
#     "Vaccines",
#     "AI Social Impacts",
#     "Education and Digital",
#     "Green Technology",
#     "Inequality",
#     "Global Health",
#     "Public Speaking",
#     "Collaborations",
#     "Pandemics"
# ]




#to screen grab tweet
import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from playwright.sync_api import sync_playwright
from pathlib import Path
def capture_tweet_screenshot(tweet_url: str, output_path="tweet.png"):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Load the Twitter embed URL
        page.goto(f"https://publish.twitter.com/?query={tweet_url}&widget=Tweet")

        # Wait for Twitter embed to load
        page.wait_for_selector("iframe")

        # Navigate to iframe and screenshot it
        frame = page.frame_locator("iframe").first
        tweet = frame.locator("body")
        tweet.screenshot(path=output_path)
        browser.close()

    return output_path

#for .png for pew data
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:image/jpeg;base64,{encoded}"


#for twitter
def encode_image_base64(path):
    with open(path, "rb") as f:
        return f"data:image/png;base64," + base64.b64encode(f.read()).decode()


def restructure_for_nivo_line(flat_data):
    grouped = defaultdict(list)
    
    for point in flat_data:
        grouped[point["id"]].append({"x": point["x"], "y": point["y"]})

    return [
        {"id": series_id, "data": points}
        for series_id, points in grouped.items()
    ]
    
def main():
    st.set_page_config(layout="wide")
    ###############GET DATA
    import csv
    import json
    # Open the CSV file
    with open('data/categories.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)  # Read CSV as a list of dictionaries
        data = [row for row in csv_reader]  # Convert to a list

    # Convert to JSON format
    with open('data.json', mode='w') as json_file:
        json.dump(data, json_file, indent=4)  # Write JSON with indentation for readability

    with open('data/counts.csv', mode='r') as csv_file2:
        csv_reader2 = csv.DictReader(csv_file2)  # Read CSV as a list of dictionaries
        data2 = [row for row in csv_reader2]  # Convert to a list

    # Convert to JSON format
    with open('data.json', mode='w') as json_file:
        json.dump(data2, json_file, indent=4)  # Write JSON with indentation for readability

    #GET AND SELECT LINE DATA
    line_data = restructure_for_nivo_line(data2)
    series_ids = [d["id"] for d in line_data]
    if "selected_series_event" not in st.session_state:     # --- Session state for dropdown selection ---
        st.session_state.selected_series_event = None
    if st.session_state.selected_series_event is not None:      # Extract current selection from event
        selected_series = st.session_state.selected_series_event.target.value
    else:
        selected_series = series_ids  # default to all
    filtered_data = [d for d in line_data if d["id"] in selected_series]     # Filter data

    # --- UI ---

    #print(line_data)

    with elements("newframe"):


        if "p1layout" not in state:
            p1layout = [
                # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
                #dashboard.Item("first_item", 0, 0, 2, 2),
                #dashboard.Item("tweet", 2, 0, 2, 2, isDraggable=True, isResizable=True),
                dashboard.Item("category_radar", 0, 0, 6, 4, isDraggable=True,  isResizable=True),
                dashboard.Item("count_trends", 6, 0, 6, 4, isDraggable=True,  isResizable=True),
            ]
            state.p1layout = p1layout
        else:
            p1layout = state.p1layout

        def handle_layout_change(updated_layout):
            # You can save the layout in a file, or do anything you want with it.
            # You can pass it back to dashboard.Grid() if you want to restore a saved layout.
            print(updated_layout)

        # image_src = encode_image_to_base64("images/pew_01.png")
        # twit_scr = encode_image_to_base64("images/twit_pompeo_01.png")

        # #dropdown menu
        # # Initialize session state
        # if "menu_anchor_event" not in st.session_state:
        #     st.session_state.menu_anchor_event = None
        # if "selected_series" not in st.session_state:
        #     st.session_state.selected_series = series_ids.copy()
        # st.write(st.session_state.selected_series)

        # # Determine if menu is open
        # menu_open = st.session_state.menu_anchor_event is not None
        # anchor_el = st.session_state.menu_anchor_event.target if menu_open else None
        # # Handle checkbox toggling
        # def toggle_series(series_id):
        #     if series_id in st.session_state.selected_series:
        #         st.session_state.selected_series.remove(series_id)
        #     else:
        #         st.session_state.selected_series.append(series_id)
        # #html_rendered = html(tweet01, height=300, scrolling=False)
        # #tweet01_src= encode_image_to_base64(html(tweet01, height=700, scrolling=False))
        with dashboard.Grid(p1layout, onLayoutChange=handle_layout_change):
            # mui.Card(          # 🖼️ Image card
            #     key="first_item",                # ✅ Link to dashboard tile
            #     children=mui.CardMedia(
            #         component="img",
            #         image=image_src,          # ✅ This is the correct prop for CardMedia
            #         alt="My image"
            #     )
            # )
            # mui.Card(          # 🖼️ Image card
            #     key="tweet",                # ✅ Link to dashboard tile
            #     children=mui.CardMedia(
            #         component="img",
            #         image=twit_scr,          # ✅ This is the correct prop for CardMedia
            #         alt="My image"
            #     )
            # )
            mui.Paper(
                key="category_radar",
                sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"
                    , "height": "100%", "width":"100%"},
                    #, "width": 500},
                elevation=2,
                children=[
                    mui.Box(
                        sx={
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "8px 16px",
                            "borderBottom": "1px solid #eee",
                            "backgroundColor": "#f5f5f5",
                        },
                        children=[
                            mui.icon.Radar(sx={"marginRight": 1, "color": "#333"}),
                            mui.Typography("Category Counts by Week",
                                           sx={"flex": 1,
                                               "fontWeight": 1000,
                                               "color": "#333"}
                                           ),

                        ]
                    ),
                    mui.Box(
                        sx={
                            "flex": 1,             # ⬅️ allow vertical growth
                            "minHeight": 0,        # ⬅️ prevent overflow errors
                            "display": "flex"
                        },
                        children=[
                            nivo.Radar(
                                colors=[
                                    "#B6F399","#0096FF", "#FFE600", "#00C2FF",  "#00D084",
                                      "#3F51B5", "#8C9EFF"
                                ],
                                key="first_item",
                                data=data,
                                keys=["Week of July 6", "Week of July 13"],
                                indexBy=[''],
                                valueFormat=">-.0f",
                                margin={ "top": 70, "right": 200, "bottom": 80, "left": 160 },
                                borderColor={ "from": "color" },
                                gridLabelOffset=36,
                                dotSize=10,
                                #colors="yellow_green_blue",  # ✅ set the color scheme here,
                                dotColor={ "from": "color" },
                                dotBorderColor={ "from": "color" },  # same as dot color,
                                dotBorderWidth=2,
                                motionConfig="wobbly",
                                scale={ 'type': 'log' },
                                legends=[{
                                    "anchor": "top-left",
                                    "direction": "column",
                                    "translateX": -100,
                                    "translateY": -60,
                                    "itemWidth": 80,
                                    "itemHeight": 20,
                                    "itemTextColor": "#999",
                                    "symbolSize": 12,
                                    "symbolShape": "circle",
                                    "effects": [{
                                        "on": "hover",
                                        "style": {
                                            "itemTextColor": "#000"
                                        }
                                    }]
                                }],
                                theme={
                                    "background": "#242222",
                                    "textColor": "#B6F399",
                                    "tooltip": {
                                        "container": {
                                            "background": "#0C0B0B",
                                            "color": "#E7F78E",
                                        }
                                    }
                                }
                            )
                        ]
                    )
                ]
            )
            mui.Paper(
                key="count_trends",
                sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"
                    , "height": "100%", "width":"100%"},
                    #, "width": 500},
                elevation=2,
                children=[
                    mui.Box(
                        sx={
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "8px 16px",
                            "borderBottom": "1px solid #eee",
                            "backgroundColor": "#f5f5f5",
                        },
                        children=[
                            mui.icon.Line(sx={"marginRight": 1, "color": "#333"}),
                            mui.Typography("Tweets and Engagement",
                                           sx={"flex": 1,
                                               "fontWeight": 1000,
                                               "color": "#333"}
                                           ),

                        ]
                    ),
                    mui.Box(
                        sx={
                            "flex": 1,             # ⬅️ allow vertical growth
                            "minHeight": 0,        # ⬅️ prevent overflow errors
                            "display": "flex"
                        },
                        children=[
                            nivo.Line(
                                key="second_item",
                                #key="my_line_chart",
                                data=filtered_data,
                                colors=[
                                    "#B6F399", "#0096FF", "#FFE600", "#00C2FF", "#00D084",
                                    "#3F51B5", "#8C9EFF"
                                ],
                                margin={"top": 50, "right": 110, "bottom": 50, "left": 60},
                                xScale={"type": "point"},
                                yScale={"type": "linear", "min": "auto", "max": "auto", "reverse": False},
                                axisBottom={"orient": "bottom", "legend": "Month", "legendOffset": 36},
                                axisLeft={"orient": "left", "legend": "Value", "legendOffset": -40},
                                pointSize=10,
                                pointColor={"from": "color"},
                                pointBorderWidth=2,
                                pointBorderColor={"from": "color"},
                                useMesh=True,
                                legends=[{
                                    "anchor": "bottom-right",
                                    "direction": "column",
                                    "translateX": 100,
                                    "itemWidth": 80,
                                    "itemHeight": 20,
                                    "symbolSize": 12,
                                    "symbolShape": "circle",
                                }],
                                theme={
                                    "background": "#242222",
                                    "textColor": "#B6F399",
                                    "tooltip": {
                                        "container": {
                                            "background": "#0C0B0B",
                                            "color": "#E7F78E",
                                        }
                                    }
                                }                            )
                        ]
                    )
                ]
            )
            # mui.Paper(
            #     key="line_chart_tile",
            #     sx={
            #         "display": "flex",
            #         "flexDirection": "column",
            #         "borderRadius": 3,
            #         "overflow": "hidden",
            #         "height": "400pt", #"100%"
            #         "width":"100%",
            #     },
            #     elevation=2,
            #     children=[
            #         # Title Bar
            #         mui.Box(
            #             sx={
            #                 "display": "flex",
            #                 "alignItems": "center",
            #                 "padding": "8px 16px",
            #                 "borderBottom": "1px solid #eee",
            #                 "backgroundColor": "#f5f5f5",
            #                 #"height": "400pt",
            #             },
            #             children=[
            #                 mui.icon.SsidChart(sx={"marginRight": 1, "color": "#333"}),
            #                 mui.Typography("Tweets and Engagement",
            #                                sx={"flex": 1,
            #                                    "fontWeight": 1000,
            #                                    "color": "#333"}
            #                                ),
            #                 # mui.IconButton(mui.icon.MoreVert,
            #                 #                onClick=sync("menu_anchor_event"),
            #                 #                sx={"flex": 1,
            #                 #                    "fontWeight": 1000,
            #                 #                    "color": "#333"}
            #                 #                ),
            #                 # mui.Menu(
            #                 #     #anchorEl=anchor_el,
            #                 #     #open=menu_open,
            #                 #     onClose=lambda: st.session_state.__setitem__("menu_anchor_event", None),
            #                 #     children=[
            #                 #         mui.MenuItem(
            #                 #             onClick=lambda sid=series_id: toggle_series(sid),
            #                 #             children=[
            #                 #                 mui.Checkbox(checked=series_id in st.session_state.selected_series),
            #                 #                 mui.ListItemText(primary=series_id)
            #                 #             ]
            #                 #         )
            #                 #         for series_id in series_ids
            #                 #     ]
            #                 # ),        
            #                 # mui.Box(
            #                 #     sx={"marginBottom": 2, "width": 300},
            #                 #     children=mui.FormControl(
            #                 #         fullWidth=True,
            #                 #         children=[
            #                 #             mui.InputLabel("Select Series"),
            #                 #             mui.Select(
            #                 #                 multiple=True,
            #                 #                 value=selected_series,
            #                 #                 onChange=sync("selected_series_event"),
            #                 #                 renderValue=lambda selected: ", ".join(selected),
            #                 #                 children=[
            #                 #                     mui.MenuItem(
            #                 #                         value=series_id,
            #                 #                         children=[
            #                 #                             mui.Checkbox(checked=series_id in selected_series),
            #                 #                             mui.ListItemText(primary=series_id)
            #                 #                         ]
            #                 #                     )
            #                 #                     for series_id in series_ids
            #                 #                 ]
            #                 #             )
            #                 #         ]
            #                 #     )
            #                 # )
            #             ]
            #         ),
            #         # Chart container
            #         mui.Box(
            #             sx={
            #                 "flex": 1,
            #                 "minHeight": 0,
            #                 "display": "flex",
            #                 "height": "200pt", #"100%",
            #             },
            #             children=[
            #                 nivo.Line(
            #                     key="my_line_chart",
            #                     data=filtered_data,
            #                     colors=[
            #                         "#B6F399", "#0096FF", "#FFE600", "#00C2FF", "#00D084",
            #                         "#3F51B5", "#8C9EFF"
            #                     ],
            #                     margin={"top": 50, "right": 110, "bottom": 50, "left": 60},
            #                     xScale={"type": "point"},
            #                     yScale={"type": "linear", "min": "auto", "max": "auto", "reverse": False},
            #                     axisBottom={"orient": "bottom", "legend": "Month", "legendOffset": 36},
            #                     axisLeft={"orient": "left", "legend": "Value", "legendOffset": -40},
            #                     pointSize=10,
            #                     pointColor={"from": "color"},
            #                     pointBorderWidth=2,
            #                     pointBorderColor={"from": "color"},
            #                     useMesh=True,
            #                     legends=[{
            #                         "anchor": "bottom-right",
            #                         "direction": "column",
            #                         "translateX": 100,
            #                         "itemWidth": 80,
            #                         "itemHeight": 20,
            #                         "symbolSize": 12,
            #                         "symbolShape": "circle",
            #                     }],
            #                     theme={
            #                         "background": "#242222",
            #                         "textColor": "#B6F399",
            #                         "tooltip": {
            #                             "container": {
            #                                 "background": "#0C0B0B",
            #                                 "color": "#E7F78E",
            #                             }
            #                         }
            #                     }
            #                 )
            #             ]
            #         )
            #     ]
            # )

    pdf_url="http://3.85.37.226:9000/exec_sum.pdf"
    href = f'<a href="{pdf_url}" target="_blank" class="summary-link">Full Report</a>'

    html_executive_summary = [wb(" Real-Time AI Reporting", "robot")]
    html_executive_summary.append("""
        </div>
        <div style="
            height: 250px;
            overflow-y: auto;
            padding: 10px 15px;
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

    # st.markdown("""
    #         <style>
    #             [data-testid="stVerticalBlock"] { gap: .1rem; }
    #             section.main > div.block-container { padding-top: 0rem; }
    #         </style>   
    #             """,unsafe_allow_html=True)         
    components.html(summary_widget_html, height=370, scrolling=False)       

if __name__ == "__main__":
    main()


