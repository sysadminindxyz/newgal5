import streamlit as st
import streamlit.components.v1 as components


def main(title, icon_name, optional_text=""):
    
    icon_link=f'<i class="bi bi-{icon_name}"></i>'

    html_list = ["""
<div style="
    background-color: #e0e0e0;
    padding: 8px 15px;
    font-weight: bold;
    font-size: 18px;
    border-bottom: 1px solid #bbb;
    color: #333;
    display: flex; 
    justify-content: space-between; 
    align-items: center;
">
    <!-- Left side: icon + title -->
    <div style="display: flex; align-items: center; gap: 8px;">
        """ + icon_link + title + """
    </div>

    <!-- Right side: table -->
    <div style="flex-shrink: 0;">
        <table style="
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            font-size: 8pt;
        ">
          <tr>
            <th style="padding: 2px 16px;"></th>
            <th style="padding: 2px 16px;">Day</th>
            <th style="padding: 2px 16px;">Week</th>
            <th style="padding: 2px 16px;">Month</th>
          </tr>
          <tr>
            <td style="padding: 2px 16px;">Articles</td>
            <td style="padding: 2px 16px;">24</td>
            <td style="padding: 2px 16px;">168</td>
            <td style="padding: 2px 16px;">710</td>
          </tr>
          <tr>
            <td style="padding: 4px 16px;"></td>
            <td style="color:#4CAF50; padding: 2px 16px;">+5%</td>
            <td style="color:#4CAF50; padding: 2px 16px;">+12%</td>
            <td style="color:#4CAF50; padding: 2px 16px;">+25%</td>
          </tr>
        </table>
    </div>
</div>
        """,
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
   #print("html_list", html_list)                    
    return("".join(html_list))


if __name__ == "__main__":
    main()