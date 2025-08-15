import streamlit as st
import streamlit.components.v1 as components


def main(title, icon_name, optional_text=""):
    
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
                padding: 8px 15px;
                font-weight: bold;
                font-size: 18px;
                border-bottom: 1px solid #bbb;
                color: #333;
            ">
        """,
        icon_link,
        title,
        """<style>
  table {
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 14px;
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
  }
  th, td {
    border-bottom: 1px solid #ddd;
    text-align: center;
    padding: 6px 8px;
  }
  th {
    background-color: #f9f9f9;
    font-weight: 600;
  }
  tr:last-child td {
    color: #4CAF50; /* green for positive change */
    font-weight: bold;
  }
</style>

<table>
  <tr>
    <th></th>
    <th>Day</th>
    <th>Week</th>
    <th>Month</th>
  </tr>
  <tr>
    <td>Articles</td>
    <td>24</td>
    <td>168</td>
    <td>710</td>
  </tr>
  <tr>
    <td>Change</td>
    <td>+5%</td>
    <td>+12%</td>
    <td>+25%</td>
  </tr>
</table>"""
        # """
        #     </div>
        # <div style="
        #     max-width: 800px;
        #     margin-left: 0;
        #     border: 2px solid #bbb;
        #     border-radius: 8px;
        #     overflow: hidden;
        #     background-color: #ffffff;
        #     box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        # ">
        #     <div style="
        #         background-color: #e0e0e0;
        #         padding: 8px 15px;
        #         font-weight: bold;
        #         font-size: 18px;
        #         border-bottom: 1px solid #bbb;
        #         color: #333;
        #     ">
        # """,
        # optional_text,
        """
            </div>
            <div style="
                height: 250px;
                overflow-y: auto;
                padding: 10px 15px;
                background-color: #f9f9f9;
            ">
        """,
    ]
    print("html_list", html_list)                    
    return("".join(html_list))


if __name__ == "__main__":
    main()