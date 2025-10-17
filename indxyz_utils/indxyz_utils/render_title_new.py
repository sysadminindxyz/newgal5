
import base64
import streamlit as st
import streamlit.components.v1 as components


def render_title(title, subtitle=""):

    #GET IMAGES IN BASE64
    def get_base64_image(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()

    mercury_base64 = get_base64_image("images/mercury.png")
    popai_base64 = get_base64_image("images/popai.png")
    #pew6_base64= get_base64_image("images/pew6.png")
    #pew7_base64= get_base64_image("images/pew7.png")

    header_col1, header_col2, header_col3 = st.columns([2, 6,2])

    with header_col1:
        st.markdown(
            f""" <div style='text-align: left;
                            font-family:Avenir Next LT Pro Light, sans-serif;
                            font-size:14px;   
                            font-weight: bold;
                            margin-top: -40px;
                            font-color:#1396cc;
                            '>
                Powered by:</div>
            <div style='text-align: left;'>
                <img src="data:image/png;base64,{popai_base64}" width='80'>
            </div>
            """,
            unsafe_allow_html=True
        )

    with header_col2:
        st.markdown(
            f"""
            <div style='
                #display: inline-block;
                justify-content: space-between;
                align-items: center;        
                background-color:#FFFFFF;
                #padding: -50px 5px;
                #-webkit-text-stroke: 1px #6E3F18;
                #border: 2px solid #627C7E;
                #border-radius: -10px;
                margin-top: -50px;
                font-family:Avenir Next LT Pro Light, sans-serif;
                font-size:45px;
                color:#1396cc;
                #font-weight: bold;
                text-align: center; 
                #max-width: 100%;
                #word-wrap: break-word;
            '>{title}</div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div style='
                #display: inline-block;
                justify-content: space-between;
                align-items: center;        
                background-color:#FFFFFF;
                margin-bottom: 20px;
                font-family:Aptos Mono, sans-serif;
                font-size:20px;
                font-weight: bold;
                color:#302929;
                text-align: center; 
                #max-width: 100%;
                #word-wrap: break-word;
            '>{subtitle}</div>
            """,
            unsafe_allow_html=True
        )

    with header_col3: 

        html_parts= []
        # html_parts.append(subtitle)
        # components.html(subtitle)

        # st.markdown(
        #     f"""
        #     """)
        # #     <div style='text-align: left;'>
        # #         <img src="data:image/png;base64,{mercury_base64}" width='110'>
        # #     </div>
        # #      <a href="https://researchresultswebsite.com/" target="_blank" rel="noopener noreferrer">
        # #          \n Mercury Workbench

        # #     """,
        # #     unsafe_allow_html=True
        # # )
