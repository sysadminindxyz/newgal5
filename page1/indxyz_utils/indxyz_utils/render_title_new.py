
import base64
import streamlit as st


def render_title(title):

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
            f"""
            <div style='text-align: right;'>
                <img src="data:image/png;base64,{popai_base64}" width='200'>
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
                background-color:#5050C6;
                padding: 5px 5px;
                #-webkit-text-stroke: 1px #6E3F18;
                #border: 2px solid #627C7E;
                border-radius: 10px;
                #margin-top: 10px;
                font-family:Helvetica;
                font-size:32px;
                color:#FFF8ED;
                font-weight: bold;
                text-align: center; 
                #max-width: 100%;
                #word-wrap: break-word;
            '>{title}</div>
            """,
            unsafe_allow_html=True
        )
    with header_col3: 
        st.markdown(
            f"""
            <div style='text-align: left;'>
                <img src="data:image/png;base64,{mercury_base64}" width='150'>
            </div>
            """,
            unsafe_allow_html=True
        )
