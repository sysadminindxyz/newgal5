import streamlit as st
import streamlit.components.v1 as components


def main(title, icon_name, counts, changes):
    
    icon_link=f'<i class="bi bi-{icon_name}"></i>'

    colors=[]
    for cnt in changes:
        if cnt.startswith('-'): colors.append('#f44336')  # Red for negative change
        else: colors.append('#4CAF50')  # Green for positive change

    html_list = ["""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">

        <style>
        .desc {
            color: #666;
            font-size: 14px;
        }
        .source-link {
            color: #007acc;
            text-decoration: none;
            margin-right: 10px;
        }
        .source-link:hover {
            color: #005b99;
            text-decoration: underline;
        }
        </style>
        <div style="
            max-width: 800px;
            margin-left: 0;
            border: 2px solid #bbb;
            border-radius: 8px;
            overflow: hidden;
            background-color: #ffffff;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        ">
        <div style="
            background-color: #e0e0e0;
            padding: 5px 15px;
            font-weight: bold;
            font-size: 18px;
            border-bottom: 1px solid #bbb;
            color: #333;
            display: flex; 
            justify-content: space-between; 
            align-items: center;
        ">
            <div style="display: flex; align-items: center; gap: 8px;">
                <!-- Icon and Title -->
                """ + icon_link + title + f"""
            </div>
            <div style="flex-shrink: 0;">
                <table style="
                    border-collapse: collapse;
                    font-family: Arial, sans-serif;
                    font-size: 8pt;
                ">
                <tr>
                    <th style="text-align: left; padding: 1px 4px;"></th>
                    <th style="text-align: center; padding: 1px 4px;">Day</th>
                    <th style="text-align: center; padding: 1px 4px;">Week</th>
                    <th style="text-align: center; padding: 1px 4px;">Month</th>
                </tr>
                <tr>
                    <td style="text-align: left; padding: 1px 4px;">Count</td>
                    <td style="text-align: center; padding: 1px 4px;">{counts[0]}</td>
                    <td style="text-align: center; padding: 1px 4px;">{counts[1]}</td>
                    <td style="text-align: center; padding: 1px 4px;">{counts[2]}</td>
                </tr>
                <tr>
                    <td style="text-align: left; padding: 1px 4px;">Change</td>
                    <td style="color:{colors[0]}; text-align: center; padding: 1px 4px;">{changes[0]}</td>
                    <td style="color:{colors[1]}; text-align: center; padding: 1px 4px;">{changes[1]}</td>
                    <td style="color:{colors[2]}; text-align: center; padding: 1px 4px;">{changes[2]}</td>
                </tr>
                </table>
        </div>
"""
    ]                    
    return("".join(html_list))


if __name__ == "__main__":
    main()