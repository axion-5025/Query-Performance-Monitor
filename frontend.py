import html
import pandas as pd
import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Query Monitor",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = "http://127.0.0.1:8000"


# ============================================================
# API HELPERS
# ============================================================

def api_get(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()

    except requests.RequestException:
        pass

    return None


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def ms(value):
    return num(value) * 1000


def fmt_ms(value):
    return f"{ms(value):.2f} ms"


def query_text(query):
    return str(
        query.get(
            "query_text",
            "Unknown query",
        )
    )


def status(value):
    execution_ms = ms(value)

    if execution_ms < 10:
        return "Fast"

    if execution_ms <= 20:
        return "Medium"

    return "Slow"


def badge_class(value):
    current = status(value)

    if current == "Fast":
        return "fast"

    if current == "Medium":
        return "medium"

    return "slow"


# ============================================================
# SPARKLINE
# ============================================================

def sparkline(values, color="#1769ff"):

    values = [
        num(value)
        for value in values
    ]

    if not values:
        values = [0, 0]

    if len(values) == 1:
        values = [values[0], values[0]]

    width = 100
    height = 38
    padding = 3

    low = min(values)
    high = max(values)

    span = high - low or 1

    points = []

    for index, value in enumerate(values):

        x = (
            padding
            + index
            * (width - padding * 2)
            / (len(values) - 1)
        )

        y = (
            height
            - padding
            - (
                (value - low)
                / span
            )
            * (height - padding * 2)
        )

        points.append(
            f"{x:.1f},{y:.1f}"
        )

    points_string = " ".join(points)

    return (
        f'<svg class="spark" '
        f'viewBox="0 0 {width} {height}">'
        f'<polyline '
        f'points="{points_string}" '
        f'fill="none" '
        f'stroke="{color}" '
        f'stroke-width="2.4" '
        f'stroke-linecap="round" '
        f'stroke-linejoin="round" />'
        f'</svg>'
    )


# ============================================================
# GET BACKEND DATA
# ============================================================

queries = api_get("/queries")

if not isinstance(queries, list):
    queries = []


stats = api_get("/queries/stats")


if not isinstance(stats, dict):

    times = [
        num(
            query.get(
                "execution_time"
            )
        )
        for query in queries
    ]

    if times:

        average = sum(times) / len(times)

        fastest = min(
            queries,
            key=lambda query: num(
                query.get(
                    "execution_time"
                )
            ),
        )

        slowest = max(
            queries,
            key=lambda query: num(
                query.get(
                    "execution_time"
                )
            ),
        )

    else:

        average = 0
        fastest = None
        slowest = None

    stats = {
        "total_queries": len(queries),
        "average_execution_time": average,
        "fastest_query": fastest,
        "slowest_query": slowest,
    }


total_queries = stats.get(
    "total_queries",
    len(queries),
)

average_time = stats.get(
    "average_execution_time",
    0,
)


fastest_query = stats.get(
    "fastest_query"
)

slowest_query = stats.get(
    "slowest_query"
)


if not isinstance(
    fastest_query,
    dict,
):
    fastest_query = None


if not isinstance(
    slowest_query,
    dict,
):
    slowest_query = None


fastest_time = (
    fastest_query.get(
        "execution_time",
        0,
    )
    if fastest_query
    else 0
)


slowest_time = (
    slowest_query.get(
        "execution_time",
        0,
    )
    if slowest_query
    else 0
)


fast_count = sum(
    1
    for query in queries
    if status(
        query.get(
            "execution_time"
        )
    ) == "Fast"
)


medium_count = sum(
    1
    for query in queries
    if status(
        query.get(
            "execution_time"
        )
    ) == "Medium"
)


slow_count = sum(
    1
    for query in queries
    if status(
        query.get(
            "execution_time"
        )
    ) == "Slow"
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   STREAMLIT RESET
   ========================================================== */

#MainMenu {
    display: none !important;
}

footer {
    display: none !important;
}

header[data-testid="stHeader"] {
    display: none !important;
}

div[data-testid="stToolbar"] {
    display: none !important;
}

section[data-testid="stSidebar"] {
    display: none !important;
}

div[data-testid="stAppViewContainer"] {
    background: #f6f8fb !important;
}

div[data-testid="stAppViewContainer"] > section {
    background: #f6f8fb !important;
}

div[data-testid="stMain"] {
    background: #f6f8fb !important;
}

div[data-testid="stMainBlockContainer"] {
    max-width: 1480px !important;
    padding-top: 0 !important;
    padding-bottom: 40px !important;
    padding-left: 28px !important;
    padding-right: 28px !important;
}


/* ==========================================================
   REMOVE EXTRA TOP SPACE
   ========================================================== */

div[data-testid="stAppViewContainer"] > div:first-child {
    padding-top: 0 !important;
}

div[data-testid="stMainBlockContainer"] > div:first-child {
    margin-top: 0 !important;
}


/* ==========================================================
   HEADER
   ========================================================== */

.qm-header {
    width: 100%;
    background: #ffffff;
    border-bottom: 1px solid #e3e8ef;
    margin: 0;
    padding: 20px 28px 0 28px;
    box-sizing: border-box;
}

.qm-header-inner {
    max-width: 1480px;
    margin: 0 auto;
}

.qm-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    padding-bottom: 18px;
}

.qm-brand-icon {
    width: 48px;
    height: 48px;
    min-width: 48px;
    border-radius: 11px;
    background: #1769ff;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 23px;
    box-shadow: 0 6px 15px rgba(23,105,255,0.18);
}

.qm-brand-title {
    font-size: 24px;
    line-height: 1;
    font-weight: 800;
    color: #0f1d33;
    letter-spacing: -0.5px;
}

.qm-brand-subtitle {
    font-size: 13px;
    color: #60708a;
    margin-top: 7px;
}


/* ==========================================================
   NAVIGATION
   ========================================================== */

.qm-nav-space {
    height: 14px;
}

div[data-testid="stHorizontalBlock"] {
    gap: 12px !important;
}

.qm-nav-button button {
    height: 48px !important;
    min-height: 48px !important;
    border-radius: 9px !important;
    border: 1px solid #d9dfe8 !important;
    background: #ffffff !important;
    color: #233451 !important;
    font-size: 14px !important;
    font-weight: 650 !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

.qm-nav-button button:hover {
    border-color: #1769ff !important;
    color: #1769ff !important;
    background: #f8fbff !important;
}

.qm-nav-active button {
    background: #1769ff !important;
    border-color: #1769ff !important;
    color: #ffffff !important;
    box-shadow: 0 5px 14px rgba(23,105,255,0.18) !important;
}


/* ==========================================================
   MAIN CONTENT
   ========================================================== */

.qm-content {
    max-width: 1480px;
    margin: 0 auto;
    padding-top: 28px;
}

.qm-page-title {
    font-size: 25px;
    line-height: 1.2;
    font-weight: 800;
    color: #0f1d33;
    margin-bottom: 6px;
}

.qm-page-subtitle {
    font-size: 13px;
    color: #65758e;
    margin-bottom: 20px;
}


/* ==========================================================
   METRIC CARDS
   ========================================================== */

.qm-metric {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 13px;
    min-height: 145px;
    padding: 18px;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(15,23,42,0.035);
}

.qm-metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.qm-metric-label {
    font-size: 11px;
    font-weight: 800;
    color: #18253b;
    letter-spacing: 0.2px;
}

.qm-metric-value {
    font-size: 27px;
    line-height: 1;
    font-weight: 850;
    color: #101d33;
    margin-top: 17px;
}

.qm-metric-icon {
    width: 46px;
    height: 46px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
}

.qm-blue {
    background: #e8f1ff;
    color: #1769ff;
}

.qm-green {
    background: #e8f8ee;
    color: #16a34a;
}

.qm-purple {
    background: #f1e9ff;
    color: #7c3aed;
}

.qm-red {
    background: #ffe9e9;
    color: #ef4444;
}

.qm-metric-bottom {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-top: 13px;
}

.qm-metric-note {
    font-size: 11px;
    color: #60708a;
}

.qm-green-text {
    color: #16a34a;
    font-weight: 700;
}

.qm-red-text {
    color: #ef4444;
    font-weight: 700;
}

.spark {
    width: 92px;
    height: 38px;
}


/* ==========================================================
   PANELS
   ========================================================== */

.qm-panel {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 13px;
    padding: 17px 18px;
    min-height: 290px;
    box-shadow: 0 2px 8px rgba(15,23,42,0.03);
    box-sizing: border-box;
}

.qm-panel-title {
    font-size: 14px;
    font-weight: 800;
    color: #17243a;
}

.qm-panel-subtitle {
    font-size: 11px;
    color: #74839a;
    margin-top: 3px;
    margin-bottom: 10px;
}


/* ==========================================================
   TOP QUERIES
   ========================================================== */

.qm-top-query {
    padding: 9px 0;
    border-bottom: 1px solid #eef1f5;
}

.qm-query-line {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
}

.qm-query-id {
    width: 25px;
    color: #64748b;
    font-weight: 800;
}

.qm-query-name {
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.qm-query-time {
    font-weight: 800;
    white-space: nowrap;
}

.qm-progress-bg {
    height: 4px;
    background: #eef2f6;
    border-radius: 10px;
    margin: 7px 0 0 33px;
    overflow: hidden;
}

.qm-progress {
    height: 100%;
    border-radius: 10px;
}

.qm-progress-red {
    background: #ef4444;
}

.qm-progress-orange {
    background: #f59e0b;
}

.qm-progress-green {
    background: #16a34a;
}


/* ==========================================================
   STATUS
   ========================================================== */

.qm-status-layout {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 24px;
    min-height: 225px;
}

.qm-donut {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.qm-donut-inner {
    width: 94px;
    height: 94px;
    border-radius: 50%;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.qm-donut-number {
    font-size: 23px;
    font-weight: 850;
    color: #17243a;
}

.qm-donut-label {
    font-size: 11px;
    color: #687890;
}

.qm-status-item {
    font-size: 11px;
    line-height: 1.8;
    color: #34435b;
}

.qm-status-dot {
    font-size: 13px;
    margin-right: 5px;
}


/* ==========================================================
   RECENT QUERIES
   ========================================================== */

.qm-recent-card {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 13px;
    height: 600px;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(15,23,42,0.03);
}

.qm-recent-scroll {
    height: 430px !important;
    max-height: 430px !important;
    overflow-y: scroll !important;
    overflow-x: hidden !important;
}

.qm-recent-scroll::-webkit-scrollbar {
    width: 8px;
}

.qm-recent-scroll::-webkit-scrollbar-track {
    background: #f1f3f5;
}

.qm-recent-scroll::-webkit-scrollbar-thumb {
    background: #9ca3af;
    border-radius: 10px;
}

.qm-recent-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 17px 18px;
}

.qm-recent-title {
    font-size: 14px;
    font-weight: 800;
    color: #17243a;
}

.qm-recent-tools {
    border: 1px solid #e0e5ec;
    border-radius: 8px;
    padding: 8px 12px;
    color: #64748b;
    font-size: 11px;
}

.qm-table-header,
.qm-table-row {
    display: grid;
    grid-template-columns: 70px minmax(280px, 1fr) 190px 110px;
    align-items: center;
    column-gap: 15px;
}

.qm-table-header {
    padding: 9px 18px;
    border-top: 1px solid #e9edf2;
    border-bottom: 1px solid #e9edf2;
    color: #53637b;
    font-size: 10px;
    font-weight: 800;
}

.qm-table-row {
    padding: 9px 18px;
    border-bottom: 1px solid #edf0f4;
    font-size: 11px;
    color: #263754;
}

.qm-sql {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.qm-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
}

.qm-badge-fast {
    color: #15803d;
    background: #eaf8ef;
}

.qm-badge-medium {
    color: #d97706;
    background: #fff4dd;
}

.qm-badge-slow {
    color: #dc2626;
    background: #ffe9e9;
}

.qm-table-foot {
    padding: 11px 18px;
    color: #65758e;
    font-size: 11px;
}


/* ==========================================================
   OTHER PAGES
   ========================================================== */

.qm-page-card {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 13px;
    padding: 18px;
    box-shadow: 0 2px 8px rgba(15,23,42,0.03);
}

.qm-sql-box {
    background: #f7f9fc;
    border: 1px solid #e6eaf0;
    border-radius: 8px;
    padding: 13px;
    font-family: monospace;
    font-size: 12px;
    color: #263754;
    overflow-x: auto;
}

.qm-gap {
    height: 18px;
}


/* ==========================================================
   STREAMLIT INPUTS
   ========================================================== */

div[data-testid="stTextInput"] input {
    border: 1px solid #dce2ea !important;
    border-radius: 9px !important;
    background: #ffffff !important;
    color: #17243a !important;
    min-height: 42px !important;
}

div[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 900px) {

    div[data-testid="stMainBlockContainer"] {
        padding-left: 14px !important;
        padding-right: 14px !important;
    }

    .qm-header {
        padding-left: 16px;
        padding-right: 16px;
    }

    .qm-brand-title {
        font-size: 20px;
    }

    .qm-table-header,
    .qm-table-row {
        grid-template-columns:
            45px
            minmax(180px, 1fr)
            110px
            90px;
    }

}
/* Navigation button colours */

div.stButton > button {
    background-color: #2196F3 !important;
    color: white !important;
    border: 1px solid #2196F3 !important;
}

div.stButton > button:hover {
    background-color: #1565C0 !important;
    color: white !important;
    border: 1px solid #1565C0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="qm-header">
<div class="qm-header-inner">
<div class="qm-brand">

<div class="qm-brand-icon">🗄️</div>

<div>
<div class="qm-brand-title">QUERY MONITOR</div>
<div class="qm-brand-subtitle">Database Performance Analytics</div>
</div>

</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# NAVIGATION
# ============================================================

st.markdown(
    '<div class="qm-nav-space"></div>',
    unsafe_allow_html=True,
)


pages = [
    ("▦", "Dashboard"),
    ("▤", "Queries"),
    ("⌁", "Analysis"),
    ("♧", "Alerts"),
    ("⚙", "Settings"),
]


nav_columns = st.columns(
    5,
    gap="small",
)


for column, (icon, page) in zip(
    nav_columns,
    pages,
):

    with column:

        if st.session_state.page == page:

            st.markdown(
                '<div class="qm-nav-button qm-nav-active">',
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                '<div class="qm-nav-button">',
                unsafe_allow_html=True,
            )

        clicked = st.button(
            f"{icon}  {page}",
            key=f"navigation_{page}",
            use_container_width=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        if clicked:

            st.session_state.page = page
            st.rerun()


# ============================================================
# CONTENT START
# ============================================================

st.markdown(
    '<div class="qm-content">',
    unsafe_allow_html=True,
)


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    st.markdown(
        '<div class="qm-page-title">Performance Overview</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="qm-page-subtitle">'
        'Monitor database query performance using live backend data.'
        '</div>',
        unsafe_allow_html=True,
    )


    # ========================================================
    # METRIC CARDS
    # ========================================================

    metric_columns = st.columns(
        4,
        gap="small",
    )


    recent_times = [
        num(
            query.get(
                "execution_time"
            )
        )
        for query in queries[-8:]
    ]


    if not recent_times:
        recent_times = [0, 0, 0]


    metrics = [

        {
            "label": "TOTAL QUERIES",
            "value": str(total_queries),
            "icon": "🗄️",
            "class": "qm-blue",
            "note": "● Live query activity",
            "note_class": "qm-green-text",
            "spark": sparkline(
                recent_times,
                "#1769ff",
            ),
        },

        {
            "label": "AVG EXECUTION TIME",
            "value": fmt_ms(
                average_time
            ),
            "icon": "◷",
            "class": "qm-green",
            "note": "Calculated from backend statistics",
            "note_class": "",
            "spark": sparkline(
                recent_times,
                "#16a34a",
            ),
        },

        {
            "label": "FASTEST QUERY",
            "value": fmt_ms(
                fastest_time
            ),
            "icon": "🚀",
            "class": "qm-purple",
            "note": "Best recorded performance",
            "note_class": "qm-green-text",
            "spark": sparkline(
                list(
                    reversed(
                        recent_times
                    )
                ),
                "#7c3aed",
            ),
        },

        {
            "label": "SLOWEST QUERY",
            "value": fmt_ms(
                slowest_time
            ),
            "icon": "⌛",
            "class": "qm-red",
            "note": "Requires attention",
            "note_class": "qm-red-text",
            "spark": sparkline(
                recent_times,
                "#ef4444",
            ),
        },
    ]


    for column, metric in zip(
        metric_columns,
        metrics,
    ):

        with column:

            st.markdown(
                f"""
<div class="qm-metric">

<div class="qm-metric-top">

<div>
<div class="qm-metric-label">{metric["label"]}</div>
<div class="qm-metric-value">{metric["value"]}</div>
</div>

<div class="qm-metric-icon {metric["class"]}">
{metric["icon"]}
</div>

</div>

<div class="qm-metric-bottom">

<div class="qm-metric-note {metric["note_class"]}">
{metric["note"]}
</div>

{metric["spark"]}

</div>

</div>
""",
                unsafe_allow_html=True,
            )


    st.markdown(
        '<div class="qm-gap"></div>',
        unsafe_allow_html=True,
    )


# ========================================================
# THREE PANELS
# ========================================================
    left, middle, right = st.columns(
       [1.35, 0.95, 1.15],
        gap="small",
    )


    # ========================================================
    # EXECUTION TREND
    # ========================================================

    with left:

        st.markdown(
            """
<div class="qm-panel">
<div class="qm-panel-title">Query Execution Trend</div>
<div class="qm-panel-subtitle">
Execution time for recorded queries
</div>
</div>
""",
            unsafe_allow_html=True,
        )


        if queries:

            trend = pd.DataFrame(
                {
                    "Query": [
                        f"Q{query.get('id', index + 1)}"
                        for index, query
                        in enumerate(queries)
                    ],

                    "Execution Time (ms)": [
                        ms(
                            query.get(
                                "execution_time"
                            )
                        )
                        for query in queries
                    ],
                }
            )


            st.line_chart(
                trend.set_index(
                    "Query"
                ),
                height=220,
                use_container_width=True,
            )

        else:

            st.info(
                "No query data available."
            )


    # ========================================================
    # STATUS DONUT
    # ========================================================

    with middle:

        total_status = (
            fast_count
            + medium_count
            + slow_count
        )


        if total_status:

            fast_percent = (
                fast_count
                / total_status
                * 100
            )

            medium_percent = (
                medium_count
                / total_status
                * 100
            )

            slow_percent = (
                slow_count
                / total_status
                * 100
            )

        else:

            fast_percent = 0
            medium_percent = 0
            slow_percent = 0


        p1 = fast_percent
        p2 = (
            fast_percent
            + medium_percent
        )


        gradient = (
            "conic-gradient("
            f"#16a34a 0% {p1}%, "
            f"#f59e0b {p1}% {p2}%, "
            f"#ef4444 {p2}% 100%)"
        )


        st.markdown(
            f"""
<div class="qm-panel">

<div class="qm-panel-title">
Queries by Status
</div>

<div class="qm-panel-subtitle">
Performance classification
</div>

<div class="qm-status-layout">

<div class="qm-donut"
style="background:{gradient};">

<div class="qm-donut-inner">

<div class="qm-donut-number">
{total_status}
</div>

<div class="qm-donut-label">
Total
</div>

</div>
</div>


<div>

<div class="qm-status-item">

<span
class="qm-status-dot"
style="color:#16a34a">
●
</span>

<strong>Fast</strong> (&lt; 10ms)

<br>

&nbsp;&nbsp;&nbsp;&nbsp;
{fast_count}
({fast_percent:.1f}%)

</div>


<div class="qm-status-item">

<span
class="qm-status-dot"
style="color:#f59e0b">
●
</span>

<strong>Medium</strong> (10–20ms)

<br>

&nbsp;&nbsp;&nbsp;&nbsp;
{medium_count}
({medium_percent:.1f}%)

</div>


<div class="qm-status-item">

<span
class="qm-status-dot"
style="color:#ef4444">
●
</span>

<strong>Slow</strong> (&gt; 20ms)

<br>

&nbsp;&nbsp;&nbsp;&nbsp;
{slow_count}
({slow_percent:.1f}%)

</div>

</div>

</div>

</div>
""",
            unsafe_allow_html=True,
        )


    # ========================================================
    # TOP TIME CONSUMING
    # ========================================================

    with right:

        top_queries = sorted(
            queries,
            key=lambda query: num(
                query.get("execution_time")
            ),
            reverse=True,
        )[:5]

        top_queries_html = """
<div class="qm-panel">

<div class="qm-panel-title">
Top Time Consuming Queries
</div>

<div class="qm-panel-subtitle">
Highest execution times
</div>
"""

        if top_queries:

            max_time = max(
                num(
                    query.get("execution_time")
                )
                for query in top_queries
            ) or 1

            for query in top_queries:

                execution = num(
                    query.get("execution_time")
                )

                width = (
                    execution / max_time
                ) * 100

                query_id = html.escape(
                    str(
                        query.get(
                            "id",
                            "-"
                        )
                    )
                )

                text = html.escape(
                    query_text(query)
                )

                current_status = status(
                    execution
                )

                if current_status == "Slow":
                    bar_class = "qm-progress-red"

                elif current_status == "Medium":
                    bar_class = "qm-progress-orange"

                else:
                    bar_class = "qm-progress-green"

                top_queries_html += f"""
<div class="qm-top-query">

<div class="qm-query-line">

<span class="qm-query-id">
Q{query_id}
</span>

<span class="qm-query-name">
{text}
</span>

<span class="qm-query-time">
{fmt_ms(execution)}
</span>

</div>

<div class="qm-progress-bg">

<div
class="qm-progress {bar_class}"
style="width:{width:.1f}%">
</div>

</div>

</div>
"""

        else:

            top_queries_html += """
<div class="qm-panel-subtitle">
No query data available.
</div>
"""

        top_queries_html += """
</div>
"""

        # IMPORTANT:
        # Entire panel + queries are rendered in ONE markdown block.
        st.markdown(
            top_queries_html,
            unsafe_allow_html=True,
        )
# ============================================================
# RECENT QUERIES
# ============================================================

    recent_html = """
<div class="qm-recent-card">

    <div class="qm-recent-head">
        <div class="qm-recent-title">
            Recent Queries
        </div>

        <div class="qm-recent-tools">
            Latest Queries
        </div>
    </div>

    <div class="qm-table-header">
        <div>ID</div>
        <div>Query</div>
        <div>Execution Time</div>
        <div>Status</div>
    </div>

    <div class="qm-recent-scroll">
"""

    for query in reversed(queries):

        query_id = str(query.get("id", "-"))

        if not query_id.startswith("Q"):
            query_id = "Q" + query_id

        query_text_value = html.escape(
            query_text(query)
        )

        execution = num(
            query.get("execution_time")
        )

        current_status = status(execution)

        if current_status == "Fast":
            badge_class = "qm-badge-fast"

        elif current_status == "Medium":
            badge_class = "qm-badge-medium"

        else:
            badge_class = "qm-badge-slow"

        recent_html += f"""
        <div class="qm-table-row">

            <div>
                <strong>{query_id}</strong>
            </div>

            <div class="qm-sql" title="{query_text_value}">
                {query_text_value}
            </div>

            <div>
                <strong>{fmt_ms(execution)}</strong>
            </div>

            <div>
                <span class="qm-badge {badge_class}">
                    {current_status}
                </span>
            </div>

        </div>
"""

    recent_html += """
    </div>

    <div class="qm-table-foot">
        Scroll to view more queries
    </div>

</div>
"""

    recent_html += """
    </div>
    """

    st.html(recent_html)

# ============================================================
# QUERIES PAGE
# ============================================================

elif st.session_state.page == "Queries":

    st.markdown(
        '<div class="qm-page-title">Queries</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="qm-page-subtitle">'
        'Browse and inspect recorded database queries.'
        '</div>',
        unsafe_allow_html=True,
    )
# ============================================================
# ADD QUERY
# ============================================================

    with st.container():
     st.markdown("➕ Add New Query")
     new_query_text = st.text_area(
        "SQL Query",
        placeholder="SELECT * FROM users;",
        height=100,
        key="queries_add_input",
     )
    threshold_text = st.text_input(
        "Performance Threshold (seconds)",
        placeholder="Example: 2",
        key="performance_threshold",
        help="Enter 0 or a positive number.",
    )
    execution_time_ms = st.number_input(
        "Execution Time (ms)",
        min_value=0.01,
        value=10.00,
        step=1.00,
        key="query_execution_time",
    )
    if st.button(
        "Add Query",
        type="primary",
        key="queries_add_button",
        ):
        if not threshold_text.strip():
            st.error("Please enter a performance threshold.")
            st.stop()

        try:
            threshold = float(threshold_text.strip())
        except ValueError:
            st.error("Invalid threshold. Please enter a number.")
            st.stop()

        if threshold < 0:
            st.error("Invalid threshold. Threshold cannot be negative.")
            st.stop()
        if new_query_text.strip():

            try:
                response = requests.post(
                    f"{API_URL}/queries",
                    json={
                        "query_text": new_query_text.strip(),
                        "execution_time": execution_time_ms / 1000,
                        "performance_threshold": threshold,
},
                    timeout=5,
                )

                if response.status_code in (200, 201):
                    st.success("Query added successfully.")
                    st.rerun()

                else:
                    st.error(
                        f"Unable to add query. "
                        f"Backend returned {response.status_code}."
                    )

            except requests.RequestException:
                st.error(
                    "Backend connection failed."
                )

        else:
            st.warning(
                "Please enter a SQL query."
            )

    search = st.text_input(
        "Search queries",
        placeholder="Search SQL query...",
        label_visibility="collapsed",
    )


    filtered_queries = queries


    if search:

        keyword = search.lower()

        filtered_queries = [
            query
            for query in queries
            if keyword
            in query_text(
                query
            ).lower()
        ]


    if not filtered_queries:

        st.info(
            "No queries found."
        )


    for query in filtered_queries:

        query_id = html.escape(
            str(
                query.get(
                    "id",
                    "-",
                )
            )
        )


        text = html.escape(
            query_text(
                query
            )
        )


        execution = query.get(
            "execution_time",
            0,
        )


        st.markdown(
            f"""
<div class="qm-page-card">

<div style="
font-size:14px;
font-weight:800;
margin-bottom:12px;
color:#17243a;
">
Query #{query_id}
</div>

<div class="qm-sql-box">
{text}
</div>

<div style="
margin-top:12px;
font-size:12px;
color:#52627a;
">

<strong>Execution:</strong>
{fmt_ms(execution)}

&nbsp;&nbsp;&nbsp;

<strong>Status:</strong>
{status(execution)}

</div>

</div>

<div class="qm-gap"></div>
""",
            unsafe_allow_html=True,
        )
        

 # =========================
 # EDIT / DELETE BUTTONS
# =========================

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "✏️ Edit",
                key=f"edit_query_{query_id}",
                type="primary",
            ):
                st.session_state[f"editing_query_{query_id}"] = True
                st.rerun()

        with col2:
            if st.button(
                "🗑️ Delete",
                key=f"delete_query_{query_id}",
                type="primary",
            ):
                try:
                    response = requests.delete(
                        f"{API_URL}/queries/{query_id}",
                        timeout=5,
                    )

                    if response.status_code in (200, 204):
                        st.success("Query deleted successfully.")
                        st.rerun()
                    else:
                        st.error(
                            f"Unable to delete query. "
                            f"Backend returned {response.status_code}."
                        )

                except requests.RequestException:
                    st.error("Backend connection failed.")

        # =========================
        # EDIT MODE
        # =========================

        if st.session_state.get(
            f"editing_query_{query_id}",
            False,
        ):
            edited_text = st.text_area(
                "Edit SQL Query",
                value=query_text(query),
                key=f"edit_text_{query_id}",
                height=120,
            )

            save_col, cancel_col = st.columns(2)

            with save_col:
                if st.button(
                    "💾 Save",
                    key=f"save_query_{query_id}",
                    type="primary",
                ):
                    try:
                        response = requests.put(
                            f"{API_URL}/queries/{query_id}",
                            json={
                                "query_text": edited_text.strip()
                            },
                            timeout=5,
                        )

                        if response.status_code in (200, 204):
                            st.success(
                                "Query updated successfully."
                            )
                            st.session_state[
                                f"editing_query_{query_id}"
                            ] = False
                            st.rerun()
                        else:
                            st.error(
                                f"Unable to update query. "
                                f"Backend returned {response.status_code}."
                            )

                    except requests.RequestException:
                        st.error(
                            "Backend connection failed."
                        )

            with cancel_col:
                if st.button(
                    "❌ Cancel",
                    key=f"cancel_query_{query_id}",
                ):
                    st.session_state[
                        f"editing_query_{query_id}"
                    ] = False
                    st.rerun()

# ============================================================
# ANALYSIS PAGE
# ============================================================
if st.session_state.page == "Analysis":

    st.markdown(
        '<div class="qm-page-title">Analysis</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="qm-page-subtitle">'
        'Execution performance across recorded queries.'
        '</div>',
        unsafe_allow_html=True,
    )


    if queries:

        analysis = pd.DataFrame(
            {
                "Query": [
                    f"Q{query.get('id', index + 1)}"
                    for index, query
                    in enumerate(queries)
                ],

                "Execution Time (ms)": [
                    ms(
                        query.get(
                            "execution_time"
                        )
                    )
                    for query in queries
                ],

                "Status": [
                    status(
                        query.get(
                            "execution_time"
                        )
                    )
                    for query in queries
                ],
            }
        )


        st.dataframe(   
            analysis,
            use_container_width=True,
            hide_index=True,
        )


        st.markdown(
            '<div class="qm-gap"></div>',
            unsafe_allow_html=True,
        )


        st.line_chart(
            analysis.set_index(
                "Query"
            )[
                ["Execution Time (ms)"]
            ],
            height=400,
            use_container_width=True,
        )


    else:

        st.info(
            "No query data available."
        )


# ============================================================
# ALERTS PAGE
# ============================================================

elif st.session_state.page == "Alerts":

    st.markdown(
        '<div class="qm-page-title">Alerts</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="qm-page-subtitle">'
        'Queries requiring performance attention.'
        '</div>',
        unsafe_allow_html=True,
    )


    slow_queries = [
        query
        for query in queries
        if status(
            query.get(
                "execution_time"
            )
        ) == "Slow"
    ]


    if slow_queries:

        for query in slow_queries:

            st.error(
                f"Slow Query #{query.get('id', '-')}"
                f" — "
                f"{fmt_ms(query.get('execution_time'))}"
            )


            st.code(
                query.get(
                    "query_text",
                    "",
                ),
                language="sql",
            )


    else:

        st.success(
            "No slow queries detected."
        )


# ============================================================
# SETTINGS PAGE
# ============================================================

elif st.session_state.page == "Settings":

    st.markdown(
        '<div class="qm-page-title">Settings</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="qm-page-subtitle">'
        'Application and backend configuration.'
        '</div>',
        unsafe_allow_html=True,
    )


    safe_api_url = html.escape(
        API_URL
    )


    st.markdown(
        f"""
<div class="qm-page-card">

<div style="
font-size:18px;
font-weight:850;
color:#17243a;
margin-bottom:18px;
">
Application Settings
</div>

<p>
<strong>Application:</strong>
Query Monitor
</p>

<p>
<strong>Frontend:</strong>
Streamlit
</p>

<p>
<strong>Backend:</strong>
FastAPI
</p>

<p>
<strong>API:</strong>
{safe_api_url}
</p>

<hr>

<p>
<strong>Total Queries:</strong>
{total_queries}
</p>

<p>
<strong>Average Execution Time:</strong>
{fmt_ms(average_time)}
</p>

</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# CONTENT END
# ============================================================

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)