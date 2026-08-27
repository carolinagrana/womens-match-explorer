
# ─────────────────────────────────────────────
# PROJECT OVERVIEW
# ─────────────────────────────────────────────

# FIFA Women's World Cup 2023 Match Explorer
#
# Interactive Streamlit application for exploring FIFA Women's World Cup 2023 match data.
#
# The application enables users to analyze attacking patterns, passing behavior, 
# shooting performance and player contributions for any selected match and team.

# ─────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
from matplotlib.colors import LinearSegmentedColormap

# ─────────────────────────────────────────────
# 1. PAGE CONFIGURATION
# ─────────────────────────────────────────────

st.set_page_config(page_title="Women's Match Explorer", layout="wide", page_icon="⚽")

st.markdown("""<style>.block-container {padding-top: 3rem;}</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 2. CONSTANTS
# ─────────────────────────────────────────────

events_path = "Proyecto_Final/data/WorldCup23_Events_Processed.csv"

shot_colors = {
    'Goal':'#2a9d8f',
    'Saved':'#e2711d',
    'Missed':'#bc4749',
    'Blocked':'#1b263b',
    'Own Goal':"#e9dab6",
}

pass_colors = {
    'Complete':'#2a9d8f',
    'Incomplete':"#a86d6e"
}

# ─────────────────────────────────────────────
# 3. CACHED FUNCTIONS
# ─────────────────────────────────────────────

@st.cache_data
def load_events():

    df = pd.read_csv(events_path)

    return df

# ─────────────────────────────────────────────
# 4. HELPER FUNCTIONS
# ─────────────────────────────────────────────

def draw_attacking_lanes(df_passes: pd.DataFrame) -> plt.Figure:

    """
    Pass origins are grouped into three horizontal channels (Right, Center and Left) and expressed as a percentage of total passes.
    """  

    pitch = Pitch(
        pitch_type='custom',
        pitch_length=105, pitch_width=68,
        pitch_color='#2d6a4f', line_color='#e5e5e5',
        linewidth=1.2, goal_type='line'
        )
    
    fig, ax = pitch.draw(figsize=(12, 7))
    
    ax.invert_yaxis()

    colors = ["#2B9267", "#57b489", "#bee2c3"]
    colormap = LinearSegmentedColormap.from_list('oa_heatmap', colors)

    bs = pitch.bin_statistic(df_passes['x'], df_passes['y'],
                             statistic='count', bins=(1, 3))
    
    total = bs['statistic'].sum()
    bs['statistic'] = (bs['statistic'] / total) * 100 
    str_format='{0:.1f}%' 
    
    lane_values = bs['statistic'].flatten()
    best_lane_index = np.argmax(lane_values)

    pitch.heatmap(bs, ax=ax, cmap=colormap, alpha=0.8)

    pitch.label_heatmap(bs, color='white', ax=ax, str_format=str_format, 
                    ha='center', va='center', fontsize=18, weight="bold")

    y_positions = [56.67, 34, 11.33]

    ax.text(60, y_positions[best_lane_index],
            "★",
            fontsize=16,
            color='#ffd60a',
            fontweight='bold',
            ha='center',
            va='center'
        )

    plt.tight_layout()
    return fig


def draw_shot_map(df_shots: pd.DataFrame) -> plt.Figure:

    """
    Shot markers are scaled according to xG values. Larger markers represent a higher probability of scoring.
    """

    pitch = VerticalPitch(
            pitch_type='custom', half=True,
            pitch_color='#2d6a4f', line_color='white', linewidth=1,
            stripe=True, stripe_color='#2d6a4f',
            pitch_length=105, pitch_width=68,
            goal_type='box', pad_bottom=-5
        )
    
    fig, ax = pitch.draw(figsize=(8, 6), constrained_layout=True)
    fig.set_facecolor('#2d6a4f')

    goals = (df_shots['shot_result'] == 'Goal').sum()
    total = len(df_shots)
    xg_sum = df_shots['shot_statsbomb_xg'].sum()

    line_widths = np.where(df_shots['shot_result'] == 'Goal',1.5,0.5)


    ax.text(
        0.5, 1.02,
        f"{total} shots  |  {goals} goals  |  {xg_sum:.1f} xG",
        transform=ax.transAxes,
        fontsize=11,
        color='white',
        fontweight='bold',
        ha='center',
        va='bottom'
    )

    pitch.scatter(
        df_shots['x'],
        df_shots['y'],
        color=df_shots['shot_result'].map(shot_colors).fillna('#adb5bd'),
        s=25 + df_shots['shot_statsbomb_xg'] * 250,
        marker='o',
        edgecolors='white',
        linewidths=line_widths,
        alpha=0.85,
        zorder=3,
        ax=ax
    )

    legend_handles = [
        ax.plot(
            [],
            marker='o',
            ls='',
            color=color
        )[0]
        for color in shot_colors.values()
    ]

    ax.legend(
        legend_handles,
        list(shot_colors.keys()),
        loc='upper center',
        bbox_to_anchor=(0.5,1.015),
        ncol = len(shot_colors),
        fontsize=8,
        frameon = False,
        handletextpad = 0.5,
        labelcolor='white'
    )

    return fig


def draw_passmap(df_passes: pd.DataFrame,
                 show_progressive_only: bool) -> plt.Figure:

    """
    Passes are visualized using directional lines.
    Green lines indicate successful passes, while red lines represent incomplete passes.
    The visualization can be filtered to show only progressive passes. 
    A pass is considered progressive when it moves the ball forward by 15 meters or more.    
    """

    if show_progressive_only:
        df_plot = df_passes[df_passes['progressive_pass']==True].copy() 
    else:
        df_plot = df_passes.copy()

    total = len(df_plot)
    completed = (df_plot['pass_result']=='Complete').sum()
    rate = completed/total * 100 if total > 0 else 0
   

    pitch = Pitch(
        pitch_type='custom',
        pitch_length=105, pitch_width=68,
        pitch_color='#2d6a4f', line_color='white',
        linewidth=1.2, goal_type='line'
    )
    fig, ax = pitch.draw(figsize=(12, 7))
    fig.set_facecolor("#2d6a4f")
    ax.invert_yaxis()

    for _, row in df_plot.iterrows():

        color = pass_colors.get(row["pass_result"],'#adb5bd')

        pitch.lines(
            row["x"],
            row["y"],
            row["end_x"],
            row["end_y"],
            lw=1.5,
            comet=True,
            color=color,
            alpha=0.8,
            ax=ax
        )

    title_suffix = ("Progressive passes only" if show_progressive_only else "All passes")

    ax.text(
        0.5,
        1.04,
        f"{title_suffix}",
        color='white',
        fontsize=12,
        ha='center',
        va='bottom',
        transform=ax.transAxes,
        fontweight='bold'
    )

    ax.text(
        0.5,
        1,
        f"{total} passes  |  {completed} successful  |  {rate:.1f} % accuracy",
        color='white',
        fontsize=11,
        ha='center',
        va='bottom',
        transform=ax.transAxes,
        fontweight='bold'
    )    

    legend_handles = [
        ax.plot(
            [],
            marker='o',
            ls='',
            color='#2a9d8f'
 
        )[0],

        ax.plot(
            [],
            marker='o',
            ls='',
            color='#a86d6e'
        )[0]
    ]

    ax.legend(
        legend_handles,
        ['Successful', 'Incomplete'],
        loc='upper center',
        frameon=False,
        fontsize=8,
        bbox_to_anchor=(0.49,1),
        labelcolor='white',
        ncol=2
    )

    return fig


# ─────────────────────────────────────────────
# 5. DATA LOADING
# ─────────────────────────────────────────────

df_events = load_events()

# ─────────────────────────────────────────────
# 6. SIDEBAR
# ─────────────────────────────────────────────

matches = (df_events[['match_id','match_label','match_date','competition_stage_name']].drop_duplicates().sort_values('match_date'))

matches['match_display'] =  matches['match_date'].astype(str) + " | " + matches['match_label'] 

stage_order = ['Group Stage', 'Round of 16', 'Quarter-finals', 'Semi-finals', '3rd Place Final', 'Final']

matches['competition_stage_name'] = pd.Categorical(matches['competition_stage_name'], categories = stage_order, ordered = True)

with st.sidebar:

    st.title("Match selector")

    stages = list(matches['competition_stage_name'].dropna().unique())

    selected_stage = st.selectbox("Stage", stages, index=None, placeholder='Select stage...')

    selected_match = None
    selected_match_id = None

    if selected_stage is not None:
        matches_stage = matches[matches['competition_stage_name']== selected_stage]
    else:    
        matches_stage = matches.iloc[0:0]
    
    selected_match = st.selectbox("Match", matches_stage['match_display'].tolist(), index=None, placeholder='Select match...', disabled = matches_stage.empty)

    if selected_match is not None:
        selected_match_id = matches_stage.loc[matches_stage['match_display'] == selected_match,'match_id'].iloc[0]
        teams = sorted(df_events.loc[df_events['match_id']==selected_match_id,'team_name'].unique())
    else:
        teams = []

    selected_team = st.selectbox("Team", teams, index=None, placeholder='Select team...', disabled = len(teams) == 0)

    st.divider()

# ─────────────────────────────────────────────
# 7. INITIAL CONTENT
# ─────────────────────────────────────────────

if selected_team is None:

    st.title("⚽ Football Match Explorer")
    st.subheader("🏆FIFA Women's World Cup 2023")
    st.info("Select a match from the sidebar to explore the data")
    st.stop()

# ─────────────────────────────────────────────
# 8. MATCH INFORMATION
# ─────────────────────────────────────────────

if selected_team is not None:

    match_info = matches[matches['match_id'] == selected_match_id].iloc[0]

    st.markdown(
    """
    <div style="
        text-align: center;font-size: 24px; font-weight: bold; margin-top:0px; margin-bottom:0px;
    ">
        🏆 FIFA Women's World Cup 2023
    </div>
    """,
    unsafe_allow_html=True
)

    st.markdown(
    f"""
    <div style="text-align:center; padding:0; margin-top:0px; margin-bottom:0px;font-size:20px; font-weight: bold; ">
            {match_info["match_label"]}
        </div>
    """,
    unsafe_allow_html=True
)

    st.markdown(
    f"""
    <div style="text-align:center; font-size:16px; padding:0; margin-top:3px;">
            {match_info["competition_stage_name"]}
        </div>
    """,
    unsafe_allow_html=True
)      

# ─────────────────────────────────────────────
# 9. DATAFRAMES
# ─────────────────────────────────────────────

# ────────────────────────
# 9.1 COLLECTIVE 
# ────────────────────────

if selected_match is not None:

    df_match = df_events[df_events["match_id"] == selected_match_id]

else:
    df_match = pd.DataFrame()


if selected_team is not None:

    df_team = df_match[df_match["team_name"] == selected_team].copy()

else:
    df_team = pd.DataFrame()

if not df_team.empty:
    df_passes = df_team[df_team['type_name']=='Pass'].copy()
    df_shots = df_team[df_team['type_name']=='Shot'].copy()

else:
    df_passes = pd.DataFrame()
    df_shots = pd.DataFrame()

# ────────────────────────
# 9.2 INDIVIDUAL 
# ────────────────────────

if not df_team.empty:

    df_player_stats = (df_team.groupby('player_name')['type_name']
        .value_counts()
        .unstack(fill_value=0)
        .reset_index())

    df_progressive = (df_team.groupby('player_name')['progressive_pass']
        .sum()
        .reset_index()
        .rename(columns = {'progressive_pass':'Progressive Pass'}))

    df_successful_passes = (df_team[df_team['type_name']=='Pass'].groupby('player_name')['pass_result']
        .apply(lambda x: (x == 'Complete').sum())
        .reset_index()
        .rename(columns = {'pass_result':'Successful Pass'}))

    df_key_passes =  (df_team.groupby('player_name')['pass_shot_assist']
        .sum()
        .reset_index()
        .rename(columns = {'pass_shot_assist':'Key Pass'}))

    df_assists =  (df_team.groupby('player_name')['pass_goal_assist']
        .sum()
        .reset_index()
        .rename(columns = {'pass_goal_assist':'Assist'}))    

    df_xg =  (df_team.groupby('player_name')['shot_statsbomb_xg']
        .sum()
        .reset_index()
        .rename(columns = {'shot_statsbomb_xg':'xG'}))

    df_goals = (df_team[df_team['shot_result']=='Goal'].groupby('player_name')
        .size()
        .reset_index(name='Goal'))

    df_player_stats = (df_player_stats
    .merge(df_progressive, on = 'player_name', how = 'left')
    .merge(df_successful_passes, on = 'player_name', how = 'left')
    .merge(df_key_passes, on = 'player_name', how = 'left')
    .merge(df_assists, on = 'player_name', how = 'left')
    .merge(df_xg, on = 'player_name', how = 'left')
    .merge(df_goals, on = 'player_name', how = 'left'))

    calculated_columns = ['Progressive Pass','Successful Pass','Key Pass', 'Assist', 'xG', 'Goal']

    df_player_stats[calculated_columns] = df_player_stats[calculated_columns].fillna(0)
    df_player_stats['Pass Accuracy'] = np.where(df_player_stats['Pass']>0,df_player_stats['Successful Pass'] / df_player_stats['Pass'] * 100,0)

    pct_columns = ['Key Pass','Progressive Pass','Pass Accuracy','xG','Shot','Dribble','Ball Recovery','Interception','Duel']
    
    # Player scores are calculated in two steps:
    #
    # 1. Raw metrics are converted into percentile ranks within the selected team to make players comparable.
    #
    # 2. Percentile ranks are combined using weighted averages to create Creator, Threat and Defensive Scores, which are used to identify match standouts.
    #
    # Creator Score = 45% * Key Passes Pct + 35% * Progressive Passes Pct + 20% * Pass Accuracy Pct
    # Threat Score = 45% * xG Pct + 35% * Shot Pct + 20% * Dribble Pct
    # Defensive Score = 40% * Ball Recoveries Pct + 30% * Interceptions Pct + 30% * Duels Pct
        
    for column in pct_columns:
        df_player_stats[f'{column} pct'] = (df_player_stats[column].rank(pct=True)*100)

    df_player_stats['Creator Score'] = df_player_stats['Key Pass pct']*0.45 + df_player_stats['Progressive Pass pct']*0.35 + df_player_stats['Pass Accuracy pct']*0.2

    df_player_stats['Threat Score'] = df_player_stats['xG pct']*0.45 + df_player_stats['Shot pct']*0.35 + df_player_stats['Dribble pct']*0.2
    
    df_player_stats['Defensive Score'] = df_player_stats['Ball Recovery pct']*0.4 + df_player_stats['Interception pct']*0.3 + df_player_stats['Duel pct']*0.3
    
else:

    df_player_stats = pd.DataFrame()

# ─────────────────────────────────────────────
# 10. SECTIONS
# ─────────────────────────────────────────────

col1,col2,col3 = st.columns([1.75,1,1.5])

with col2:
    st.markdown("""<div style="height:25px;"></div>""",unsafe_allow_html=True)
    section = st.pills('Section',["📊 Collective","📊 Player Statistics"],label_visibility='collapsed',default="📊 Collective",width='content')

# ────────────────────────
# 10.1 COLLECTIVE SECTION
# ────────────────────────

if section == "📊 Collective":

    chart = st.selectbox("Select visualization",["Attacking Channels", "Pass Map", "Shot Map"],label_visibility='collapsed')

    if chart == "Attacking Channels":

        fig = draw_attacking_lanes(df_passes)
        st.pyplot(fig)

    elif chart == "Shot Map":

        fig = draw_shot_map(df_shots)
        st.pyplot(fig)   


    elif chart == "Pass Map":

        pass_view = st.segmented_control("Show:",["All passes", "Only progressive passes"],default="All passes",label_visibility='collapsed')

        show_progressive_only = pass_view ==  "Only progressive passes"

        fig = draw_passmap(df_passes, show_progressive_only)
        st.pyplot(fig)   

# ────────────────────────
# 10.2 INDIVIDUAL SECTION
# ────────────────────────

if section == "📊 Player Statistics":

    if not df_player_stats.empty:

        top_threat =  (df_player_stats.sort_values('Threat Score', ascending=False).head(1).iloc[0])
        top_creator =  (df_player_stats.sort_values('Creator Score', ascending=False).head(1).iloc[0])
        top_defender =  (df_player_stats.sort_values('Defensive Score', ascending=False).head(1).iloc[0])

        st.markdown(
                                f"""
                                <div style="text-align:center; padding:0; margin-top:5px; margin-bottom:5px;font-size:18px; font-weight: bold;">
                                        Match Standouts
                                    </div>
                                """,
                                unsafe_allow_html=True
                            )
            

        col1, col2, col3 = st.columns(3)

        with col1:
                st.markdown(f"""
                            <div style="text-align:center; padding:0; margin:0;font-size:16px; font-weight: 600;">
                                ⚡ Threat
                                <div style="font-size:14px; font-weight:500;">
                                    {top_threat['player_name']}
                                </div>
                                <div style="font-size:12px; color:#888888; margin-top:4px;">
                                    {top_threat['xG']:.2f} xG · {top_threat['Shot']} shots
                                </div>
                            </div>
                            """, 
                            unsafe_allow_html=True)

        with col2:
                st.markdown(f"""
                            <div style="text-align:center; padding:0; margin:0;font-size:16px; font-weight: 600;">
                                🎯 Creator
                                <div style="font-size:14px; font-weight:500;">
                                    {top_creator['player_name']}
                                </div>
                                <div style="font-size:12px; color:#888888; margin-top:4px;">
                                    {top_creator['Key Pass']} key passes · {top_creator['Progressive Pass']} progressive passes
                                </div>
                            </div>
                            """, 
                            unsafe_allow_html=True)

        with col3:
                st.markdown(f"""
                            <div style="text-align:center; padding:0; font-size:16px; font-weight: 600;">
                                🛡️ Defender
                                <div style="font-size:14px; font-weight:500;">
                                    {top_defender['player_name']}
                                </div>
                                <div style="font-size:12px; color:#888888; margin-top:4px;">
                                    {top_defender['Ball Recovery']} recoveries · {top_defender['Interception']} interceptions
                                </div>
                            </div>
                            """, 
                            unsafe_allow_html=True)

    else:
        st.info("No player data available.")

    st.markdown(
                        f"""
                        <div style="text-align:center; padding:0; margin-top:15px; font-size:18px; font-weight: bold; ">
                                Detailed Metrics
                            </div>
                        """,
                        unsafe_allow_html=True
                    )
    

    chart = st.segmented_control(" ",["Offensive","Defensive"],default='Offensive',label_visibility='collapsed')

    if chart == "Offensive":
                        
            # The offensive player table is sorted by Offensive Score. This metric combines Creator Score and Threat Score with equal weighting.
            
            featured_off_players = {top_creator['player_name'],top_threat['player_name']}

            df_player_stats['Player Display Off'] = df_player_stats['player_name'].apply(lambda player: f'⭐ {player}' if player in featured_off_players else player)

            df_player_stats['Passes Display'] = (df_player_stats['Pass'].astype(int).astype(str)) + " (" + (df_player_stats['Pass Accuracy'].round(1).astype(str)) + "%)"

            df_player_stats['Offensive Score'] = df_player_stats['Creator Score'] * 0.5 + df_player_stats['Threat Score'] * 0.5

            cols_offensive = ['Player Display Off', 'Goal','Assist', 'xG', 'Shot', 'Key Pass','Passes Display','Dribble']

            df_offensive = df_player_stats.loc[df_player_stats['Offensive Score'].sort_values(ascending=False).index,cols_offensive]

            st.dataframe(df_offensive,
                     use_container_width=True,
                     hide_index=True,
                     column_config={
                         'Player Display Off': st.column_config.TextColumn('Player'),
                         'Goal':st.column_config.NumberColumn('Goals'),
                         'Assist':st.column_config.NumberColumn('Assists'),
                         'xG':st.column_config.NumberColumn('xG'),
                         'Shot':st.column_config.NumberColumn('Shots'),
                         'Key Pass':st.column_config.NumberColumn('Key Passes'),
                         'Passes Display':st.column_config.TextColumn('Passes'),
                         'Dribble':st.column_config.NumberColumn('Dribbles')
                     },
                     height = (len(df_offensive)*35) + 38)


    elif chart == "Defensive":

            # The defensive player table is sorted by Defensive Score.
           
            featured_def_players = {top_defender['player_name']}

            df_player_stats['Player Display Def'] = df_player_stats['player_name'].apply(lambda player: f'⭐ {player}' if player in featured_def_players else player)

            cols_defensive = ['Player Display Def','Ball Recovery', 'Interception', 'Duel','Pressure','Clearance','Block']

            df_defensive = df_player_stats.loc[df_player_stats['Defensive Score'].sort_values(ascending=False).index,cols_defensive]

            st.dataframe(df_defensive,
                     use_container_width=True,
                     hide_index=True,
                     column_config={
                         'Player Display Def': st.column_config.TextColumn('Player'),
                         'Ball Recovery':st.column_config.NumberColumn('Ball Recoveries'),
                         'Interception':st.column_config.NumberColumn('Interceptions'),                         
                         'Block':st.column_config.NumberColumn('Blocks'),
                         'Duel':st.column_config.NumberColumn('Duels'),              
                         'Clearance':st.column_config.NumberColumn('Clearances'),           
                         'Pressure':st.column_config.NumberColumn('Pressure')
                     },
                     height = (len(df_defensive)*35) + 38)