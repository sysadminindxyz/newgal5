

import json
import streamlit as st
from pathlib import Path
from streamlit.components.v1 import html as html

#st.set_page_config(page_title="Tweet Embeds")


def main():
  
  st.write(
      """
      Trending Social Posts &nbsp;
      =====================

      """
  )

def main():
    st.set_page_config(layout="wide")

    st.write(
        """
        Trending Social Posts &nbsp;
        =====================

        """
    )

    # ✅ Embedded tweet (clean, working version)

    # tweet_embed01 = """
    # <blockquote class="twitter-tweet" data-theme="dark">
    # <p lang="en" dir="ltr">This is exact same man one year apart. 
    # <br><br>Before AND After. <br><br>Ozempic is a miracle. 
    # <a href="https://twitter.com/search?q=%24NVO&amp;src=ctag&amp;ref_src=twsrc%5Etfw">$NVO</a> 
    # <a href="https://t.co/7lzFhlQcb0">pic.twitter.com/7lzFhlQcb0</a></p>&mdash; tic toc (@TicTocTick) <a href="https://twitter.com/TicTocTick/status/1946911910311371042?ref_src=twsrc%5Etfw">July 20, 2025</a></blockquote>
    # <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    # """

    tweet_embed = """
    <blockquote class="twitter-tweet" data-theme="dark">
      <p lang="en" dir="ltr">
        Mike Pompeo looks like a totally different person now.<br><br>Ozempic is wild
        <a href="https://t.co/9PIgngr7UR">pic.twitter.com/9PIgngr7UR</a>
      </p>
      &mdash; Ken Theroux (@KenTheroux)
      <a href="https://twitter.com/KenTheroux/status/1947154448637419826?ref_src=twsrc%5Etfw">
        July 21, 2025
      </a>
    </blockquote>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    """
    html(tweet_embed01, height=700, scrolling=False)



    # html(tweet_embed, height=600, scrolling=False)


if __name__ == "__main__":
    main()

