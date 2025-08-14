import streamlit as st
from streamlit_elements import elements, mui

def main():

    with elements("newframe"):

        # You can create a draggable and resizable dashboard using
        # any element available in Streamlit Elements.

        from streamlit_elements import dashboard

        # First, build a default layout for every element you want to include in your dashboard
        import base64

        def encode_image_to_base64(image_path):
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{encoded}"

        image_src1 = encode_image_to_base64("images/social/pew_01.png")
        image_src2 = encode_image_to_base64("images/social/pew_02.png")
        image_src3 = encode_image_to_base64("images/social/pew_03.png")
        image_src4 = encode_image_to_base64("images/social/pew_04.png")
        image_src5 = encode_image_to_base64("images/social/pew_05.png")


        layout = [
            # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
            dashboard.Item("first_item", 0, 0, 3, 2),
            dashboard.Item("second_item", 3, 0, 3, 2), #isDraggable=False, moved=False),
            dashboard.Item("third_item", 6, 0, 3, 2), #isResizable=False),
            dashboard.Item("fourth_item", 0, 2, 3, 2), #isResizable=False),
            dashboard.Item("fifth_item", 3, 2, 3, 2), #isResizable=False),
        ]

        def handle_layout_change(updated_layout):
            # You can save the layout in a file, or do anything you want with it.
            # You can pass it back to dashboard.Grid() if you want to restore a saved layout.
            print(updated_layout)

        with dashboard.Grid(layout, onLayoutChange=handle_layout_change):
            # 🖼️ Image card
            mui.Card(
                key="first_item",                # ✅ Link to dashboard tile
                children=mui.CardMedia(
                    component="img",
                    image=image_src1,          # ✅ This is the correct prop for CardMedia
                    alt="My image"
                )
            )
            mui.Card(
                key="second_item",                # ✅ Link to dashboard tile
                children=mui.CardMedia(
                    component="img",
                    image=image_src2,          # ✅ This is the correct prop for CardMedia
                    alt="My image"
                )
            )
            mui.Card(
                key="third_item",                # ✅ Link to dashboard tile
                children=mui.CardMedia(
                    component="img",
                    image=image_src3,          # ✅ This is the correct prop for CardMedia
                    alt="My image"
                )
            )            
            mui.Card(
                key="fourth_item",                # ✅ Link to dashboard tile
                children=mui.CardMedia(
                    component="img",
                    image=image_src4,          # ✅ This is the correct prop for CardMedia
                    alt="My image"
                )
            )
            mui.Card(
                key="fifth_item",                # ✅ Link to dashboard tile
                children=mui.CardMedia(
                    component="img",
                    image=image_src5,          # ✅ This is the correct prop for CardMedia
                    alt="My image"
                )
            )

    tmp="https://www.pewresearch.org/science/2024/02/26/how-americans-view-weight-loss-drugs-and-their-potential-impact-on-obesity-in-the-u-s/"
    #st.html(tmp, height=370, scrolling=False)
    st.markdown("[LINK TO FULL REPORT](%s)" % tmp)


if __name__ == "__main__":
    st.set_page_config(page_title="Snacklash", page_icon="🥨", layout="wide")
    main()
