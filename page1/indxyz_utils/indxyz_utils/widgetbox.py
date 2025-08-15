import streamlit as st
import streamlit.components.v1 as components


def main(title, icon_name):
    
    icon_link=f'<i class="bi bi-{icon_name}"></i>'

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
                padding: 18px 15px;
                font-family: Arial, sans-serif; /* ← Added font family */
                font-weight: bold;
                font-size: 18px;
                border-bottom: 1px solid #bbb;
                color: #333;
            ">
        """,
        icon_link,
        title, "<!-- You can add more HTML here if needed -->",
    ]                    
    return("".join(html_list))


if __name__ == "__main__":
    main()