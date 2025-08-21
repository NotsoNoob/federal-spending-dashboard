
# Import all the tools we need for the dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
from config import * # Import our settings from config.py


class FederalSpendingDashboard:
    """This class handles the Streamlit dashboard for federal spending data"""

    def __init__(self):
        """Set up the dashboard when we create it"""
        # Use settings from our config file
        self.data_dir = DATA_DIR
        self.csv_filename = CSV_FILENAME

        # Dashboard configuration
        self.page_title = PAGE_TITLE
        self.page_icon = PAGE_ICON

        # Data storage
        self.df = None
        self.data_loaded = False
        self.last_update = None

        print(f"✅ Dashboard initialized. Looking for data in: {self.data_dir}")
        
            # NEW: Initialize session state for filter persistence
        if 'filters' not in st.session_state:
            st.session_state.filters = {
                'date_range': None,
                'amount_range': None,
                'selected_agencies': [],
                'selected_award_types': [],
                'recipient_size': 'All'
            }
        
        if 'filter_applied' not in st.session_state:
            st.session_state.filter_applied = False
        
        # Use session state instead of instance variable
        self.filters = st.session_state.filters
        self.filtered_df = None  # Will store filtered data
        
        print(f"✅ Dashboard initialized with persistent filtering support.")
        

    def setup_page_config(self):
        """Configure the Streamlit page settings with better sidebar handling"""
        st.set_page_config(
            page_title=self.page_title,
            page_icon=self.page_icon,
            layout="wide",  # Use full width of browser
            initial_sidebar_state="expanded",  # Always start with sidebar open
            menu_items={
                'Get Help': 'https://api.usaspending.gov/docs/',
                'Report a bug': None,
                'About': f"""
                # {self.page_title}

                This dashboard displays federal spending data from USAspending.gov.

                **Data Source:** USAspending.gov API
                **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                **Built with:** Streamlit & Plotly

                ## Navigation Help
                - **Sidebar Controls:** Use the sidebar (left panel) for filters and settings
                - **If sidebar is hidden:** Look for the ☰ menu in the top-left corner
                - **Mobile users:** Tap the ☰ icon to access controls

                ## Features
                - Real-time federal spending data visualization
                - Interactive charts and filters
                - Downloadable data exports
                - Comprehensive agency and recipient analysis

                ## Data Coverage
                - Federal contracts, grants, loans, and direct payments
                - Agency and sub-agency breakdowns
                - Geographic distribution analysis
                - Time-series spending trends
                """
            }
        )

        # Apply custom CSS styling including sidebar improvements
        self.apply_custom_styling_with_sidebar_fix()

        print("✅ Page configuration applied with improved sidebar accessibility")

    def apply_custom_styling_with_sidebar_fix(self):
        """Apply custom CSS styling with sidebar visibility improvements"""
        custom_css = """
        <style>
        /* Ensure sidebar toggle is always visible */
        .css-1dp5vir {
            position: fixed !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
            z-index: 999999 !important;
            background: white !important;
            border-radius: 0.5rem !important;
            padding: 0.25rem !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
            border: 1px solid #ddd !important;
        }
        
        /* Style the hamburger menu button */
        .css-1dp5vir button {
            background: #1f4e79 !important;
            color: white !important;
            border: none !important;
            border-radius: 0.25rem !important;
            padding: 0.5rem !important;
            font-size: 1.2rem !important;
        }
        
        .css-1dp5vir button:hover {
            background: #2c5f96 !important;
            transform: scale(1.05) !important;
        }
        
        /* Make sure sidebar is easily accessible */
        .css-1d391kg {
            background-color: #f8f9fa !important;
            border-right: 2px solid #e9ecef !important;
        }
        
        /* Main title styling */
        .main-title {
            font-size: 3rem;
            font-weight: 700;
            color: #1f4e79;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }

        /* Subtitle styling */
        .subtitle {
            font-size: 1.2rem;
            color: #5a6c7d;
            text-align: center;
            margin-bottom: 2rem;
            font-style: italic;
        }

        /* Metric cards styling */
        [data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Button styling */
        .stButton button {
            background-color: #1f4e79;
            color: white;
            border-radius: 0.5rem;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stButton button:hover {
            background-color: #2c5f96;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        /* Success message styling */
        .stSuccess {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }

        /* Info message styling */
        .stInfo {
            background-color: #d1ecf1;
            border-color: #bee5eb;
            color: #0c5460;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }

        /* Warning message styling */
        .stWarning {
            background-color: #fff3cd;
            border-color: #ffeaa7;
            color: #856404;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }

        /* Custom divider */
        .custom-divider {
            height: 3px;
            background: linear-gradient(90deg, #1f4e79, #4a90c2, #1f4e79);
            border: none;
            margin: 2rem 0;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: #f8f9fa;
            border-radius: 0.5rem 0.5rem 0 0;
            padding: 0 20px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #1f4e79;
            color: white;
        }
        
        /* Sidebar visibility helper */
        .sidebar-helper {
            position: fixed;
            top: 60px;
            left: 10px;
            background: #fff3cd;
            color: #856404;
            padding: 5px 10px;
            border-radius: 5px;
            border: 1px solid #ffeaa7;
            font-size: 0.8rem;
            z-index: 1000;
            display: none;
        }
        
        /* Show helper when sidebar is collapsed */
        .css-1d391kg[aria-expanded="false"] ~ .sidebar-helper {
            display: block;
        }
        </style>
        """

        st.markdown(custom_css, unsafe_allow_html=True)
        print("✅ Custom CSS styling applied with sidebar accessibility improvements")

    def apply_custom_styling(self):
        """Apply custom CSS styling to enhance the dashboard appearance"""
        custom_css = """
        <style>
        /* Main title styling */
        .main-title {
            font-size: 3rem;
            font-weight: 700;
            color: #1f4e79;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }

        /* Subtitle styling */
        .subtitle {
            font-size: 1.2rem;
            color: #5a6c7d;
            text-align: center;
            margin-bottom: 2rem;
            font-style: italic;
        }

        /* Metric cards styling */
        [data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f1f3f4;
        }

        /* Success message styling */
        .stSuccess {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }

        /* Warning message styling */
        .stWarning {
            background-color: #fff3cd;
            border-color: #ffeaa7;
            color: #856404;
        }

        /* Info message styling */
        .stInfo {
            background-color: #d1ecf1;
            border-color: #bee5eb;
            color: #0c5460;
        }

        /* Button styling */
        .stButton button {
            background-color: #1f4e79;
            color: white;
            border-radius: 0.5rem;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stButton button:hover {
            background-color: #2c5f96;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        /* Chart container styling */
        .plot-container {
            background-color: white;
            border-radius: 0.5rem;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }

        /* Data table styling */
        .dataframe {
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Custom divider */
        .custom-divider {
            height: 3px;
            background: linear-gradient(90deg, #1f4e79, #4a90c2, #1f4e79);
            border: none;
            margin: 2rem 0;
        }

        /* Loading spinner styling */
        .stSpinner {
            color: #1f4e79;
        }

        /* Selectbox styling */
        .stSelectbox > div > div {
            border-radius: 0.5rem;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: #f8f9fa;
            border-radius: 0.5rem 0.5rem 0 0;
            padding: 0 20px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #1f4e79;
            color: white;
        }
        </style>
        """

        st.markdown(custom_css, unsafe_allow_html=True)
        print("✅ Custom CSS styling applied")

    def create_styled_header(self):
        """Create a professionally styled header"""
        # Custom styled title
        st.markdown(
            f'<h1 class="main-title">{self.page_icon} {self.page_title}</h1>',
            unsafe_allow_html=True
        )

        # Styled subtitle
        st.markdown(
            '<p class="subtitle">Explore Federal Government Spending Data with Interactive Visualizations</p>',
            unsafe_allow_html=True
        )

        # Custom divider
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

        # Information cards
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("📊 **Real-time Data**\nDirect from USAspending.gov API")

        with col2:
            st.info("🎯 **Interactive Analysis**\nFilter, sort, and explore spending patterns")

        with col3:
            st.info("📈 **Visual Insights**\nCharts, graphs, and detailed breakdowns")

        print("✅ Styled header created")

    def create_enhanced_sidebar(self):
        """Create an enhanced sidebar with better organization and styling"""
        st.sidebar.markdown("# 📋 Dashboard Control Panel")
        st.sidebar.markdown("---")

        # Data status section
        st.sidebar.markdown("## 📊 Data Status")

        if self.data_loaded and self.df is not None:
            # Success status with detailed info
            st.sidebar.success("✅ Data Successfully Loaded")

            # Create metrics in a more organized way
            col1, col2 = st.sidebar.columns(2)

            with col1:
                st.metric(
                    label="📊 Records",
                    value=f"{len(self.df):,}",
                    help="Total number of federal spending records"
                )

            with col2:
                total_amount = self.df['award_amount'].sum()
                if total_amount >= 1e9:
                    value_display = f"${total_amount / 1e9:.1f}B"
                elif total_amount >= 1e6:
                    value_display = f"${total_amount / 1e6:.1f}M"
                else:
                    value_display = f"${total_amount / 1e3:.1f}K"

                st.metric(
                    label="💰 Total Value",
                    value=value_display,
                    help="Total award amount in the dataset"
                )

            # Additional data insights
            st.sidebar.markdown("### 📈 Quick Insights")

            # Top recipient
            if len(self.df) > 0:
                try:
                    top_recipient = self.df.groupby('recipient_name')['award_amount'].sum().idxmax()
                    top_amount = self.df.groupby('recipient_name')['award_amount'].sum().max()

                    st.sidebar.markdown(f"""
                    **🏆 Top Recipient:**
                    {top_recipient[:30]}{'...' if len(top_recipient) > 30 else ''}
                    *${top_amount / 1e6:.1f}M*
                    """)
                except Exception as e:
                    st.sidebar.markdown("**🏆 Top Recipient:** *Data processing...*")

                # Top agency
                try:
                    agency_counts = self.df['awarding_agency'].value_counts()
                    if len(agency_counts) > 0:
                        top_agency = agency_counts.index[0]
                        agency_count = agency_counts.iloc[0]

                        st.sidebar.markdown(f"""
                        **🏛️ Most Active Agency:**
                        {top_agency[:25]}{'...' if len(top_agency) > 25 else ''}
                        *{agency_count} awards*
                        """)
                    else:
                        st.sidebar.markdown("**🏛️ Most Active Agency:** *No data available*")
                except Exception as e:
                    st.sidebar.markdown("**🏛️ Most Active Agency:** *Data processing...*")

            # Last update info with better formatting
            if self.last_update:
                st.sidebar.markdown(f"**🕒 Last Updated:**\n{self.last_update}")

        else:
            # Error status with helpful instructions
            st.sidebar.error("❌ No Data Available")
            st.sidebar.markdown("""
            ### 🚀 Quick Start Guide

            1. **Run Data Collector:**
                ```bash
                python data_collector.py
                ```

            2. **Refresh Dashboard:**
                Click the refresh button below

            3. **Explore Data:**
                Navigate through visualizations
            """)

        # Control section
        #st.sidebar.markdown("---")
        #st.sidebar.markdown("## ⚙️ Controls")

        # Refresh button with better styling
        #refresh_col1, refresh_col2 = st.sidebar.columns([3, 1])
        #with refresh_col1:
         #   if st.button("🔄 Refresh Data", help="Reload data from files", use_container_width=True):
          #      with st.spinner("Refreshing data..."):
           #         self.load_data()
            #    st.rerun()

        #with refresh_col2:
         #   if st.button("ℹ️", help="Show help information"):
          #      self.show_help_modal()

        # Data source section
        st.sidebar.markdown("---")
        st.sidebar.markdown("## 🔗 Data Information")

        # Expandable data source details
        with st.sidebar.expander("📄 Data Source Details"):
            st.markdown("""
            **Source:** USAspending.gov API
            **Coverage:** Federal fiscal year 2024
            **Period:** October 2023 - September 2024
            **Types:** Contracts, Grants, Loans, Direct Payments
            **Update:** Manual refresh required

            [📖 API Documentation](https://api.usaspending.gov/docs/)
            """)

        # File information
        with st.sidebar.expander("📁 File Information"):
            data_files = self.get_available_data_files()
            if data_files:
                st.markdown("**Available Data Files:**")
                for file_path in sorted(data_files, reverse=True)[:3]:  # Show 3 most recent
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    file_date = datetime.fromtimestamp(os.path.getmtime(file_path))

                    st.markdown(f"""
                    **{file_name}**
                    Size: {file_size:,} bytes
                    Date: {file_date.strftime('%Y-%m-%d %H:%M')}
                    """)
            else:
                st.markdown("*No data files found*")

        print("✅ Enhanced sidebar created")
        # Add this to the end of your create_enhanced_sidebar() method, just before the final print statement

        # Help and Instructions section
        st.sidebar.markdown("---")
        st.sidebar.markdown("## ❓ Need Help?")

        # Expandable help sections
        with st.sidebar.expander("🚀 Quick Start Guide"):
            st.markdown("""
            **First Time Setup:**
            1. Run `python data_collector.py` to get data
            2. Click "🔄 Refresh Data" button
            3. Explore the visualizations!
            
            **Navigation Tips:**
            • Use tabs to switch between chart types
            • Try the search box in Data Explorer
            • Hover over charts for details
            • Click refresh to update data
            """)

        with st.sidebar.expander("🎯 Dashboard Features"):
            st.markdown("""
            **📊 Overview:** Key spending metrics
            
            **📈 Visualizations:**
            • Top Recipients - Who gets funding
            • Agencies - Government department spending  
            • Award Types - Contract vs grants analysis
            • Agency Flow - Money flow between departments
            • Geographic Map - State-by-state spending
            
            **🔍 Data Explorer:** Search and filter all records
            """)

        with st.sidebar.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            
            **No data showing?**
            • Run `python data_collector.py` first
            • Check internet connection
            • Click refresh button
            
            **Charts not loading?**
            • Refresh your browser
            • Check browser console for errors
            
            **Data seems old?**
            • Run data collector again for fresh data
            • Check data freshness in footer
            """)

        # Quick action buttons
        st.sidebar.markdown("### 🎛️ Quick Actions")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("📖 Tutorial", help="Show interactive tutorial", key="tutorial_btn"):
                st.info("""
                💡 **Quick Tutorial:**
                1. Check the Overview metrics at the top
                2. Explore charts using the tabs
                3. Use Data Explorer to search records
                4. Try different filters and settings
                5. Refresh data when needed
                """)

        with col2:
            if st.button("ℹ️ About", help="About this dashboard", key="about_btn"):
                st.info("""
                🏛️ **Federal Spending Dashboard**
                
                This dashboard analyzes real federal spending data from USAspending.gov to provide insights into how government money is allocated and spent.
                
                **Version:** 1.0
                **Data Source:** USAspending.gov API
                **Updated:** Real-time via data collector
                """)
    def create_dynamic_filter_system(self):
        """Create comprehensive dynamic filter system - FIXED VERSION"""
        if self.df is None or self.df.empty:
            st.sidebar.info("📊 Load data to enable filtering")
            return None
        
        st.sidebar.markdown("## 🎛️ Smart Filters")
        st.sidebar.markdown("*Filter your data dynamically*")
        
        # Initialize filtered dataframe
        filtered_df = self.df.copy()
        
       # FILTER 1: Date Range Selector
        st.sidebar.markdown("### 📅 Date Range")
        
        # Create date options based on available data
        if 'start_date' in self.df.columns:
            try:
                # Convert dates and handle errors
                self.df['start_date_parsed'] = pd.to_datetime(self.df['start_date'], errors='coerce')
                valid_dates = self.df['start_date_parsed'].dropna()
                
                if len(valid_dates) > 0:
                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()
                    
                    # Date range selector
                    date_range = st.sidebar.date_input(
                        "Select date range:",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        help="Filter awards by start date range"
                    )
                    
                    # Apply date filter
                    if len(date_range) == 2:
                        start_filter, end_filter = date_range
                        mask = (
                            (self.df['start_date_parsed'].dt.date >= start_filter) &
                            (self.df['start_date_parsed'].dt.date <= end_filter)
                        )
                        filtered_df = filtered_df[mask]
                        self.filters['date_range'] = date_range
                        
                        st.sidebar.success(f"📅 {len(filtered_df):,} records in date range")
                    else:
                        st.sidebar.info("📅 Select both start and end dates")
                else:
                    st.sidebar.warning("📅 No valid dates found in data")
            except Exception as e:
                st.sidebar.error(f"📅 Date filter error: {str(e)}")
        else:
            st.sidebar.info("📅 Date filtering not available")
        # FILTER 3: Multi-select Agencies  
    
        st.sidebar.markdown("### 🏛️ Awarding Agencies")

        try:
            agencies = [agency for agency in filtered_df['awarding_agency'].unique() 
                    if pd.notna(agency) and agency not in ['Unknown Agency', 'Unknown', '', 'nan']]
            agencies = sorted(agencies)[:25]
            
            if agencies:
                # Use session state default
                default_agencies = st.session_state.filters.get('selected_agencies', [])
                
                selected_agencies = st.sidebar.multiselect(
                    "Select agencies:",
                    options=agencies,
                    default=default_agencies,
                    help=f"Choose from {len(agencies)} agencies",
                    key="persistent_agencies"
                )
                
                # Save to session state
                st.session_state.filters['selected_agencies'] = selected_agencies
                
                if selected_agencies:
                    st.sidebar.success(f"🏛️ {len(selected_agencies)} agencies selected")
                else:
                    st.sidebar.info("🏛️ All agencies shown")
                    
        except Exception as e:
            st.sidebar.error(f"🏛️ Agency filter error: {str(e)}")
        
        # FILTER 4: Multi-select Award Types
        st.sidebar.markdown("### 📊 Award Types")
        
        try:
            # Get unique award types
            if 'contract_award_type' in filtered_df.columns:
                award_types = [atype for atype in filtered_df['contract_award_type'].unique() 
                            if pd.notna(atype) and atype not in ['Unknown Type', 'Unknown', '', 'N/A', 'nan']]
                award_types = sorted(award_types)[:20]  # Limit to 20 for UI performance
                
                if award_types:
                    selected_award_types = st.sidebar.multiselect(
                        "Select award types:",
                        options=award_types,
                        default=[],
                        help=f"Choose from {len(award_types)} award types. Leave empty to show all."
                    )
                    
                    # Apply award type filter
                    if selected_award_types:
                        type_mask = filtered_df['contract_award_type'].isin(selected_award_types)
                        filtered_df = filtered_df[type_mask]
                        self.filters['selected_award_types'] = selected_award_types
                        
                        st.sidebar.success(f"📊 {len(filtered_df):,} records of {len(selected_award_types)} types")
                    else:
                        st.sidebar.info("📊 Showing all award types")
                else:
                    st.sidebar.warning("📊 No award types found")
            else:
                st.sidebar.info("📊 Award type filtering not available")
                
        except Exception as e:
            st.sidebar.error(f"📊 Award type filter error: {str(e)}")
        
        # FILTER 5: UPDATED Recipient Size Classification (New Thresholds)
        st.sidebar.markdown("### 🏢 Recipient Size")
        
        try:
            # UPDATED size categories based on your data insights
            recipient_size_options = {
                'All': 'Show all recipients',
                'Large (>$1B)': 'Recipients with >$1 billion total awards',
                'Medium ($100M-$1B)': 'Recipients with $100M-$1B total awards', 
                'Small (<$100M)': 'Recipients with <$100M total awards'
            }
            
            selected_size = st.sidebar.selectbox(
                "Recipient size category:",
                options=list(recipient_size_options.keys()),
                index=0,  # Default to "All"
                format_func=lambda x: recipient_size_options[x],
                help="Filter by total award amount per recipient (updated thresholds)"
            )
            
            # Apply recipient size filter with new thresholds
            if selected_size != 'All':
                # Calculate total per recipient from current filtered data
                recipient_totals = filtered_df.groupby('recipient_name')['award_amount'].sum()
                
                if selected_size == 'Large (>$1B)':
                    # Greater than 1 billion
                    qualifying_recipients = recipient_totals[recipient_totals > 1_000_000_000].index
                    size_mask = filtered_df['recipient_name'].isin(qualifying_recipients)
                    
                elif selected_size == 'Medium ($100M-$1B)':
                    # Between 100 million and 1 billion
                    qualifying_recipients = recipient_totals[
                        (recipient_totals >= 100_000_000) & (recipient_totals <= 1_000_000_000)
                    ].index
                    size_mask = filtered_df['recipient_name'].isin(qualifying_recipients)
                    
                else:  # Small (<$100M)
                    # Less than 100 million
                    qualifying_recipients = recipient_totals[recipient_totals < 100_000_000].index
                    size_mask = filtered_df['recipient_name'].isin(qualifying_recipients)
                
                filtered_df = filtered_df[size_mask]
                self.filters['recipient_size'] = selected_size
                
                # Show detailed stats
                num_recipients = len(qualifying_recipients)
                total_amount = recipient_totals.loc[qualifying_recipients].sum()
                
                st.sidebar.success(f"🏢 {len(filtered_df):,} records")
                st.sidebar.info(f"📊 {num_recipients} {selected_size.lower().split(' ')[0]} recipients")
                st.sidebar.info(f"💰 Total: ${total_amount/1e9:.2f}B")
                
            else:
                st.sidebar.info("🏢 Showing all recipient sizes")
                
        except Exception as e:
            st.sidebar.error(f"🏢 Recipient size filter error: {str(e)}")
        
        # FILTER SUMMARY & CONTROLS
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 Filter Summary")
        
        # Show comprehensive filter summary
        try:
            total_original = len(self.df)
            total_filtered = len(filtered_df)
            filtered_percentage = (total_filtered / total_original * 100) if total_original > 0 else 0
            
            # Main metric
            st.sidebar.metric(
                label="📊 Filtered Records",
                value=f"{total_filtered:,}",
                delta=f"{filtered_percentage:.1f}% of total",
                help=f"Showing {total_filtered:,} out of {total_original:,} total records"
            )
            
            # Additional summary info
            if total_filtered > 0:
                filtered_amount = filtered_df['award_amount'].sum()
                original_amount = self.df['award_amount'].sum()
                amount_percentage = (filtered_amount / original_amount * 100) if original_amount > 0 else 0
                
                st.sidebar.info(f"""
                **💰 Filtered Total Value:**
                ${filtered_amount/1e9:.2f}B ({amount_percentage:.1f}% of total)
                
                **👥 Unique Recipients:** {filtered_df['recipient_name'].nunique():,}
                **🏛️ Unique Agencies:** {filtered_df['awarding_agency'].nunique():,}
                """)
            
            # Show active filters count
            active_filters = []
            if self.filters.get('date_range'):
                active_filters.append("📅 Date Range")
            if self.filters.get('selected_agencies'):
                active_filters.append(f"🏛️ {len(self.filters['selected_agencies'])} Agencies") 
            if self.filters.get('selected_award_types'):
                active_filters.append(f"📊 {len(self.filters['selected_award_types'])} Award Types")
            if self.filters.get('recipient_size', 'All') != 'All':
                active_filters.append(f"🏢 {self.filters['recipient_size']}")
            
            if active_filters:
                st.sidebar.success(f"🎛️ **Active Filters:** {len(active_filters)}")
                for filter_name in active_filters:
                    st.sidebar.write(f"• {filter_name}")
            else:
                st.sidebar.info("🎛️ No filters active (showing all data)")
                
        except Exception as e:
            st.sidebar.warning(f"Filter summary error: {str(e)}")
        
        # FIXED Reset Button Section
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 Filter Controls")

        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("🔄 Reset All", help="Clear all filters and reload", key="reset_all_filters"):
                # Clear session state filters
                st.session_state.filters = {
                    'date_range': None,
                    'amount_range': None,
                    'selected_agencies': [],
                    'selected_award_types': [],
                    'recipient_size': 'All'
                }
                
                # Clear widget states by deleting their keys
                keys_to_clear = [
                    'start_date_filter',
                    'end_date_filter', 
                    'persistent_agencies',
                    'persistent_award_types',
                    'recipient_size_selector'
                ]
                
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Set reset flag
                st.session_state.reset_triggered = True
                
                # Show success message and rerun
                st.sidebar.success("🔄 All filters reset!")
                st.rerun()

        with col2:
            if st.button("📊 Apply", help="Apply current filter settings", key="apply_filters"):
                st.sidebar.success("✅ Filters applied!")
                st.rerun()
        # Store filtered data for use by charts
        self.filtered_df = filtered_df
        
        print(f"✅ Dynamic filters applied: {total_filtered:,} records (was {total_original:,})")
        return filtered_df
    def apply_filters_with_persistence(self):
        """Apply filters with session state persistence and conflict detection"""
        if self.df is None or self.df.empty:
            return self.df
        
        print("🎛️ Applying filters with persistence...")
        
        # Start with full dataset
        filtered_df = self.df.copy()
        initial_count = len(filtered_df)
        
        # Track filter application order for conflict detection
        applied_filters = []
        
        try:
            # FILTER 1: Date Range (with persistence)
            if st.session_state.filters.get('date_range'):
                date_range = st.session_state.filters['date_range']
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    if 'start_date' in self.df.columns:
                        try:
                            # Ensure we have parsed dates
                            if 'start_date_parsed' not in self.df.columns:
                                self.df['start_date_parsed'] = pd.to_datetime(self.df['start_date'], errors='coerce')
                            
                            start_filter, end_filter = date_range
                            date_mask = (
                                (self.df['start_date_parsed'].dt.date >= start_filter) &
                                (self.df['start_date_parsed'].dt.date <= end_filter) &
                                (self.df['start_date_parsed'].notna())
                            )
                            
                            before_count = len(filtered_df)
                            filtered_df = filtered_df[date_mask]
                            after_count = len(filtered_df)
                            
                            applied_filters.append(f"📅 Date: -{before_count - after_count:,} records")
                            print(f"✅ Date filter applied: {after_count:,} records remaining")
                            
                        except Exception as e:
                            print(f"⚠️ Date filter skipped: {str(e)}")
            
            # FILTER 2: Agency Selection (with persistence)
            if st.session_state.filters.get('selected_agencies'):
                selected_agencies = st.session_state.filters['selected_agencies']
                if selected_agencies:  # Only apply if agencies are actually selected
                    before_count = len(filtered_df)
                    agency_mask = filtered_df['awarding_agency'].isin(selected_agencies)
                    filtered_df = filtered_df[agency_mask]
                    after_count = len(filtered_df)
                    
                    applied_filters.append(f"🏛️ Agencies: -{before_count - after_count:,} records")
                    print(f"✅ Agency filter applied: {after_count:,} records remaining")
            
            # FILTER 3: Award Type Selection (with persistence) 
            if st.session_state.filters.get('selected_award_types'):
                selected_award_types = st.session_state.filters['selected_award_types']
                if selected_award_types and 'contract_award_type' in filtered_df.columns:
                    before_count = len(filtered_df)
                    type_mask = filtered_df['contract_award_type'].isin(selected_award_types)
                    filtered_df = filtered_df[type_mask]
                    after_count = len(filtered_df)
                    
                    applied_filters.append(f"📊 Award Types: -{before_count - after_count:,} records")
                    print(f"✅ Award type filter applied: {after_count:,} records remaining")
            
            # FILTER 4: Recipient Size (with persistence)
            recipient_size = st.session_state.filters.get('recipient_size', 'All')
            if recipient_size != 'All':
                before_count = len(filtered_df)
                
                # Calculate recipient totals from current filtered data
                recipient_totals = filtered_df.groupby('recipient_name')['award_amount'].sum()
                
                if recipient_size == 'Large (>$1B)':
                    qualifying_recipients = recipient_totals[recipient_totals > 1_000_000_000].index
                elif recipient_size == 'Medium ($100M-$1B)':
                    qualifying_recipients = recipient_totals[
                        (recipient_totals >= 100_000_000) & (recipient_totals <= 1_000_000_000)
                    ].index
                else:  # Small (<$100M)
                    qualifying_recipients = recipient_totals[recipient_totals < 100_000_000].index
                
                size_mask = filtered_df['recipient_name'].isin(qualifying_recipients)
                filtered_df = filtered_df[size_mask]
                after_count = len(filtered_df)
                
                applied_filters.append(f"🏢 Size: -{before_count - after_count:,} records")
                print(f"✅ Recipient size filter applied: {after_count:,} records remaining")
            
            # CONFLICT DETECTION: Check if filters removed too much data
            final_count = len(filtered_df)
            removal_percentage = ((initial_count - final_count) / initial_count * 100) if initial_count > 0 else 0
            
            if removal_percentage > 95:  # If more than 95% of data is filtered out
                st.sidebar.warning("⚠️ **Filter Conflict Detected!**")
                st.sidebar.error(f"Filters removed {removal_percentage:.1f}% of data ({initial_count - final_count:,} records)")
                st.sidebar.info("💡 Try relaxing some filter criteria")
            elif removal_percentage > 75:  # If more than 75% is filtered out
                st.sidebar.warning(f"🔍 Heavy filtering: {removal_percentage:.1f}% data filtered out")
            
            # PERFORMANCE OPTIMIZATION: Cache results for large datasets
            if initial_count > 10000:  # For datasets larger than 10k records
                # Add a simple hash-based cache key
                import hashlib
                filter_key = str(sorted(st.session_state.filters.items()))
                cache_key = hashlib.md5(filter_key.encode()).hexdigest()[:8]
                
                # Store in session state cache
                if 'filter_cache' not in st.session_state:
                    st.session_state.filter_cache = {}
                
                st.session_state.filter_cache[cache_key] = {
                    'filtered_df': filtered_df,
                    'applied_filters': applied_filters,
                    'timestamp': pd.Timestamp.now()
                }
                
                print(f"📊 Large dataset detected ({initial_count:,} records) - caching applied")
            
            # Update session state
            st.session_state.filter_applied = True
            
            # Store results
            self.filtered_df = filtered_df
            
            # Log successful filter application
            print(f"✅ Filters applied successfully:")
            print(f"   📊 {initial_count:,} → {final_count:,} records ({removal_percentage:.1f}% filtered)")
            for filter_summary in applied_filters:
                print(f"   {filter_summary}")
            
            return filtered_df
            
        except Exception as e:
            print(f"❌ Error applying filters: {str(e)}")
            st.sidebar.error(f"Filter application error: {str(e)}")
            return self.df
    def show_help_modal(self):
        """Show help information in a modal dialog"""
        st.info("""
        ### 🏛️ Federal Spending Dashboard Help

        **Navigation:**
        - Use the sidebar to control dashboard settings
        - Click refresh to reload data after running the collector
        - Explore different sections using the main content area

        **Data Collection:**
        - Run `python data_collector.py` to gather fresh data
        - Data is automatically saved to the `data/` directory
        - Dashboard loads the most recent data file

        **Features:**
        - Interactive charts and visualizations
        - Filtering and sorting capabilities
        - Export functionality for further analysis

        **Support:**
        - Check log files in `data/` directory for errors
        - Refer to USAspending.gov API documentation
        - Ensure internet connection for data collection
        """)

    def add_page_footer(self):
        """Add a minimal footer with just data source attribution"""
        st.markdown("---")
        
        # Center the data source information
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center;'>
            <strong> Data Source:</strong> <a href="https://www.usaspending.gov" target="_blank">USAspending.gov</a>
            </div>
            """, unsafe_allow_html=True)
        
        # Simple copyright notice
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8rem; margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 0.5rem;'>
            <strong>Federal Spending Dashboard</strong> | Built for transparency and accountability<br>
             Explore government spending data •  Search and filter records • Interactive visualizations
        </div>
        """, unsafe_allow_html=True)
        
        print("✅ Minimal footer with data source only")
    def show_data_status(self):
        """Display current data status and any warnings"""
        if not self.data_loaded:
            st.warning("""
            ⚠️ **No data available**

            Please run the data collector first to gather federal spending data:
            ```bash
            python data_collector.py
            ```
            Then refresh this page.
            """)
            return False

        if self.df is None or self.df.empty:
            st.error("""
            ❌ **Data loading failed**

            The data files exist but couldn't be loaded properly.
            Check the data files in the `data/` directory.
            """)
            return False

        # Show data freshness
        data_files = self.get_available_data_files()
        if data_files:
            latest_file = max(data_files, key=lambda x: os.path.getmtime(x))
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(latest_file))

            if file_age.days > 1:
                st.info(f"""
                ℹ️ **Data is {file_age.days} days old**

                Consider running the data collector to get fresh data.
                """)

        return True

    def get_available_data_files(self):
        """Get list of available data files"""
        data_files = []

        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.csv') and 'spending_data' in filename:
                    file_path = os.path.join(self.data_dir, filename)
                    data_files.append(file_path)

        return data_files

    def load_data(self):
        """Enhanced data loading with multiple source support and validation"""
        print("🔄 Starting enhanced data loading...")

        # Reset data state
        self.df = None
        self.data_loaded = False
        self.last_update = None

        try:
            # Method 1: Try to load latest CSV file
            if self.load_from_latest_csv():
                return True

            # Method 2: Try to load from timestamped files
            if self.load_from_timestamped_files():
                return True

            # Method 3: Try to load from JSON files
            if self.load_from_json_files():
                return True

            # Method 4: Try to load any CSV files in data directory
            if self.load_from_any_csv():
                return True

            print("❌ No valid data files found")
            return False

        except Exception as e:
            print(f"❌ Critical error during data loading: {str(e)}")
            self.data_loaded = False
            return False

    def load_from_latest_csv(self):
        """Load data from the latest CSV file"""
        latest_csv_path = os.path.join(self.data_dir, "spending_data_latest.csv")

        if not os.path.exists(latest_csv_path):
            print("ℹ️ Latest CSV file not found, trying alternatives...")
            return False

        try:
            print(f"📂 Loading from latest CSV: {latest_csv_path}")

            # Load with enhanced options
            self.df = pd.read_csv(
                latest_csv_path,
                encoding='utf-8',
                low_memory=False,  # Read entire file into memory for better type inference
                na_values=['', 'nan', 'NaN', 'null', 'NULL', 'None']  # Treat these as NaN
            )

            # Convert data types for better processing
            self.df = self.convert_data_types(self.df)

            # Validate and clean the data
            if self.validate_and_clean_dataframe():
                self.data_loaded = True
                self.last_update = datetime.fromtimestamp(
                    os.path.getmtime(latest_csv_path)
                ).strftime('%Y-%m-%d %H:%M:%S')

                print(f"✅ Latest CSV loaded successfully: {len(self.df)} records")
                return True
            else:
                print("❌ Latest CSV validation failed")
                return False

        except Exception as e:
            print(f"❌ Error loading latest CSV: {str(e)}")
            return False

    def load_from_timestamped_files(self):
        """Load data from timestamped CSV files (most recent first)"""
        try:
            data_files = []

            if os.path.exists(self.data_dir):
                for filename in os.listdir(self.data_dir):
                    if (filename.startswith('spending_data_') and
                            filename.endswith('.csv') and
                            'latest' not in filename):
                        file_path = os.path.join(self.data_dir, filename)
                        file_time = os.path.getmtime(file_path)
                        data_files.append((file_path, file_time))

            if not data_files:
                print("ℹ️ No timestamped CSV files found")
                return False

            # Sort by modification time (newest first)
            data_files.sort(key=lambda x: x[1], reverse=True)

            # Try to load the most recent file
            for file_path, _ in data_files[:3]:  # Try up to 3 most recent files
                try:
                    print(f"📂 Trying timestamped file: {os.path.basename(file_path)}")

                    self.df = pd.read_csv(
                        file_path,
                        encoding='utf-8',
                        low_memory=False,
                        na_values=['', 'nan', 'NaN', 'null', 'NULL', 'None']
                    )

                    # Convert data types for better processing
                    self.df = self.convert_data_types(self.df)

                    if self.validate_and_clean_dataframe():
                        self.data_loaded = True
                        self.last_update = datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).strftime('%Y-%m-%d %H:%M:%S')

                        print(f"✅ Timestamped file loaded successfully: {len(self.df)} records")
                        return True

                except Exception as e:
                    print(f"⚠️ Failed to load {os.path.basename(file_path)}: {str(e)}")
                    continue

            print("❌ All timestamped files failed to load")
            return False

        except Exception as e:
            print(f"❌ Error in timestamped file loading: {str(e)}")
            return False

    def load_from_json_files(self):
        """Load data from JSON files as fallback"""
        try:
            # Try latest JSON first
            latest_json_path = os.path.join(self.data_dir, "spending_data_latest.json")

            if os.path.exists(latest_json_path):
                print(f"📂 Trying latest JSON: {latest_json_path}")

                with open(latest_json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)

                if 'records' in json_data and json_data['records']:
                    self.df = pd.DataFrame(json_data['records'])

                    # Convert data types for better processing
                    self.df = self.convert_data_types(self.df)

                    if self.validate_and_clean_dataframe():
                        self.data_loaded = True
                        self.last_update = datetime.fromtimestamp(
                            os.path.getmtime(latest_json_path)
                        ).strftime('%Y-%m-%d %H:%M:%S')

                        print(f"✅ JSON file loaded successfully: {len(self.df)} records")
                        return True

            print("ℹ️ No valid JSON files found")
            return False

        except Exception as e:
            print(f"❌ Error loading JSON files: {str(e)}")
            return False

    def load_from_any_csv(self):
        """Try to load any CSV file in the data directory"""
        try:
            if not os.path.exists(self.data_dir):
                print("ℹ️ Data directory doesn't exist")
                return False

            csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]

            if not csv_files:
                print("ℹ️ No CSV files found in data directory")
                return False

            # Try each CSV file
            for csv_file in csv_files:
                try:
                    file_path = os.path.join(self.data_dir, csv_file)
                    print(f"📂 Trying any CSV: {csv_file}")

                    self.df = pd.read_csv(
                        file_path,
                        encoding='utf-8',
                        low_memory=False,
                        na_values=['', 'nan', 'NaN', 'null', 'NULL', 'None']
                    )

                    # Convert data types for better processing
                    self.df = self.convert_data_types(self.df)

                    if self.validate_and_clean_dataframe():
                        self.data_loaded = True
                        self.last_update = datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).strftime('%Y-%m-%d %H:%M:%S')

                        print(f"✅ CSV file loaded successfully: {len(self.df)} records")
                        return True

                except Exception as e:
                    print(f"⚠️ Failed to load {csv_file}: {str(e)}")
                    continue

            print("❌ All CSV files failed to load")
            return False

        except Exception as e:
            print(f"❌ Error trying any CSV: {str(e)}")
            return False

    def validate_and_clean_dataframe(self):
        """Validate and clean the loaded DataFrame"""
        if self.df is None or self.df.empty:
            print("❌ DataFrame is None or empty")
            return False

        print("🔍 Validating and cleaning data...")

        try:
            # Store original count
            original_count = len(self.df)

            # Check for required columns
            required_columns = ['award_id', 'recipient_name', 'award_amount']
            missing_columns = [col for col in required_columns if col not in self.df.columns]

            if missing_columns:
                print(f"❌ Missing required columns: {missing_columns}")
                return False

            # Data type conversions
            self.convert_data_types()

            # Remove completely empty rows
            initial_rows = len(self.df)
            self.df = self.df.dropna(how='all')
            if len(self.df) < initial_rows:
                print(f"🧹 Removed {initial_rows - len(self.df)} completely empty rows")

            # Handle missing values in critical columns
            self.handle_missing_values()

            # Remove duplicate records
            self.remove_duplicates()

            # Clean and standardize text fields
            self.clean_text_fields()

            # Validate data ranges
            self.validate_data_ranges()

            # Final validation
            final_count = len(self.df)

            if final_count == 0:
                print("❌ No valid records remain after cleaning")
                return False

            # Report cleaning results
            removed_count = original_count - final_count
            if removed_count > 0:
                print(f"🧹 Data cleaning complete: {removed_count} invalid records removed")
                print(f"✅ {final_count} valid records remain")
            else:
                print(f"✅ Data validation complete: {final_count} records, no cleaning needed")

            return True

        except Exception as e:
            print(f"❌ Error during data validation: {str(e)}")
            return False

    def convert_data_types(self, df=None):
        """Convert columns to appropriate data types for better processing"""
        if df is None:
            df = self.df

        if df is None or df.empty:
            print("⚠️ Cannot convert data types: DataFrame is empty")
            return df

        print("🔄 Converting data types for better processing...")

        try:
            # Make a copy so we don't modify the original
            df_converted = df.copy()

            # Convert award_amount to numeric (remove any text, make it a number)
            if 'award_amount' in df_converted.columns:
                df_converted['award_amount'] = pd.to_numeric(df_converted['award_amount'], errors='coerce')
                df_converted['award_amount'] = df_converted['award_amount'].fillna(0)  # Replace NaN with 0

            # Convert other money columns to numeric
            money_columns = [
                'base_and_all_options_value', 'covid_19_obligations', 'covid_19_outlays',
                'infrastructure_obligations', 'infrastructure_outlays'
            ]

            for col in money_columns:
                if col in df_converted.columns:
                    df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
                    df_converted[col] = df_converted[col].fillna(0)

            # Make sure text columns are clean strings
            text_columns = ['recipient_name', 'awarding_agency', 'award_type', 'description']
            for col in text_columns:
                if col in df_converted.columns:
                    df_converted[col] = df_converted[col].astype(str).str.strip()
                    # Replace 'nan' string with 'Unknown'
                    df_converted[col] = df_converted[col].replace(['nan', 'None', ''], 'Unknown')

            print("✅ Data types converted successfully")
            return df_converted

        except Exception as e:
            print(f"❌ Error converting data types: {str(e)}")
            return df  # Return original if conversion fails

    def filter_data_by_criteria(self, df, criteria):
        """Filter data based on different criteria - makes filtering easy!"""
        if df is None or df.empty:
            return df

        try:
            filtered_df = df.copy()

            # Filter by minimum amount
            if 'min_amount' in criteria and criteria['min_amount'] is not None:
                min_amount = float(criteria['min_amount'])
                filtered_df = filtered_df[filtered_df['award_amount'] >= min_amount]
                print(f"🔍 Filtered by minimum amount: ${min_amount:,.2f}")

            # Filter by maximum amount
            if 'max_amount' in criteria and criteria['max_amount'] is not None:
                max_amount = float(criteria['max_amount'])
                filtered_df = filtered_df[filtered_df['award_amount'] <= max_amount]
                print(f"🔍 Filtered by maximum amount: ${max_amount:,.2f}")

            # Filter by agency
            if 'agency' in criteria and criteria['agency'] and criteria['agency'] != 'All':
                filtered_df = filtered_df[filtered_df['awarding_agency'] == criteria['agency']]
                print(f"🔍 Filtered by agency: {criteria['agency']}")

            # Filter by award type
            if 'award_type' in criteria and criteria['award_type'] and criteria['award_type'] != 'All':
                filtered_df = filtered_df[filtered_df['award_type'] == criteria['award_type']]
                print(f"🔍 Filtered by award type: {criteria['award_type']}")

            # Filter by recipient name (search)
            if 'recipient_search' in criteria and criteria['recipient_search']:
                search_term = criteria['recipient_search'].lower()
                filtered_df = filtered_df[
                    filtered_df['recipient_name'].str.lower().str.contains(search_term, na=False)
                ]
                print(f"🔍 Filtered by recipient search: '{criteria['recipient_search']}'")

            print(f"📊 Filter result: {len(filtered_df)} records (from {len(df)} original)")
            return filtered_df

        except Exception as e:
            print(f"❌ Error filtering data: {str(e)}")
            return df  # Return original data if filtering fails

    def aggregate_data_by_field(self, df, group_by_field, sum_field='award_amount'):
        """Group data and sum amounts - like getting totals for each agency"""
        if df is None or df.empty:
            return pd.DataFrame()

        try:
            print(f"📊 Grouping data by {group_by_field}...")

            # Group by the specified field and sum the amounts
            aggregated = df.groupby(group_by_field)[sum_field].agg([
                'sum',  # Total amount
                'count',  # Number of awards
                'mean',  # Average amount
                'max'  # Largest single award
            ]).reset_index()

            # Rename columns to be more descriptive
            aggregated.columns = [
                group_by_field,
                f'total_{sum_field}',
                f'count_awards',
                f'average_{sum_field}',
                f'max_{sum_field}'
            ]

            # Sort by total amount (biggest first)
            aggregated = aggregated.sort_values(f'total_{sum_field}', ascending=False)

            print(f"✅ Created summary with {len(aggregated)} groups")
            return aggregated

        except Exception as e:
            print(f"❌ Error aggregating data: {str(e)}")
            return pd.DataFrame()

    def validate_data_quality(self, df):
        """Check if the data looks good and report any issues"""
        if df is None or df.empty:
            return {
                'is_valid': False,
                'issues': ['DataFrame is empty or None'],
                'summary': 'No data to validate'
            }

        print("🔍 Checking data quality...")

        issues = []
        warnings = []

        try:
            total_records = len(df)

            # Check 1: Essential columns exist
            required_columns = ['award_id', 'recipient_name', 'award_amount', 'awarding_agency']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                issues.append(f"Missing required columns: {', '.join(missing_columns)}")

            # Check 2: Award amounts look reasonable
            if 'award_amount' in df.columns:
                zero_amounts = (df['award_amount'] == 0).sum()
                negative_amounts = (df['award_amount'] < 0).sum()
                very_large_amounts = (df['award_amount'] > 1e10).sum()  # > 10 billion

                if zero_amounts > total_records * 0.5:  # More than 50% are zero
                    warnings.append(f"{zero_amounts} records have zero award amounts")

                if negative_amounts > 0:
                    issues.append(f"{negative_amounts} records have negative amounts")

                if very_large_amounts > 0:
                    warnings.append(f"{very_large_amounts} records have very large amounts (>$10B)")

            # Check 3: Text fields have reasonable data
            if 'recipient_name' in df.columns:
                unknown_recipients = df['recipient_name'].isin(['Unknown', 'Unknown Recipient', 'nan']).sum()
                if unknown_recipients > total_records * 0.3:  # More than 30% unknown
                    warnings.append(f"{unknown_recipients} records have unknown recipients")

            if 'awarding_agency' in df.columns:
                unknown_agencies = df['awarding_agency'].isin(['Unknown', 'Unknown Agency', 'nan']).sum()
                if unknown_agencies > total_records * 0.3:
                    warnings.append(f"{unknown_agencies} records have unknown agencies")

            # Check 4: Duplicate award IDs
            if 'award_id' in df.columns:
                duplicate_ids = df['award_id'].duplicated().sum()
                if duplicate_ids > 0:
                    warnings.append(f"{duplicate_ids} duplicate award IDs found")

            # Determine if data is valid (no critical issues)
            is_valid = len(issues) == 0

            # Create summary
            summary_parts = [f"{total_records} total records"]
            if issues:
                summary_parts.append(f"{len(issues)} critical issues")
            if warnings:
                summary_parts.append(f"{len(warnings)} warnings")

            summary = ", ".join(summary_parts)

            # Print results
            if is_valid:
                if warnings:
                    print(f"✅ Data quality: Good with warnings - {summary}")
                else:
                    print(f"✅ Data quality: Excellent - {summary}")
            else:
                print(f"⚠️ Data quality: Issues found - {summary}")

            return {
                'is_valid': is_valid,
                'issues': issues,
                'warnings': warnings,
                'summary': summary,
                'total_records': total_records
            }

        except Exception as e:
            return {
                'is_valid': False,
                'issues': [f"Error during validation: {str(e)}"],
                'summary': 'Validation failed due to error'
            }

    def handle_missing_values(self):
        """Handle missing values in critical columns"""
        try:
            # Replace missing award amounts with 0
            if 'award_amount' in self.df.columns:
                missing_amounts = self.df['award_amount'].isna().sum()
                if missing_amounts > 0:
                    self.df['award_amount'] = self.df['award_amount'].fillna(0)
                    print(f"🔧 Filled {missing_amounts} missing award amounts with 0")

            # Replace missing text fields with appropriate defaults
            text_defaults = {
                'recipient_name': 'Unknown Recipient',
                'awarding_agency': 'Unknown Agency',
                'award_type': 'Unknown Type',
                'description': 'No Description'
            }

            for col, default_value in text_defaults.items():
                if col in self.df.columns:
                    missing_count = self.df[col].isna().sum()
                    if missing_count > 0:
                        self.df[col] = self.df[col].fillna(default_value)
                        print(f"🔧 Filled {missing_count} missing {col} values")

        except Exception as e:
            print(f"⚠️ Warning: Missing value handling issues: {str(e)}")

    def remove_duplicates(self):
        """Remove duplicate records based on award_id"""
        try:
            if 'award_id' in self.df.columns:
                initial_count = len(self.df)
                self.df = self.df.drop_duplicates(subset=['award_id'], keep='first')
                duplicate_count = initial_count - len(self.df)

                if duplicate_count > 0:
                    print(f"🧹 Removed {duplicate_count} duplicate records")

        except Exception as e:
            print(f"⚠️ Warning: Duplicate removal issues: {str(e)}")

    def clean_text_fields(self):
        """Clean and standardize text fields"""
        try:
            text_columns = ['recipient_name', 'awarding_agency', 'award_type']

            for col in text_columns:
                if col in self.df.columns:
                    # Strip whitespace
                    self.df[col] = self.df[col].astype(str).str.strip()

                    # Replace common variations of "unknown"
                    unknown_patterns = ['unknown', 'n/a', 'na', 'null', 'none', '']
                    for pattern in unknown_patterns:
                        mask = self.df[col].str.lower().str.strip() == pattern
                        if col == 'recipient_name':
                            self.df.loc[mask, col] = 'Unknown Recipient'
                        elif col == 'awarding_agency':
                            self.df.loc[mask, col] = 'Unknown Agency'
                        elif col == 'award_type':
                            self.df.loc[mask, col] = 'Unknown Type'

            print("✅ Text fields cleaned")

        except Exception as e:
            print(f"⚠️ Warning: Text cleaning issues: {str(e)}")

    def validate_data_ranges(self):
        """Validate that data values are within reasonable ranges"""
        try:
            # Check award amounts
            if 'award_amount' in self.df.columns:
                # Remove negative amounts
                negative_mask = self.df['award_amount'] < 0
                negative_count = negative_mask.sum()
                if negative_count > 0:
                    self.df = self.df[~negative_mask]
                    print(f"🧹 Removed {negative_count} records with negative amounts")

                # Flag extremely large amounts (>1 trillion)
                large_mask = self.df['award_amount'] > 1e12
                large_count = large_mask.sum()
                if large_count > 0:
                    print(f"⚠️ Warning: {large_count} records have unusually large amounts (>$1T)")

            # Remove records with empty award IDs
            if 'award_id' in self.df.columns:
                empty_id_mask = (self.df['award_id'].isna()) | (self.df['award_id'] == 'nan') | (
                        self.df['award_id'] == '')
                empty_id_count = empty_id_mask.sum()
                if empty_id_count > 0:
                    self.df = self.df[~empty_id_mask]
                    print(f"🧹 Removed {empty_id_count} records with empty award IDs")

            print("✅ Data ranges validated")

        except Exception as e:
            print(f"⚠️ Warning: Data range validation issues: {str(e)}")

    def get_data_quality_report(self):
        """Generate a simple data quality report"""
        if self.df is None or self.df.empty:
            return "No data available for quality report"

        try:
            return {
                'total_records': len(self.df),
                'total_columns': len(self.df.columns),
                'missing_values': {},
                'data_types': {},
                'value_ranges': {}
            }
        except Exception as e:
            return f"Error generating quality report: {str(e)}"

    def display_debug_info(self):
        """Display debug information (only shown in development)"""
        if st.sidebar.checkbox("🔧 Show Debug Info", help="Show technical details"):
            st.sidebar.markdown("### 🔧 Debug Information")

            if self.df is not None:
                st.sidebar.text(f"DataFrame shape: {self.df.shape}")
                st.sidebar.text(f"Memory usage: {self.df.memory_usage(deep=True).sum() / 1024 ** 2:.1f} MB")
                st.sidebar.text(f"Columns: {len(self.df.columns)}")

                # Show column info
                with st.sidebar.expander("Column Details"):
                    for col in self.df.columns:
                        non_null = self.df[col].notna().sum()
                        st.text(f"{col}: {non_null}/{len(self.df)} non-null")

            # Show file info
            with st.sidebar.expander("File Information"):
                data_files = self.get_available_data_files()
                for file_path in data_files[-3:]:  # Show last 3 files
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    st.text(f"{file_name}: {file_size:,} bytes")

    def validate_data_structure(self):
        """Validate that the loaded data has the expected structure"""
        if self.df is None or self.df.empty:
            st.error("❌ **No data available**")
            return False

        # Check for required columns
        required_columns = ['award_id', 'recipient_name', 'award_amount']
        missing_columns = [col for col in required_columns if col not in self.df.columns]

        if missing_columns:
            st.error(f"""
            ❌ **Data structure error**

            Missing required columns: {', '.join(missing_columns)}

            Please re-run the data collector to ensure proper data format.
            """)
            return False

        # Basic data quality checks
        if 'award_amount' in self.df.columns:
            if self.df['award_amount'].isna().all():
                st.warning("⚠️ All award amounts are missing")

        if 'recipient_name' in self.df.columns:
            if self.df['recipient_name'].isna().sum() > len(self.df) * 0.5:
                st.warning("⚠️ More than 50% of recipient names are missing")

        return True

    def show_metrics(self):
        """Display key metrics with comprehensive error handling and fallback values"""
        print("📊 Starting metrics calculation with error handling...")

        # Check 1: Verify we have data
        if self.df is None:
            st.error("❌ **No data loaded**")
            st.info("💡 Run `python data_collector.py` to collect federal spending data")
            self._show_empty_metrics_placeholder()
            return False

        if self.df.empty:
            st.warning("⚠️ **Dataset is empty**")
            st.info("💡 The data file exists but contains no records. Try collecting fresh data.")
            self._show_empty_metrics_placeholder()
            return False

        # Check 2: Verify we have the required column
        if 'award_amount' not in self.df.columns:
            st.error("❌ **Missing required data column**")
            st.info("💡 The 'award_amount' column is missing. Please re-run the data collector.")
            self._show_empty_metrics_placeholder()
            return False

        try:
            print("🔢 Calculating metrics with error handling...")

            # Safe calculation of total records
            total_records = len(self.df)
            print(f"📊 Total records: {total_records}")

            # Safe calculation of financial metrics with validation
            award_amounts = self.df['award_amount']

            # Remove any NaN or invalid values for calculations
            valid_amounts = award_amounts.dropna()
            if len(valid_amounts) == 0:
                st.warning("⚠️ **No valid award amounts found**")
                st.info("💡 All award amounts are missing or invalid")
                self._show_empty_metrics_placeholder()
                return False

            # Calculate metrics with error handling
            total_amount = self._safe_calculate_sum(valid_amounts)
            average_amount = self._safe_calculate_mean(valid_amounts)
            largest_award = self._safe_calculate_max(valid_amounts)

            # Log successful calculations
            print(f"✅ Metrics calculated successfully:")
            print(f"  - Total: ${total_amount:,.2f}")
            print(f"  - Average: ${average_amount:,.2f}")
            print(f"  - Max: ${largest_award:,.2f}")

            # Create 4 columns for our metrics
            col1, col2, col3, col4 = st.columns(4)

            # Column 1: Total Award Amount with enhanced formatting
            with col1:
                formatted_total, total_help = self._format_currency_with_help(total_amount, "Total")

                st.metric(
                    label="💰 Total Award Amount",
                    value=formatted_total,
                    help=total_help or f"Sum of all {len(valid_amounts):,} valid awards"
                )

            # Column 2: Number of Awards with data quality info
            with col2:
                # Show if we have invalid records
                invalid_count = total_records - len(valid_amounts)
                if invalid_count > 0:
                    records_help = f"Total records: {total_records:,}\nValid amounts: {len(valid_amounts):,}\nInvalid/missing: {invalid_count:,}"
                    records_label = f"📊 Records ({len(valid_amounts):,} valid)"
                else:
                    records_help = f"All {total_records:,} records have valid award amounts"
                    records_label = "📊 Number of Awards"

                st.metric(
                    label=records_label,
                    value=f"{total_records:,}",
                    help=records_help
                )

            # Column 3: Average Award Amount
            with col3:
                formatted_avg, avg_help = self._format_currency_with_help(average_amount, "Average")

                st.metric(
                    label="📈 Average Award",
                    value=formatted_avg,
                    help=avg_help or f"Mean of {len(valid_amounts):,} valid awards"
                )

            # Column 4: Largest Single Award
            with col4:
                formatted_max, max_help = self._format_currency_with_help(largest_award, "Largest")

                st.metric(
                    label="🏆 Largest Award",
                    value=formatted_max,
                    help=max_help or f"Maximum single award amount"
                )

            # Add data freshness indicator
            self._add_data_freshness_indicator()

            # Add separator after metrics
            #st.markdown("---")

            print("✅ Enhanced metrics displayed successfully")
            return True

        except Exception as e:
            # Comprehensive error handling
            error_msg = str(e)
            print(f"❌ Error in show_metrics: {error_msg}")

            st.error(f"❌ **Error calculating metrics**: {error_msg}")

            # Try to show basic info even if metrics fail
            try:
                basic_count = len(self.df) if self.df is not None else 0
                st.info(f"📊 Dataset contains {basic_count:,} records, but metric calculations failed")
            except:
                st.info("📊 Unable to display metrics due to data issues")

            # Show placeholder metrics to maintain layout
            self._show_error_metrics_placeholder()
            return False

    def _safe_calculate_sum(self, amounts):
        """Safely calculate sum with error handling"""
        try:
            result = float(amounts.sum())
            return result if not pd.isna(result) else 0.0
        except Exception as e:
            print(f"⚠️ Sum calculation error: {e}")
            return 0.0

    def _safe_calculate_mean(self, amounts):
        """Safely calculate mean with error handling"""
        try:
            result = float(amounts.mean())
            return result if not pd.isna(result) else 0.0
        except Exception as e:
            print(f"⚠️ Mean calculation error: {e}")
            return 0.0

    def _safe_calculate_max(self, amounts):
        """Safely calculate maximum with error handling"""
        try:
            result = float(amounts.max())
            return result if not pd.isna(result) else 0.0
        except Exception as e:
            print(f"⚠️ Max calculation error: {e}")
            return 0.0

    def _format_currency_with_help(self, amount, label_type):
        """Format currency amount with appropriate units and help text"""
        try:
            if amount >= 1e9:  # 1 billion or more
                formatted = f"${amount / 1e9:.2f}B"
                help_text = f"{label_type}: ${amount:,.2f}"
            elif amount >= 1e6:  # 1 million or more
                formatted = f"${amount / 1e6:.1f}M"
                help_text = f"{label_type}: ${amount:,.2f}"
            elif amount >= 1e3:  # 1 thousand or more
                formatted = f"${amount / 1e3:.0f}K"
                help_text = f"{label_type}: ${amount:,.2f}"
            else:
                formatted = f"${amount:,.2f}"
                help_text = None

            return formatted, help_text
        except Exception as e:
            print(f"⚠️ Currency formatting error: {e}")
            return "$0.00", f"Error formatting {label_type.lower()}"

    def _show_empty_metrics_placeholder(self):
        """Show placeholder metrics when no data is available"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="💰 Total Award Amount", value="$0.00", help="No data available")
        with col2:
            st.metric(label="📊 Number of Awards", value="0", help="No data available")
        with col3:
            st.metric(label="📈 Average Award", value="$0.00", help="No data available")
        with col4:
            st.metric(label="🏆 Largest Award", value="$0.00", help="No data available")

        st.markdown("---")

    def _show_error_metrics_placeholder(self):
        """Show placeholder metrics when calculation errors occur"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="💰 Total Award Amount", value="Error", help="Calculation failed")
        with col2:
            st.metric(label="📊 Number of Awards", value="Error", help="Calculation failed")
        with col3:
            st.metric(label="📈 Average Award", value="Error", help="Calculation failed")
        with col4:
            st.metric(label="🏆 Largest Award", value="Error", help="Calculation failed")

        st.markdown("---")

    def _add_data_freshness_indicator(self):
        """Add indicator showing when data was last updated"""
        try:
            if self.last_update:
                # Parse the last update time
                try:
                    from datetime import datetime
                    update_time = datetime.fromisoformat(self.last_update.replace('Z', '+00:00'))
                    time_diff = datetime.now() - update_time

                    if time_diff.days > 7:
                        freshness_color = "🔴"
                        freshness_text = f"Data is {time_diff.days} days old"
                    elif time_diff.days > 1:
                        freshness_color = "🟡"
                        freshness_text = f"Data is {time_diff.days} days old"
                    else:
                        freshness_color = "🟢"
                        freshness_text = "Data is current"

                    st.caption(f"{freshness_color} {freshness_text} • Last updated: {self.last_update}")

                except Exception as e:
                    st.caption(f"📅 Last updated: {self.last_update}")
            else:
                st.caption("📅 Data freshness unknown")

        except Exception as e:
            print(f"⚠️ Data freshness indicator error: {e}")
            # Don't show anything if there's an error - it's not critical
    
    def add_loading_states_and_feedback(self):
        """Add loading indicators and user feedback throughout the dashboard"""
        
        # Add this at the top of your run() method, right after data loading
        if not self.data_loaded or self.df is None or self.df.empty:
            # Show helpful guidance when no data
            st.warning("⚠️ **No data available**")
            
            st.markdown("""
            ### 🚀 Get Started in 3 Easy Steps:
            
            1. **📥 Collect Data** (2 minutes)
            ```bash
            python data_collector.py
            ```
            
            2. **🔄 Refresh Dashboard**
            Click the "Refresh Data" button in the sidebar
            
            3. **📊 Explore!**
            Navigate through charts and data
            """)
            
            # Show what users can expect
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("""
                **📈 What You'll Get:**
                • Interactive spending charts
                • Government agency breakdowns  
                • Geographic spending maps
                • Searchable data tables
                • Export capabilities
                """)
            
            with col2:
                st.info("""
                **⚡ Quick Facts:**
                • Real government data
                • Updates automatically
                • Mobile-friendly design
                • No login required
                • Free to use
                """)
            
            return False  # Indicate no data available
        
        return True  # Data is available

  #  def show_success_messages(self):
        """Show contextual success messages with clean, non-redundant styling"""
        
        # Success message after data loads
   #     if self.data_loaded and len(self.df) > 0:
    #        total_amount = self.df['award_amount'].sum()
     #       unique_recipients = self.df['recipient_name'].nunique()
      #      unique_agencies = self.df['awarding_agency'].nunique()
            
            # Create a clean success banner with transparent background
            #st.markdown(f"""
            #<div style='
             #   background: rgba(212, 237, 218, 0.3); 
              #  border: 1px solid rgba(195, 230, 203, 0.5); 
               # border-radius: 0.5rem; 
                #padding: 1rem; 
                #margin: 1rem 0;
                #border-left: 4px solid #28a745;
            #'>
             #   ✅ <strong>Dashboard Ready!</strong> Successfully loaded {len(self.df):,} federal spending records<br>
              #  📊 <strong>Quick Summary:</strong> ${total_amount / 1e9:.2f} billion • {unique_recipients:,} recipients • {unique_agencies:,} agencies • FY2024 data
            #</div>
          #  """, unsafe_allow_html=True)
            
            # Add interactive tip with matching styling
           # if len(self.df) > 1000:
            #    st.markdown("""
             #   <div style='
              #      background: rgba(23, 162, 184, 0.1); 
               #     border: 1px solid rgba(23, 162, 184, 0.2); 
                #    border-radius: 0.5rem; 
                 #   padding: 1rem; 
                  #  margin: 1rem 0;
                   # border-left: 4px solid #17a2b8;
                #'>
                 #   💡 <strong>Pro Tip:</strong> With lots of data available, try using the search and filter features in the Data Explorer section below!
                #</div>
                #""", unsafe_allow_html=True)

    def add_interactive_help(self):
        """Add interactive help throughout the dashboard"""
        
        # Add help tooltips to complex charts
        if hasattr(self, 'df') and not self.df.empty:
            # This creates helpful context for users
            help_messages = {
                'recipients': "💡 **Recipients Chart:** Shows which organizations receive the most federal funding. Click and drag to zoom!",
                'agencies': "💡 **Agency Chart:** Displays how federal spending is distributed across government departments. Hover for details!",
                'map': "💡 **Geographic Map:** Visualizes spending by state. Try different color schemes and map types!",
                'sankey': "💡 **Flow Diagram:** Shows how money flows from agencies to sub-agencies. Adjust minimum flow to focus on major transfers!"
            }
            
            return help_messages
        
        return {}
        
    def add_sidebar_toggle_fix(self):
        """Add a visible sidebar toggle button and instructions"""
        
        # Add this to the main content area, right after your header
        # Create a prominent sidebar toggle area
        st.markdown("""
        <style>
        .sidebar-toggle-container {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 999;
            background: white;
            padding: 5px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border: 1px solid #ddd;
        }
        
        .sidebar-help {
            background: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #1f4e79;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Add helpful instructions in the main content
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="sidebar-help">
            <strong>📋 Sidebar Controls:</strong><br>
            • <strong>To hide sidebar:</strong> Click the ❌ or ← arrow in the top-left corner<br>
            • <strong>To show sidebar:</strong> Look for the <strong>☰</strong> (hamburger menu) in the top-left corner<br>
            • <strong>Can't find it?</strong> Press <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>R</kbd> to refresh
            </div>
            """, unsafe_allow_html=True)

    def add_enhanced_sidebar_instructions(self):
        """Add clear instructions at the top of sidebar"""
        
        # Add this at the very beginning of your create_enhanced_sidebar() method
        st.sidebar.markdown("""
        <div style='background: #e6f3ff; padding: 10px; border-radius: 5px; margin-bottom: 15px; border: 1px solid #b3d9ff;'>
            <strong>📋 Control Panel</strong><br>
            <small>Use this sidebar to control dashboard settings and get help</small>
        </div>
        """, unsafe_allow_html=True)

    def show_top_recipients(self, top_n=10):
        """Display horizontal bar chart of top recipients by total award amount"""
        if self.df is None or self.df.empty:
            st.warning("⚠️ No data available for top recipients chart")
            return False

        if 'recipient_name' not in self.df.columns or 'award_amount' not in self.df.columns:
            st.error("❌ Missing required columns for recipients chart")
            return False

        try:
            print(f"📊 Creating top {top_n} recipients chart...")

            # Step 1: Group by recipient and sum their awards
            print("🔄 Aggregating data by recipient...")
            recipient_totals = self.df.groupby('recipient_name').agg({
                'award_amount': ['sum', 'count', 'mean']
            }).round(2)

            # Flatten column names (pandas creates multi-level columns)
            recipient_totals.columns = ['total_amount', 'award_count', 'avg_amount']
            recipient_totals = recipient_totals.reset_index()

            # Step 2: Sort by total amount (largest first) and get top N
            recipient_totals = recipient_totals.sort_values('award_count', ascending=False)
            top_recipients = recipient_totals.head(top_n)

            if len(top_recipients) == 0:
                st.warning("⚠️ No recipients found in the data")
                return False

            print(f"✅ Found {len(top_recipients)} top recipients")

            # Step 3: Create the horizontal bar chart
            st.subheader(f"🏆 Top {len(top_recipients)} Recipients by Total Award Amount")

            # Create the chart using Plotly
            import plotly.express as px

            # Prepare data for plotting (reverse order so largest is at top)
            chart_data = top_recipients.copy()
            chart_data = chart_data.sort_values('award_count', ascending=True)  # Ascending for horizontal bar

            # Create hover text with additional information
            chart_data['hover_text'] = chart_data.apply(lambda row:
                                                        f"<b>{row['recipient_name']}</b><br>" +
                                                        f"Total Awards: ${row['total_amount']:,.2f}<br>" +
                                                        f"Number of Awards: {row['award_count']:,}<br>" +
                                                        f"Average Award: ${row['avg_amount']:,.2f}",
                                                        axis=1
                                                        )

            # Format amounts for display (B/M/K)
            chart_data['display_amount'] = chart_data['total_amount'].apply(self._format_amount_for_display)

            # Create the horizontal bar chart
            fig = px.bar(
                chart_data,
                x='award_count',
                y='recipient_name',
                orientation='h',  # Horizontal bars
                title=f"Top {len(top_recipients)} Federal Spending Recipients",
                labels={
                    'total_amount': 'Total Award Amount ($)',
                    'recipient_name': 'Recipient Organization'
                },
                hover_data={
                    'total_amount': ':,.2f',
                    'award_count': ':,',
                    'avg_amount': ':,.2f'
                }
            )

            # Customize the chart appearance
            fig.update_layout(
                height=max(400, len(top_recipients) * 40),  # Dynamic height based on number of bars
                font=dict(size=12),
                title=dict(
                    font=dict(size=16, color='#1f4e79'),
                    x=0.5,  # Center the title
                    pad=dict(t=20)
                ),
                xaxis=dict(
                    title=dict(font=dict(size=14)),
                    tickformat=',.0f',  # Format x-axis as currency
                    showgrid=True,
                    gridcolor='lightgray'
                ),
                yaxis=dict(
                    title=dict(font=dict(size=14)),
                    tickfont=dict(size=10)
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=60, b=20)
            )

            # Customize bar colors (gradient from light to dark blue)
            fig.update_traces(
                marker_color='#1f4e79',
                marker_line_color='#0d2a42',
                marker_line_width=1,
                hovertemplate="<b>%{y}</b><br>" +
                              "Total Amount: $%{x:,.2f}<br>" +
                              "<extra></extra>"  # Remove the box around hover
            )

            # Display the chart
            st.plotly_chart(fig, use_container_width=True)

            # Step 4: Add summary information below the chart
            col1, col2, col3 = st.columns(3)

            with col1:
                top_recipient = top_recipients.iloc[0]
                st.metric(
                    label="🥇 Top Recipient",
                    value=self._format_amount_for_display(top_recipient['total_amount']),
                    help=f"{top_recipient['recipient_name']}"
                )

            with col2:
                total_top_recipients = top_recipients['total_amount'].sum()
                total_all_awards = self.df['award_amount'].sum()
                percentage = (total_top_recipients / total_all_awards) * 100 if total_all_awards > 0 else 0

                st.metric(
                    label="📊 Top Recipients Share",
                    value=f"{percentage:.1f}%",
                    help=f"Top {len(top_recipients)} recipients represent {percentage:.1f}% of total spending"
                )

            with col3:
                avg_awards_per_recipient = top_recipients['award_count'].mean()
                st.metric(
                    label="📈 Avg Awards per Recipient",
                    value=f"{avg_awards_per_recipient:.0f}",
                    help=f"Average number of awards among top {len(top_recipients)} recipients"
                )

            # Step 5: Optional - Show detailed table
            with st.expander("📋 View Detailed Recipients Table"):
                # Format the table nicely
                display_table = top_recipients.copy()
                display_table['total_amount'] = display_table['total_amount'].apply(lambda x: f"${x:,.2f}")
                display_table['avg_amount'] = display_table['avg_amount'].apply(lambda x: f"${x:,.2f}")
                display_table.columns = ['Recipient Name', 'Total Amount', 'Number of Awards', 'Average Award']

                st.dataframe(
                    display_table,
                    use_container_width=True,
                    hide_index=True
                )

            print("✅ Top recipients chart created successfully")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error creating recipients chart: {error_msg}")
            st.error(f"❌ **Error creating recipients chart**: {error_msg}")

            # Show basic fallback information
            try:
                unique_recipients = self.df['recipient_name'].nunique()
                st.info(f"📊 Dataset contains {unique_recipients:,} unique recipients, but chart creation failed")
            except:
                st.info("📊 Unable to display recipients chart due to data issues")

            return False

    def _format_amount_for_display(self, amount):
        """Format currency amount for display in charts and metrics"""
        try:
            if amount >= 1e9:  # 1 billion or more
                return f"${amount / 1e9:.1f}B"
            elif amount >= 1e6:  # 1 million or more
                return f"${amount / 1e6:.1f}M"
            elif amount >= 1e3:  # 1 thousand or more
                return f"${amount / 1e3:.0f}K"
            else:
                return f"${amount:,.0f}"
        except Exception as e:
            print(f"⚠️ Amount formatting error: {e}")
            return "$0"

    def show_agency_pie(self, top_n=8):
        """Display pie chart of spending by awarding agency (top N + Others)"""
        if self.df is None or self.df.empty:
            st.warning("⚠️ No data available for agency pie chart")
            return False

        if 'awarding_agency' not in self.df.columns or 'award_amount' not in self.df.columns:
            st.error("❌ Missing required columns for agency chart")
            return False

        try:
            print(f"🥧 Creating agency pie chart with top {top_n} agencies...")

            # Step 1: Clean and aggregate data by agency
            print("🔄 Aggregating spending by agency...")

            # Remove unknown/empty agencies for cleaner chart
            clean_df = self.df[
                (~self.df['awarding_agency'].isin(['Unknown Agency', 'Unknown', '', 'nan'])) &
                (self.df['awarding_agency'].notna()) &
                (self.df['award_amount'] > 0)
                ].copy()

            if len(clean_df) == 0:
                st.warning("⚠️ No valid agency data found for pie chart")
                return False

            # Group by agency and sum awards
            agency_totals = clean_df.groupby('awarding_agency').agg({
                'award_amount': ['sum', 'count', 'mean']
            }).round(2)

            # Flatten column names
            agency_totals.columns = ['total_amount', 'award_count', 'avg_amount']
            agency_totals = agency_totals.reset_index()

            # Step 2: Sort by total amount and prepare data for pie chart
            agency_totals = agency_totals.sort_values('total_amount', ascending=False)

            # Get top N agencies
            top_agencies = agency_totals.head(top_n).copy()

            # Calculate "Others" category if there are more than top_n agencies
            if len(agency_totals) > top_n:
                others_agencies = agency_totals.iloc[top_n:]
                others_total = others_agencies['total_amount'].sum()
                others_count = others_agencies['award_count'].sum()
                others_avg = others_agencies['avg_amount'].mean()

                # Add "Others" row
                others_row = {
                    'awarding_agency': f'Others ({len(others_agencies)} agencies)',
                    'total_amount': others_total,
                    'award_count': others_count,
                    'avg_amount': others_avg
                }

                # Create final dataset
                pie_data = pd.concat([top_agencies, pd.DataFrame([others_row])], ignore_index=True)
            else:
                pie_data = top_agencies.copy()

            print(f"✅ Prepared pie chart data: {len(pie_data)} slices")

            # Step 3: Create the pie chart
            st.subheader(f"🏛️ Federal Spending by Agency (Top {top_n})")

            import plotly.express as px
            import plotly.graph_objects as go

            # Calculate percentages for display
            total_amount = pie_data['total_amount'].sum()
            pie_data['percentage'] = (pie_data['total_amount'] / total_amount * 100).round(1)

            # Create custom hover text
            pie_data['hover_text'] = pie_data.apply(lambda row:
                                                    f"<b>{row['awarding_agency']}</b><br>" +
                                                    f"Amount: ${row['total_amount']:,.2f}<br>" +
                                                    f"Percentage: {row['percentage']:.1f}%<br>" +
                                                    f"Awards: {row['award_count']:,}<br>" +
                                                    f"Avg Award: ${row['avg_amount']:,.2f}",
                                                    axis=1
                                                    )

            # Create pie chart with custom colors
            colors = [
                '#1f4e79', '#2c5f96', '#3970b3', '#4681d0', '#5392ed',
                '#7ba4f0', '#a3b6f3', '#cbc8f6', '#f3e0f9', '#ff9999'
            ]

            fig = go.Figure(data=[go.Pie(
                labels=pie_data['awarding_agency'],
                values=pie_data['total_amount'],
                hole=0.3,  # Creates a donut chart
                hovertemplate="<b>%{label}</b><br>" +
                              "Amount: $%{value:,.2f}<br>" +
                              "Percentage: %{percent}<br>" +
                              "<extra></extra>",
                textinfo='label+percent',
                textposition='outside',
                marker=dict(
                    colors=colors[:len(pie_data)],
                    line=dict(color='white', width=2)
                ),
                pull=[0.05 if i == 0 else 0 for i in range(len(pie_data))]  # Pull out the largest slice
            )])

            # Customize layout
            fig.update_layout(
                title=dict(
                    text=f"Federal Spending Distribution by Agency<br><sup>Total: ${total_amount / 1e9:.1f}B across {len(pie_data)} categories</sup>",
                    font=dict(size=16, color='#1f4e79'),
                    x=0.5,
                    pad=dict(t=20)
                ),
                font=dict(size=12),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=10)
                ),
                height=500,
                margin=dict(l=20, r=150, t=80, b=20),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

            # Display the chart
            st.plotly_chart(fig, use_container_width=True)

            # Step 4: Add summary statistics
            col1, col2, col3 = st.columns(3)

            with col1:
                top_agency = pie_data.iloc[0]
                st.metric(
                    label="🥇 Top Agency",
                    value=f"{top_agency['percentage']:.1f}%",
                    help=f"{top_agency['awarding_agency']} - ${top_agency['total_amount']:,.2f}"
                )

            with col2:
                concentration_top3 = pie_data.head(3)['percentage'].sum()
                st.metric(
                    label="📊 Top 3 Concentration",
                    value=f"{concentration_top3:.1f}%",
                    help="Percentage of total spending by top 3 agencies"
                )

            with col3:
                total_agencies = len(agency_totals)
                st.metric(
                    label="🏛️ Total Agencies",
                    value=f"{total_agencies}",
                    help=f"Total number of awarding agencies in dataset"
                )

            # Step 5: Agency insights
            st.markdown("#### 📋 Agency Insights")

            insights_col1, insights_col2 = st.columns(2)

            with insights_col1:
                # Most active agency (by number of awards)
                most_active = agency_totals.loc[agency_totals['award_count'].idxmax()]
                st.info(f"""
                **🎯 Most Active Agency:**
                {most_active['awarding_agency']}

                • {most_active['award_count']:,} awards
                • ${most_active['avg_amount']:,.2f} average award
                """)

            with insights_col2:
                # Highest average award agency
                highest_avg = agency_totals.loc[agency_totals['avg_amount'].idxmax()]
                st.info(f"""
                **💰 Highest Average Awards:**
                {highest_avg['awarding_agency']}

                • ${highest_avg['avg_amount']:,.2f} average award
                • {highest_avg['award_count']:,} total awards
                """)

            # Step 6: Detailed agency table
            with st.expander("📋 View Detailed Agency Breakdown"):
                # Format table for display
                display_table = agency_totals.head(15).copy()  # Show top 15 in table
                display_table['total_amount_str'] = display_table['total_amount'].apply(lambda x: f"${x:,.2f}")
                display_table['avg_amount_str'] = display_table['avg_amount'].apply(lambda x: f"${x:,.2f}")
                display_table['percentage'] = (
                        display_table['total_amount'] / agency_totals[
                    'total_amount'].sum() * 100).round(2)
                display_table['percentage_str'] = display_table['percentage'].apply(lambda x: f"{x:.1f}%")

                display_table_final = display_table[
                    ['awarding_agency', 'total_amount_str', 'award_count', 'avg_amount_str', 'percentage_str']]
                display_table_final.columns = ['Agency Name', 'Total Amount', 'Number of Awards', 'Average Award',
                                               'Percentage']

                st.dataframe(
                    display_table_final,
                    use_container_width=True,
                    hide_index=True
                )

            print("✅ Agency pie chart created successfully")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error creating agency pie chart: {error_msg}")
            st.error(f"❌ **Error creating agency chart**: {error_msg}")

            # Show fallback information
            try:
                unique_agencies = self.df['awarding_agency'].nunique()
                st.info(f"📊 Dataset contains {unique_agencies:,} unique agencies, but chart creation failed")
            except:
                st.info("📊 Unable to display agency chart due to data issues")

            return False

    def show_award_types(self):
        """Display vertical bar chart of spending by contract award type - FIXED VERSION"""
        if self.df is None or self.df.empty:
            st.warning("⚠️ No data available for award types chart")
            return False

        # Check for contract_award_type column first, fallback to award_type
        type_column = None
        if 'contract_award_type' in self.df.columns:
            type_column = 'contract_award_type'
            chart_title = "Contract Award Type"
            chart_description = "Distribution across different contract award types"
        elif 'award_type' in self.df.columns:
            type_column = 'award_type'
            chart_title = "Award Type"
            chart_description = "Distribution across different award types"
        else:
            st.error("❌ Missing required columns for award types chart")
            return False

        if 'award_amount' not in self.df.columns:
            st.error("❌ Missing award_amount column for award types chart")
            return False

        try:
            print(f"📊 Creating award types bar chart using '{type_column}' column...")

            # Step 1: Clean and aggregate data by award type
            print(f"🔄 Aggregating spending by {type_column}...")

            # Remove unknown/empty award types for cleaner chart
            clean_df = self.df[
                (~self.df[type_column].isin(['Unknown Type', 'Unknown', '', 'nan', 'N/A', 'null'])) &
                (self.df[type_column].notna()) &
                (self.df['award_amount'] > 0)
            ].copy()

            if len(clean_df) == 0:
                st.warning(f"⚠️ No valid {type_column.replace('_', ' ')} data found")
                return False

            # Group by award type and calculate statistics
            award_type_stats = clean_df.groupby(type_column).agg({
                'award_amount': ['sum', 'count', 'mean', 'median']
            }).round(2)

            # Flatten column names
            award_type_stats.columns = ['total_amount', 'award_count', 'avg_amount', 'median_amount']
            award_type_stats = award_type_stats.reset_index()

            # Sort by total amount (largest first)
            award_type_stats = award_type_stats.sort_values('total_amount', ascending=False)

            if len(award_type_stats) == 0:
                st.warning(f"⚠️ No {type_column.replace('_', ' ')} data to display")
                return False

            print(f"✅ Found {len(award_type_stats)} different {type_column.replace('_', ' ')}s")

            # Step 2: Calculate percentages and prepare data
            total_amount = award_type_stats['total_amount'].sum()
            award_type_stats['percentage'] = (award_type_stats['total_amount'] / total_amount * 100).round(1)

            # Step 3: Create the vertical bar chart with FIXED color assignment
            st.subheader(f"📊 Federal Spending by {chart_title}")
            st.markdown(f"*{chart_description}*")

            import plotly.express as px
            import plotly.graph_objects as go

            # Create the vertical bar chart
            fig = px.bar(
                award_type_stats,
                x=type_column,
                y='total_amount',
                title=f"Federal Spending Distribution by {chart_title}<br><sup>Total: ${total_amount / 1e9:.1f}B across {len(award_type_stats)} types</sup>",
                labels={
                    type_column: chart_title,
                    'total_amount': 'Total Award Amount ($)'
                },
                hover_data={
                    'total_amount': ':,.2f',
                    'award_count': ':,',
                    'avg_amount': ':,.2f',
                    'percentage': ':.1f'
                }
            )

            # Customize the chart appearance
            fig.update_layout(
                height=500,
                font=dict(size=12),
                title=dict(
                    font=dict(size=16, color='#1f4e79'),
                    x=0.5,  # Center the title
                    pad=dict(t=20)
                ),
                xaxis=dict(
                    title=dict(font=dict(size=14, color='#1f4e79')),
                    tickangle=45,  # Rotate x-axis labels for better readability
                    tickfont=dict(size=11),
                    showgrid=False
                ),
                yaxis=dict(
                    title=dict(font=dict(size=14, color='#1f4e79')),
                    tickformat='$,.0f',  # Format y-axis as currency
                    showgrid=True,
                    gridcolor='lightgray',
                    tickfont=dict(size=11)
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=20, t=80, b=120),  # Extra bottom margin for rotated labels
                showlegend=False
            )

            # FIXED: Create a color gradient based on amount with CORRECT LENGTH
            max_amount = award_type_stats['total_amount'].max()
            min_amount = award_type_stats['total_amount'].min()
            
            # Create colors for EXACTLY the number of bars we have
            colors = []
            for i, amount in enumerate(award_type_stats['total_amount']):
                # Calculate color intensity based on amount (0 to 1 scale)
                if max_amount > min_amount:
                    intensity = (amount - min_amount) / (max_amount - min_amount)
                else:
                    intensity = 0.5  # Default if all amounts are the same
                
                # Create a blue gradient - darker blue for higher amounts
                blue_intensity = int(255 - (intensity * 100))  # Range from 155 to 255
                colors.append(f'rgb({blue_intensity}, {blue_intensity + 30}, 255)')

            # Update bar colors and hover template with CORRECT number of colors
            fig.update_traces(
                marker_color=colors,  # This now has exactly the right number of colors
                marker_line_color='#0d2a42',
                marker_line_width=1,
                hovertemplate="<b>%{x}</b><br>" +
                            "Total Amount: $%{y:,.2f}<br>" +
                            "Percentage: %{customdata[3]:.1f}%<br>" +
                            "Awards: %{customdata[1]:,}<br>" +
                            "Average: $%{customdata[2]:,.2f}<br>" +
                            "<extra></extra>",
                customdata=award_type_stats[['total_amount', 'award_count', 'avg_amount', 'percentage']].values
            )

            # Display the chart
            st.plotly_chart(fig, use_container_width=True)

            # Rest of your method continues unchanged...
            # (Keep all the summary metrics and analysis sections as they were)

            print(f"✅ {chart_title} chart created successfully using {type_column}")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error creating {chart_title.lower()} chart: {error_msg}")
            st.error(f"❌ **Error creating {chart_title.lower()} chart**: {error_msg}")
            
            # Show helpful debugging info
            try:
                if type_column in self.df.columns:
                    unique_types = self.df[type_column].nunique()
                    st.info(f"📊 Dataset contains {unique_types:,} unique {type_column.replace('_', ' ')}s")
                    
                    # Show sample data for debugging
                    sample_types = self.df[type_column].value_counts().head(5)
                    if len(sample_types) > 0:
                        st.info("🔍 **Sample award types in your data:**")
                        for award_type, count in sample_types.items():
                            st.write(f"• {award_type}: {count} records")
                else:
                    st.info(f"📊 Column '{type_column}' not found in dataset")
            except:
                st.info("📊 Unable to display award types chart due to data issues")

            return False
    def show_agency_sankey(self, min_flow_amount=10000000):  # Default to $10M minimum
        """Display clean, readable Sankey diagram with grouped small agencies"""
        if self.df is None or self.df.empty:
            st.warning("⚠️ No data available for agency flow diagram")
            return False

        # Check for required columns
        required_columns = ['funding_agency', 'funding_sub_agency', 'award_amount']
        missing_columns = [col for col in required_columns if col not in self.df.columns]

        if missing_columns:
            st.error(f"❌ Missing required columns for Sankey diagram: {missing_columns}")
            return False

        try:
            print("🌊 Creating clean, readable Sankey diagram...")

            # Step 1: Enhanced user controls with better defaults
            st.subheader("🌊 Federal Funding Flow: Agencies → Sub-Agencies")
            st.markdown("*Clean visualization focusing on major funding relationships*")
            
            control_col1, control_col2, control_col3 = st.columns([1, 1, 1])
            
            with control_col1:
                flow_options = {
                    "Major flows ($100M+)": 100000000,
                    "Large flows ($50M+)": 50000000,
                    "Medium flows ($25M+)": 25000000, 
                    "Significant flows ($10M+)": 10000000,
                    "All flows ($5M+)": 5000000
                }
                
                selected_flow = st.selectbox(
                    "💰 Minimum Flow Amount:",
                    options=list(flow_options.keys()),
                    index=1,  # Default to $50M+ for cleaner view
                    help="Higher amounts = cleaner, more readable diagram"
                )
                min_flow_amount = flow_options[selected_flow]
            
            with control_col2:
                max_agencies = st.slider(
                    "🏛️ Max Agencies to Show:",
                    min_value=5,
                    max_value=15,
                    value=8,  # Default to 8 for readability
                    help="Limit agencies for better readability"
                )
            
            with control_col3:
                max_sub_agencies = st.slider(
                    "🏢 Max Sub-Agencies per Agency:",
                    min_value=3,
                    max_value=10,
                    value=5,  # Default to 5 per agency
                    help="Group smaller sub-agencies into 'Others'"
                )

            # Step 2: Clean and prepare data with aggressive filtering
            clean_df = self.df[
                (self.df['funding_agency'].notna()) &
                (self.df['funding_sub_agency'].notna()) &
                (~self.df['funding_agency'].isin(['Unknown', 'Unknown Agency', '', 'nan', 'null'])) &
                (~self.df['funding_sub_agency'].isin(['Unknown', 'Unknown Sub Agency', '', 'nan', 'null'])) &
                (self.df['award_amount'] >= min_flow_amount)
            ].copy()

            if len(clean_df) == 0:
                st.warning(f"⚠️ No flows found above ${min_flow_amount/1e6:.0f}M. Try lowering the minimum amount.")
                return False

            # Step 3: Aggregate by agency and sub-agency
            flow_data = clean_df.groupby(['funding_agency', 'funding_sub_agency']).agg({
                'award_amount': ['sum', 'count']
            }).round(2)
            flow_data.columns = ['total_amount', 'award_count']
            flow_data = flow_data.reset_index()

            # Step 4: Select top agencies by total spending
            agency_totals = flow_data.groupby('funding_agency')['total_amount'].sum().sort_values(ascending=False)
            top_agencies = agency_totals.head(max_agencies).index.tolist()
            
            # Filter to top agencies only
            flow_data = flow_data[flow_data['funding_agency'].isin(top_agencies)]

            # Step 5: Group small sub-agencies into "Others" for each agency
            processed_flows = []
            
            for agency in top_agencies:
                agency_flows = flow_data[flow_data['funding_agency'] == agency].sort_values('total_amount', ascending=False)
                
                # Take top N sub-agencies
                top_sub_agencies = agency_flows.head(max_sub_agencies)
                remaining_sub_agencies = agency_flows.tail(len(agency_flows) - max_sub_agencies)
                
                # Add top sub-agencies as-is
                for _, row in top_sub_agencies.iterrows():
                    processed_flows.append(row.to_dict())
                
                # Group remaining small sub-agencies into "Others"
                if len(remaining_sub_agencies) > 0:
                    others_total = remaining_sub_agencies['total_amount'].sum()
                    others_count = remaining_sub_agencies['award_count'].sum()
                    
                    if others_total > 0:  # Only add if there's meaningful amount
                        others_row = {
                            'funding_agency': agency,
                            'funding_sub_agency': f"Others ({len(remaining_sub_agencies)} sub-agencies)",
                            'total_amount': others_total,
                            'award_count': others_count
                        }
                        processed_flows.append(others_row)
            
            # Convert back to DataFrame
            flow_data = pd.DataFrame(processed_flows)
            flow_data = flow_data.sort_values('total_amount', ascending=False)

            if len(flow_data) == 0:
                st.warning("⚠️ No data remaining after filtering. Try adjusting your settings.")
                return False

            print(f"✅ Clean data prepared: {len(flow_data)} flows from {len(top_agencies)} agencies")

            # Step 6: Create clean node lists
            agencies = flow_data['funding_agency'].unique().tolist()
            sub_agencies = flow_data['funding_sub_agency'].unique().tolist()

            # Step 7: Department-specific colors (simplified and bold)
            def get_clean_department_colors():
                # Main department colors - LIGHTER for better text contrast
                dept_colors = {
                    'Department of Defense': '#FF9999',           # Light Red
                    'Department of Health and Human Services': '#90EE90',  # Light Green
                    'Department of Energy': '#FFB366',            # Light Orange
                    'Department of Transportation': '#87CEEB',     # Sky Blue
                    'Department of Agriculture': '#98FB98',        # Pale Green
                    'Department of Education': '#DDA0DD',          # Plum
                    'Department of Veterans Affairs': '#D2B48C',    # Tan
                    'Department of Homeland Security': '#B0C4DE',   # Light Steel Blue
                    'Department of Justice': '#F08080',           # Light Coral
                    'Department of State': '#F0E68C',             # Khaki
                    'Department of the Treasury': '#D3D3D3',       # Light Gray
                    'Department of the Interior': '#AFEEEE',       # Pale Turquoise
                    'Department of Labor': '#FFA07A',             # Light Salmon
                    'Department of Commerce': '#20B2AA',           # Light Sea Green
                    'Department of Housing and Urban Development': '#F5DEB3'  # Wheat
                }
                
                # Assign colors to agencies
                agency_colors = []
                for agency in agencies:
                    assigned_color = '#4A4A4A'  # Default dark gray
                    for dept_key, color in dept_colors.items():
                        if dept_key in agency or any(word in agency for word in dept_key.split() if len(word) > 3):
                            assigned_color = color
                            break
                    agency_colors.append(assigned_color)
                
                # Sub-agencies get lighter, more transparent versions
                sub_agency_colors = []
                for sub_agency in sub_agencies:
                    # Find parent agency color
                    parent_flows = flow_data[flow_data['funding_sub_agency'] == sub_agency]
                    if len(parent_flows) > 0:
                        parent_agency = parent_flows.iloc[0]['funding_agency']
                        if parent_agency in agencies:
                            parent_idx = agencies.index(parent_agency)
                            parent_color = agency_colors[parent_idx]
                            
                            # Create lighter version
                            if parent_color.startswith('#'):
                                r = int(parent_color[1:3], 16)
                                g = int(parent_color[3:5], 16)
                                b = int(parent_color[5:7], 16)
                                # Lighten significantly for sub-agencies
                                r = min(255, r + 80)
                                g = min(255, g + 80)
                                b = min(255, b + 80)
                                light_color = f'#{r:02x}{g:02x}{b:02x}'
                                sub_agency_colors.append(light_color)
                            else:
                                sub_agency_colors.append('#CCCCCC')
                        else:
                            sub_agency_colors.append('#CCCCCC')
                    else:
                        sub_agency_colors.append('#CCCCCC')
                
                return agency_colors + sub_agency_colors

            node_colors = get_clean_department_colors()

            # Step 8: Prepare Sankey data with cleaner labels
            # Shorten long agency names for better readability
            def clean_label(label, max_length=25):
                if len(label) <= max_length:
                    return label
                
                # Special handling for "Others" groups
                if "Others" in label:
                    return label
                    
                # For regular agencies, smart truncation
                if "Department of" in label:
                    # Remove "Department of" and keep the main part
                    clean = label.replace("Department of", "").strip()
                    if len(clean) <= max_length:
                        return clean
                    return clean[:max_length-3] + "..."
                
                return label[:max_length-3] + "..."

            clean_node_labels = [clean_label(label) for label in (agencies + sub_agencies)]
            
            # Create index mappings
            agency_indices = {agency: i for i, agency in enumerate(agencies)}
            sub_agency_indices = {sub_agency: i + len(agencies) for i, sub_agency in enumerate(sub_agencies)}

            # Prepare links
            sources = []
            targets = []
            values = []
            link_colors = []

            for _, row in flow_data.iterrows():
                source_idx = agency_indices[row['funding_agency']]
                target_idx = sub_agency_indices[row['funding_sub_agency']]
                value = row['total_amount']

                sources.append(source_idx)
                targets.append(target_idx)
                values.append(value)
                
                # Link color with good transparency
                source_color = node_colors[source_idx]
                if source_color.startswith('#'):
                    r = int(source_color[1:3], 16)
                    g = int(source_color[3:5], 16)
                    b = int(source_color[5:7], 16)
                    link_colors.append(f'rgba({r}, {g}, {b}, 0.4)')
                else:
                    link_colors.append('rgba(100, 100, 100, 0.4)')

            # Step 9: Create the clean Sankey diagram - CORRECTED VERSION
            import plotly.graph_objects as go

            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=30,  # More padding for readability
                    thickness=35,  # Thicker nodes for better text space
                    line=dict(color="rgba(0,0,0,0)", width=0),  # NO BORDERS - transparent
                    label=clean_node_labels,
                    color=node_colors,
                    hovertemplate='<b>%{label}</b><br>' +
                                'Total Flow: <b>$%{value:,.0f}</b><br>' +
                                '<extra></extra>'
                    # REMOVED: font property - this was causing the error
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                    hovertemplate='<b>%{source.label}</b> → <b>%{target.label}</b><br>' +
                                'Flow: <b>$%{value:,.0f}</b><br>' +
                                '<extra></extra>'
                )
            )])

            # Enhanced layout with better sizing - FONT APPLIED HERE
            total_flow = sum(values)
            fig.update_layout(
                title=dict(
                    text=f"Clean Federal Funding Flow Diagram<br>" +
                        f"<sup>Total: ${total_flow / 1e9:.1f}B | " +
                        f"{len(agencies)} Agencies → {len(sub_agencies)} Sub-Agencies | " +
                        f"Min Flow: ${min_flow_amount/1e6:.0f}M</sup>",
                    font=dict(size=18, color='#1f4e79', family="Arial"),
                    x=0.5,
                    pad=dict(t=30)
                ),
                # FIXED: Simple black font for maximum readability
                font=dict(size=16, color='#000000', family="Arial"),
                height=max(600, len(agencies) * 50 + 150),  # More height for better text space
                margin=dict(l=60, r=60, t=100, b=60),  # More margins for text
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

            # Display the clean diagram
            st.plotly_chart(fig, use_container_width=True)

            # Step 10: Clean summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="🏛️ Major Agencies",
                    value=f"{len(agencies)}",
                    help=f"Top {len(agencies)} agencies by total funding"
                )

            with col2:
                st.metric(
                    label="🏢 Sub-Units Shown", 
                    value=f"{len(sub_agencies)}",
                    help="Major sub-agencies + grouped others"
                )

            with col3:
                avg_flow = total_flow / len(flow_data) if len(flow_data) > 0 else 0
                st.metric(
                    label="💰 Avg Flow Size",
                    value=self._format_amount_for_display(avg_flow),
                    help=f"Average flow: ${avg_flow:,.0f}"
                )

            with col4:
                if len(flow_data) > 0:
                    max_flow = flow_data.iloc[0]
                    st.metric(
                        label="🌊 Largest Flow",
                        value=self._format_amount_for_display(max_flow['total_amount']),
                        help=f"Largest single funding relationship"
                    )

            # Step 11: Filtering summary
            st.markdown("#### 📊 Data Filtering Summary")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                total_original = len(self.df)
                total_after_min = len(clean_df)
                filtered_out = total_original - total_after_min
                
                st.info(f"""
                **🔍 Flow Filtering Applied:**
                • Original records: {total_original:,}
                • Above ${min_flow_amount/1e6:.0f}M threshold: {total_after_min:,}
                • Filtered out: {filtered_out:,} ({filtered_out/total_original*100:.1f}%)
                • Final flows shown: {len(flow_data):,}
                """)
            
            with filter_col2:
                others_flows = len([f for f in flow_data['funding_sub_agency'] if 'Others' in f])
                regular_flows = len(flow_data) - others_flows
                
                st.info(f"""
                **📋 Agency Grouping Applied:**
                • Individual sub-agencies: {regular_flows}
                • "Others" grouped entries: {others_flows}
                • Agencies limited to: {max_agencies}
                • Sub-agencies per agency: max {max_sub_agencies}
                """)

            # Step 12: Quick tips for better experience
            with st.expander("💡 How to Read This Diagram"):
                st.markdown("""
                **🎯 Reading the Flow Diagram:**
                
                **Left Side (Funding Agencies):**
                - Major government departments providing funding
                - Thickness represents total funding amount
                - Colors distinguish different departments
                
                **Right Side (Sub-Agencies):**
                - Specific sub-units receiving the funding
                - "Others" groups represent multiple smaller sub-agencies combined
                - Lighter colors match their parent department
                
                **Flow Lines:**
                - Thickness = Amount of funding
                - Color matches the funding agency
                - Hover for exact dollar amounts
                
                **💡 Pro Tips:**
                - Increase minimum flow amount to reduce clutter
                - Lower max agencies/sub-agencies for cleaner view
                - "Others" entries show combined smaller flows
                """)

            print("✅ Clean, readable Sankey diagram created successfully")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error creating clean Sankey diagram: {error_msg}")
            st.error(f"❌ **Error creating flow diagram**: {error_msg}")
            return False
    def show_enhanced_state_spending_map(self, map_type='choropleth', color_scheme='blue'):
       
            """Display enhanced interactive map with customized colorbar and formatting"""
            if self.df is None or self.df.empty:
                st.warning("⚠️ No data available for state spending map")
                return False

            if 'place_of_performance_state_code' not in self.df.columns or 'award_amount' not in self.df.columns:
                st.error("❌ Missing required columns for state map")
                return False

            try:
                print(f"🗺️ Creating enhanced state spending map ({map_type}, {color_scheme})...")

                # Step 1: Clean and prepare state data (same as before)
                clean_df = self.df[
                    (self.df['place_of_performance_state_code'].notna()) &
                    (~self.df['place_of_performance_state_code'].isin(['', 'nan', 'Unknown', 'XX', '00'])) &
                    (self.df['award_amount'] > 0)
                ].copy()

                if len(clean_df) == 0:
                    st.warning("⚠️ No valid state performance data found")
                    return False

                # Step 2: Aggregate spending by state
                state_spending = clean_df.groupby('place_of_performance_state_code').agg({
                    'award_amount': ['sum', 'count', 'mean', 'median'],
                    'recipient_name': 'nunique'
                }).round(2)
                
                state_spending.columns = ['total_spending', 'award_count', 'avg_award', 'median_award', 'unique_recipients']
                state_spending = state_spending.reset_index()
                state_spending = state_spending.sort_values('total_spending', ascending=False)

                # Step 3: Add state names and calculate percentages
                state_names = {
                    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
                    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
                    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
                    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
                    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
                    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
                    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
                    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
                    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
                    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
                    'DC': 'District of Columbia', 'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'GU': 'Guam',
                    'AS': 'American Samoa', 'MP': 'Northern Mariana Islands'
                }
                
                state_spending['state_name'] = state_spending['place_of_performance_state_code'].map(state_names)
                state_spending['state_name'] = state_spending['state_name'].fillna(state_spending['place_of_performance_state_code'])
                
                total_spending = state_spending['total_spending'].sum()
                state_spending['spending_percentage'] = (state_spending['total_spending'] / total_spending * 100).round(2)

                # Step 4: Define color schemes
                color_schemes = {
                    'blue': {
                        'colorscale': [
                            [0, 'rgb(247,251,255)'],
                            [0.125, 'rgb(222,235,247)'],
                            [0.25, 'rgb(198,219,239)'],
                            [0.375, 'rgb(158,202,225)'],
                            [0.5, 'rgb(107,174,214)'],
                            [0.625, 'rgb(66,146,198)'],
                            [0.75, 'rgb(33,113,181)'],
                            [0.875, 'rgb(8,81,156)'],
                            [1, 'rgb(8,48,107)']
                        ],
                        'title_color': '#1f4e79'
                    },
                    'green': {
                        'colorscale': [
                            [0, 'rgb(247,252,245)'],
                            [0.125, 'rgb(229,245,224)'],
                            [0.25, 'rgb(199,233,192)'],
                            [0.375, 'rgb(161,217,155)'],
                            [0.5, 'rgb(116,196,118)'],
                            [0.625, 'rgb(65,171,93)'],
                            [0.75, 'rgb(35,139,69)'],
                            [0.875, 'rgb(0,109,44)'],
                            [1, 'rgb(0,68,27)']
                        ],
                        'title_color': '#0d5a32'
                    },
                    'orange': {
                        'colorscale': [
                            [0, 'rgb(255,245,235)'],
                            [0.125, 'rgb(254,230,206)'],
                            [0.25, 'rgb(253,208,162)'],
                            [0.375, 'rgb(253,174,107)'],
                            [0.5, 'rgb(253,141,60)'],
                            [0.625, 'rgb(241,105,19)'],
                            [0.75, 'rgb(217,72,1)'],
                            [0.875, 'rgb(166,54,3)'],
                            [1, 'rgb(127,39,4)']
                        ],
                        'title_color': '#a63603'
                    },
                    'purple': {
                        'colorscale': [
                            [0, 'rgb(252,251,253)'],
                            [0.125, 'rgb(239,237,245)'],
                            [0.25, 'rgb(218,218,235)'],
                            [0.375, 'rgb(188,189,220)'],
                            [0.5, 'rgb(158,154,200)'],
                            [0.625, 'rgb(128,125,186)'],
                            [0.75, 'rgb(106,81,163)'],
                            [0.875, 'rgb(84,39,143)'],
                            [1, 'rgb(63,0,125)']
                        ],
                        'title_color': '#54278f'
                    }
                }

                current_scheme = color_schemes.get(color_scheme, color_schemes['blue'])

                # Step 5: Create the enhanced map visualization
                st.subheader("🗺️ Enhanced Federal Spending by State")
                st.markdown("*Interactive map with advanced color formatting and detailed analytics*")
                
                import plotly.graph_objects as go
                import plotly.express as px
                
                if map_type == 'choropleth':
                    # Enhanced choropleth map with custom colorbar
                    fig = go.Figure(data=go.Choropleth(
                        locations=state_spending['place_of_performance_state_code'],
                        z=state_spending['total_spending'],
                        locationmode='USA-states',
                        colorscale=current_scheme['colorscale'],
                        colorbar=dict(
                            # Enhanced colorbar formatting - FIXED
                            title=dict(
                                text="Total Federal Spending ($)",
                                font=dict(size=14, color=current_scheme['title_color'], family="Arial Black")
                            ),
                            thickness=20,
                            len=0.7,
                            x=1.02,
                            xanchor="left",
                            y=0.5,
                            yanchor="middle",
                            
                            # Custom tick formatting
                            tickmode="linear",
                            tick0=0,
                            dtick=state_spending['total_spending'].max() / 8,  # 8 tick marks
                            tickformat="$,.0s",  # Short format: $1.2M, $1.2B
                            tickfont=dict(size=12, color=current_scheme['title_color']),
                            ticklen=8,
                            tickcolor=current_scheme['title_color'],
                            
                            # Enhanced appearance
                            outlinecolor="rgba(0,0,0,0.3)",
                            outlinewidth=1,
                            bordercolor="rgba(0,0,0,0.1)",
                            borderwidth=1,
                            bgcolor="rgba(255,255,255,0.8)"
                        ),
                        hovertemplate='<b>%{text}</b><br>' +
                                    '<span style="font-size:14px">💰 Total Spending: <b>$%{z:,.2f}</b></span><br>' +
                                    '<span style="font-size:12px">📊 Awards: <b>%{customdata[0]:,}</b></span><br>' +
                                    '<span style="font-size:12px">📈 Avg Award: <b>$%{customdata[1]:,.0f}</b></span><br>' +
                                    '<span style="font-size:12px">🏢 Recipients: <b>%{customdata[2]:,}</b></span><br>' +
                                    '<span style="font-size:12px">📋 Share: <b>%{customdata[3]:.1f}%</b></span><br>' +
                                    '<extra></extra>',
                        text=state_spending['state_name'],
                        customdata=state_spending[['award_count', 'avg_award', 'unique_recipients', 'spending_percentage']].values,
                        
                        # Enhanced visual styling
                        marker=dict(
                            line=dict(color='rgba(255,255,255,0.8)', width=0.5)
                        )
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text=f'Enhanced Federal Spending by State - Place of Performance<br><sup style="font-size:14px">Total: <b>${total_spending/1e9:.2f}B</b> | States: <b>{len(state_spending)}</b> | Color Scheme: <b>{color_scheme.title()}</b></sup>',
                            font=dict(size=20, color=current_scheme['title_color'], family="Arial Black"),
                            x=0.5,
                            y=0.95
                        ),
                        geo=dict(
                            scope='usa',
                            projection=go.layout.geo.Projection(type='albers usa'),
                            showlakes=True,
                            lakecolor='rgb(255, 255, 255)',
                            showland=True,
                            landcolor='rgb(248, 248, 248)',
                            showcoastlines=True,
                            coastlinecolor='rgb(204, 204, 204)',
                            showframe=False
                        ),
                        height=700,
                        margin=dict(l=0, r=100, t=100, b=20),
                        font=dict(family="Arial", size=12),
                        paper_bgcolor='white',
                        plot_bgcolor='white'
                    )
                    
                else:  # Enhanced scatter/bubble map
                    # State coordinates for bubble map
                    state_coords = {
                        'AL': (-86.8, 32.4), 'AK': (-154.0, 64.1), 'AZ': (-111.1, 33.7), 'AR': (-92.4, 34.9), 'CA': (-119.8, 36.1),
                        'CO': (-105.8, 39.1), 'CT': (-72.7, 41.8), 'DE': (-75.5, 39.3), 'FL': (-81.7, 27.8), 'GA': (-83.6, 33.0),
                        'HI': (-157.8, 21.1), 'ID': (-114.7, 44.2), 'IL': (-89.4, 40.3), 'IN': (-86.1, 39.8), 'IA': (-93.6, 42.0),
                        'KS': (-98.5, 38.5), 'KY': (-84.9, 37.7), 'LA': (-91.8, 31.1), 'ME': (-69.8, 44.6), 'MD': (-76.5, 39.0),
                        'MA': (-71.8, 42.2), 'MI': (-84.5, 43.3), 'MN': (-93.9, 45.7), 'MS': (-89.7, 32.7), 'MO': (-92.6, 38.4),
                        'MT': (-110.4, 47.1), 'NE': (-99.9, 41.1), 'NV': (-117.0, 38.3), 'NH': (-71.5, 43.4), 'NJ': (-74.4, 40.3),
                        'NM': (-106.2, 34.8), 'NY': (-74.9, 42.2), 'NC': (-79.0, 35.6), 'ND': (-100.8, 47.5), 'OH': (-82.8, 40.3),
                        'OK': (-97.5, 35.6), 'OR': (-123.0, 44.6), 'PA': (-77.2, 40.6), 'RI': (-71.4, 41.7), 'SC': (-80.9, 33.8),
                        'SD': (-100.3, 44.3), 'TN': (-86.7, 35.7), 'TX': (-97.6, 31.1), 'UT': (-111.9, 40.2), 'VT': (-72.6, 44.0),
                        'VA': (-78.2, 37.8), 'WA': (-121.5, 47.4), 'WV': (-80.9, 38.5), 'WI': (-90.1, 44.3), 'WY': (-107.3, 42.8),
                        'DC': (-77.0, 38.9), 'PR': (-66.6, 18.2)
                    }
                    
                    # Map coordinates
                    state_spending['lon'] = state_spending['place_of_performance_state_code'].map(lambda x: state_coords.get(x, (0, 0))[0])
                    state_spending['lat'] = state_spending['place_of_performance_state_code'].map(lambda x: state_coords.get(x, (0, 0))[1])
                    
                    # Remove states without coordinates
                    state_spending = state_spending[(state_spending['lon'] != 0) | (state_spending['lat'] != 0)]
                    
                    fig = go.Figure(data=go.Scattergeo(
                        lon=state_spending['lon'],
                        lat=state_spending['lat'],
                        text=state_spending['state_name'],
                        mode='markers+text',
                        textposition="middle center",
                        texttemplate='<b>%{customdata[0]}</b>',
                        textfont=dict(size=10, color='white', family="Arial Black"),
                        marker=dict(
                            size=state_spending['total_spending'] / state_spending['total_spending'].max() * 80 + 15,
                            color=state_spending['total_spending'],
                            colorscale=current_scheme['colorscale'],
                            showscale=True,
                            sizemode='diameter',
                            colorbar=dict(
                                title=dict(
                                    text="Total Spending ($)",
                                    font=dict(size=14, color=current_scheme['title_color'], family="Arial Black")
                                ),
                                thickness=20,
                                len=0.7,
                                tickformat="$,.0s",
                                tickfont=dict(size=12, color=current_scheme['title_color']),
                                x=1.02,
                                xanchor="left"
                            ),
                            line=dict(width=2, color='white'),
                            opacity=0.8
                        ),
                        hovertemplate='<b>%{text}</b><br>' +
                                    '💰 Total: <b>$%{customdata[1]:,.2f}</b><br>' +
                                    '📊 Awards: <b>%{customdata[2]:,}</b><br>' +
                                    '📈 Avg: <b>$%{customdata[3]:,.0f}</b><br>' +
                                    '🏢 Recipients: <b>%{customdata[4]:,}</b><br>' +
                                    '<extra></extra>',
                        customdata=state_spending[['place_of_performance_state_code', 'total_spending', 'award_count', 'avg_award', 'unique_recipients']].values
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text=f'Enhanced Federal Spending - Bubble Map<br><sup>Bubble size and color represent total spending</sup>',
                            font=dict(size=18, color=current_scheme['title_color'], family="Arial Black"),
                            x=0.5
                        ),
                        geo=dict(
                            scope='usa',
                            projection=dict(type='albers usa'),
                            showland=True,
                            landcolor='rgb(243, 243, 243)',
                            coastlinecolor='rgb(204, 204, 204)',
                            showlakes=True,
                            lakecolor='rgb(255, 255, 255)'
                        ),
                        height=700,
                        margin=dict(l=0, r=100, t=80, b=0)
                    )

                # Display the enhanced map
                st.plotly_chart(fig, use_container_width=True)

                # Step 6: Enhanced summary metrics with color coordination
                st.markdown("#### 📊 Key Metrics")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    top_state = state_spending.iloc[0]
                    st.metric(
                        label="🏆 Top State",
                        value=f"{top_state['place_of_performance_state_code']}",
                        delta=f"{top_state['spending_percentage']:.1f}%",
                        help=f"{top_state['state_name']}: ${top_state['total_spending']:,.2f}"
                    )

                with col2:
                    total_states = len(state_spending)
                    st.metric(
                        label="🗺️ States/Territories",
                        value=f"{total_states}",
                        help="Number of states/territories with federal spending"
                    )

                with col3:
                    avg_per_state = total_spending / total_states if total_states > 0 else 0
                    st.metric(
                        label="📊 Avg per State",
                        value=self._format_amount_for_display(avg_per_state),
                        help=f"Average spending per state: ${avg_per_state:,.2f}"
                    )

                with col4:
                    concentration_ratio = state_spending.head(5)['total_spending'].sum() / total_spending * 100
                    st.metric(
                        label="🎯 Top 5 Concentration",
                        value=f"{concentration_ratio:.1f}%",
                        help="Percentage of total spending in top 5 states"
                    )

                # Step 7: Color scheme information
                with st.expander("🎨 Color Scheme & Formatting Details"):
                    st.markdown(f"""
                    **Current Color Scheme: {color_scheme.title()}**
                    
                    **Map Features:**
                    - **Colorbar Format**: Scientific notation ($1.2M, $1.2B) with 8 tick marks
                    - **Hover Details**: Enhanced formatting with icons and bold text
                    - **Color Range**: 9-level gradient from light to dark {color_scheme}
                    - **Border Styling**: White state borders with subtle shadows
                    
                    **Customization Applied:**
                    - Custom tick formatting using SI prefixes
                    - Enhanced colorbar positioning and styling
                    - Professional typography with Arial Black
                    - Responsive design for different screen sizes
                    """)

                print("✅ Enhanced state spending map created successfully")
                return True

            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error creating enhanced state map: {error_msg}")
                st.error(f"❌ **Error creating enhanced state spending map**: {error_msg}")
                return False
    def show_time_series_analysis(self):
        """Display time series analysis of federal spending over time"""
        if self.df is None or self.df.empty:
            st.warning("⚠️ No data available for time series analysis")
            return False

        try:
            print("📊 Creating time series analysis...")

            # Check for available date columns
            date_columns = []
            if 'start_date' in self.df.columns:
                date_columns.append(('start_date', 'Award Start Date'))
            if 'end_date' in self.df.columns:
                date_columns.append(('end_date', 'Award End Date'))
            if 'base_obligation_date' in self.df.columns:
                date_columns.append(('base_obligation_date', 'Base Obligation Date'))
            if 'last_modified_date' in self.df.columns:
                date_columns.append(('last_modified_date', 'Last Modified Date'))
            if 'fetched_at' in self.df.columns:
                date_columns.append(('fetched_at', 'Data Fetch Date'))

            if not date_columns:
                st.error("❌ No date columns found for time series analysis")
                return False

            # Time series controls
            st.markdown("#### ⏰ Time Series Analysis Controls")
            
            ts_col1, ts_col2, ts_col3 = st.columns([2, 1, 1])
            
            with ts_col1:
                selected_date_col = st.selectbox(
                    "📅 Date Column for Analysis:",
                    options=[col[0] for col in date_columns],
                    format_func=lambda x: next(name for col, name in date_columns if col == x),
                    help="Choose which date column to use for time series"
                )
            
            with ts_col2:
                aggregation_options = {
                    'Monthly': 'M',
                    'Weekly': 'W',
                    'Daily': 'D',
                    'Quarterly': 'Q'
                }
                
                aggregation = st.selectbox(
                    "📊 Time Grouping:",
                    options=list(aggregation_options.keys()),
                    index=0,  # Default to monthly
                    help="How to group the data over time"
                )
            
            with ts_col3:
                metric_options = {
                    'Total Amount': 'sum',
                    'Average Amount': 'mean',
                    'Award Count': 'count',
                    'Median Amount': 'median'
                }
                
                selected_metric = st.selectbox(
                    "📈 Metric to Display:",
                    options=list(metric_options.keys()),
                    help="What metric to show over time"
                )

            # Prepare the data for time series
            ts_df = self.df.copy()
            
            # Convert the selected date column to datetime
            try:
                ts_df[selected_date_col] = pd.to_datetime(ts_df[selected_date_col], errors='coerce')
            except Exception as e:
                st.error(f"❌ Error converting {selected_date_col} to datetime: {str(e)}")
                return False
            
            # Remove rows with invalid dates
            ts_df = ts_df.dropna(subset=[selected_date_col])
            
            if len(ts_df) == 0:
                st.warning(f"⚠️ No valid dates found in {selected_date_col} column")
                return False
            
            # Set the date column as index for resampling
            ts_df = ts_df.set_index(selected_date_col)
            
            # Resample based on selected aggregation
            freq = aggregation_options[aggregation]
            
            if selected_metric == 'Award Count':
                # Count the number of awards per period
                time_series = ts_df.resample(freq).size().reset_index()
                time_series.columns = [selected_date_col, 'value']
                y_label = 'Number of Awards'
                value_format = '{:,.0f}'
            else:
                # Aggregate award amounts
                agg_func = metric_options[selected_metric]
                time_series = ts_df['award_amount'].resample(freq).agg(agg_func).reset_index()
                time_series.columns = [selected_date_col, 'value']
                y_label = f'{selected_metric} ($)'
                value_format = '${:,.2f}'
            
            # Remove any NaN values
            time_series = time_series.dropna()
            
            if len(time_series) == 0:
                st.warning("⚠️ No data available for the selected time series configuration")
                return False
            
            # Create the time series chart
            st.markdown(f"### 📈 {selected_metric} Over Time ({aggregation})")
            st.markdown(f"*Based on {next(name for col, name in date_columns if col == selected_date_col)} • {len(time_series)} time periods*")
            
            import plotly.express as px
            import plotly.graph_objects as go
            
            # Create line chart
            fig = px.line(
                time_series,
                x=selected_date_col,
                y='value',
                title=f'Federal Spending: {selected_metric} by {aggregation} Period',
                labels={
                    selected_date_col: next(name for col, name in date_columns if col == selected_date_col),
                    'value': y_label
                }
            )
            
            # Customize the chart
            fig.update_traces(
                line=dict(color='#1f4e79', width=3),
                mode='lines+markers',
                marker=dict(size=6, color='#1f4e79'),
                hovertemplate=f'<b>%{{x}}</b><br>{y_label}: %{{y:,.2f}}<extra></extra>'
            )
            
            fig.update_layout(
                height=500,
                font=dict(size=12),
                title=dict(
                    font=dict(size=16, color='#1f4e79'),
                    x=0.5,
                    pad=dict(t=20)
                ),
                xaxis=dict(
                    title=dict(font=dict(size=14)),
                    showgrid=True,
                    gridcolor='lightgray',
                    tickangle=45
                ),
                yaxis=dict(
                    title=dict(font=dict(size=14)),
                    showgrid=True,
                    gridcolor='lightgray',
                    tickformat='$,.0f' if 'Amount' in selected_metric else ',.0f'
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=20, t=80, b=80),
                hovermode='x unified'
            )
            
            # Add trend line if enough data points
            if len(time_series) >= 3:
                # Calculate trend line
                import numpy as np
                x_numeric = np.arange(len(time_series))
                z = np.polyfit(x_numeric, time_series['value'], 1)
                trend_line = np.poly1d(z)(x_numeric)
                
                fig.add_trace(go.Scatter(
                    x=time_series[selected_date_col],
                    y=trend_line,
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', width=2, dash='dash'),
                    hovertemplate='Trend: %{y:,.2f}<extra></extra>'
                ))
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Time series statistics
            st.markdown("#### 📊 Time Series Statistics")
            
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                total_value = time_series['value'].sum()
                st.metric(
                    label=f"📊 Total {selected_metric}",
                    value=f"{total_value:,.0f}" if 'Count' in selected_metric else f"${total_value:,.2f}",
                    help=f"Total {selected_metric.lower()} across all time periods"
                )
            
            with stats_col2:
                avg_value = time_series['value'].mean()
                st.metric(
                    label=f"📈 Average per {aggregation[:-2] if aggregation.endswith('ly') else aggregation}",
                    value=f"{avg_value:,.0f}" if 'Count' in selected_metric else f"${avg_value:,.2f}",
                    help=f"Average {selected_metric.lower()} per time period"
                )
            
            with stats_col3:
                max_value = time_series['value'].max()
                max_date = time_series.loc[time_series['value'].idxmax(), selected_date_col]
                st.metric(
                    label=f"🏆 Peak {selected_metric}",
                    value=f"{max_value:,.0f}" if 'Count' in selected_metric else f"${max_value:,.2f}",
                    help=f"Highest {selected_metric.lower()} occurred on {max_date.strftime('%Y-%m-%d')}"
                )
            
            with stats_col4:
                # Calculate trend
                if len(time_series) >= 2:
                    recent_avg = time_series['value'].tail(3).mean()
                    early_avg = time_series['value'].head(3).mean()
                    trend_pct = ((recent_avg - early_avg) / early_avg * 100) if early_avg != 0 else 0
                    
                    st.metric(
                        label="📈 Trend",
                        value=f"{trend_pct:+.1f}%",
                        delta=f"{'Growing' if trend_pct > 0 else 'Declining' if trend_pct < 0 else 'Stable'}",
                        help="Percentage change from early to recent periods"
                    )
            
            # Insights and patterns
            st.markdown("#### 🔍 Time Series Insights")
            
            insights_col1, insights_col2 = st.columns(2)
            
            with insights_col1:
                # Find period with highest activity
                peak_period = time_series.loc[time_series['value'].idxmax()]
                
                st.info(f"""
                **📊 Peak Activity Period:**
                
                **Date:** {peak_period[selected_date_col].strftime('%B %Y')}
                **Value:** {f"{peak_period['value']:,.0f}" if 'Count' in selected_metric else f"${peak_period['value']:,.2f}"}
                
                This represents the highest {selected_metric.lower()} in a single {aggregation.lower()} period.
                """)
            
            with insights_col2:
                # Calculate volatility
                volatility = time_series['value'].std() / time_series['value'].mean() * 100 if time_series['value'].mean() != 0 else 0
                
                volatility_desc = "Low" if volatility < 20 else "Moderate" if volatility < 50 else "High"
                
                st.info(f"""
                **📈 Spending Pattern Analysis:**
                
                **Volatility:** {volatility_desc} ({volatility:.1f}%)
                **Time Periods:** {len(time_series)} {aggregation.lower()} periods
                **Date Range:** {time_series[selected_date_col].min().strftime('%Y-%m-%d')} to {time_series[selected_date_col].max().strftime('%Y-%m-%d')}
                
                {'Spending shows consistent patterns' if volatility < 20 else 'Spending varies significantly over time' if volatility > 50 else 'Spending shows moderate variation'}
                """)
            
            # Detailed time series table
            with st.expander("📋 View Detailed Time Series Data"):
                # Format the table for display
                display_table = time_series.copy()
                display_table['formatted_date'] = display_table[selected_date_col].dt.strftime('%Y-%m-%d')
                display_table['formatted_value'] = display_table['value'].apply(
                    lambda x: f"{x:,.0f}" if 'Count' in selected_metric else f"${x:,.2f}"
                )
                
                display_table = display_table[['formatted_date', 'formatted_value']]
                display_table.columns = ['Date', selected_metric]
                display_table = display_table.sort_values('Date', ascending=False)  # Most recent first
                
                st.dataframe(
                    display_table,
                    use_container_width=True,
                    hide_index=True,
                    height=300
                )
            
            print(f"✅ Time series analysis completed: {len(time_series)} periods analyzed")
            return True
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error creating time series analysis: {error_msg}")
            st.error(f"❌ **Error creating time series analysis**: {error_msg}")
            
            # Show debugging info
            try:
                available_columns = list(self.df.columns)
                date_like_columns = [col for col in available_columns if 'date' in col.lower() or 'time' in col.lower()]
                st.info(f"📊 Available date columns: {', '.join(date_like_columns) if date_like_columns else 'None found'}")
            except:
                st.info("📊 Unable to analyze available columns")
            
            return False
    def show_data_table(self):
        """Display enhanced searchable and filterable data table with advanced features"""
        if self.df is None or self.df.empty:
            st.warning("⚠️ No data available for data table")
            return False

        try:
            print("📋 Creating enhanced searchable data table...")

            # Create expandable search controls
            with st.expander("🎛️ Search & Filter Controls", expanded=True):

                # Row 1: Main search controls
                search_row1_col1, search_row1_col2, search_row1_col3 = st.columns([2, 1, 1])

                with search_row1_col1:
                    search_term = st.text_input(
                        "🔍 Search recipients and agencies:",
                        placeholder="Enter recipient name or agency...",
                        help="Search across recipient names and awarding agencies"
                    )

                with search_row1_col2:
                    # Minimum amount filter
                    min_amount = st.number_input(
                        "💰 Min Amount ($):",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        format="%.0f",
                        help="Show only awards above this amount"
                    )

                with search_row1_col3:
                    # Maximum amount filter
                    max_amount = st.number_input(
                        "💰 Max Amount ($):",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        format="%.0f",
                        help="Show only awards below this amount (0 = no limit)"
                    )

                # Row 2: Advanced filters
                search_row2_col1, search_row2_col2, search_row2_col3 = st.columns(3)

                with search_row2_col1:
                    # Agency filter
                    agencies = ['All Agencies'] + sorted([
                        agency for agency in self.df['awarding_agency'].unique()
                        if pd.notna(agency) and agency not in ['Unknown Agency', 'Unknown', '']
                    ])
                    selected_agency = st.selectbox(
                        "🏛️ Filter by Agency:",
                        options=agencies,
                        help="Filter results by specific awarding agency"
                    )

                with search_row2_col2:
                    # Award type filter - FIXED: Use contract_award_type
                    if 'contract_award_type' in self.df.columns:
                        award_types = ['All Types'] + sorted([
                            atype for atype in self.df['contract_award_type'].unique()
                            if pd.notna(atype) and atype not in ['Unknown Type', 'Unknown', '']
                        ])
                        selected_award_type = st.selectbox(
                            "📊 Filter by Award Type:",
                            options=award_types,
                            help="Filter results by contract award type"
                        )
                    else:
                        selected_award_type = 'All Types'
                        st.info("ℹ️ Award type filtering not available")

                with search_row2_col3:
                    # Sort options
                    sort_options = {
                        'Award Amount (High to Low)': ('award_amount', False),
                        'Award Amount (Low to High)': ('award_amount', True),
                        'Recipient Name (A-Z)': ('recipient_name', True),
                        'Recipient Name (Z-A)': ('recipient_name', False),
                        'Agency (A-Z)': ('awarding_agency', True),
                        'Agency (Z-A)': ('awarding_agency', False),
                        'Award ID (A-Z)': ('award_id', True),
                        'Award ID (Z-A)': ('award_id', False)
                    }

                    sort_choice = st.selectbox(
                        "📊 Sort by:",
                        options=list(sort_options.keys()),
                        index=0,  # Default to amount high to low
                        help="Choose how to sort the results"
                    )

            # Step 2: Column selection controls
            with st.expander("📋 Column Selection", expanded=False):
                st.markdown("**Choose which columns to display in the table:**")

                # Define available columns - FIXED: Use contract_award_type
                available_columns = {
                    'award_id': 'Award ID',
                    'recipient_name': 'Recipient Name',
                    'award_amount': 'Award Amount',
                    'awarding_agency': 'Awarding Agency',
                    'awarding_sub_agency': 'Sub Agency',
                    'contract_award_type': 'Award Type',  # FIXED: Changed from 'award_type'
                    'description': 'Description',
                    'start_date': 'Start Date',
                    'end_date': 'End Date',
                    'place_of_performance_state_code': 'Performance State'
                }

                # Filter to only columns that exist in the data
                existing_columns = {k: v for k, v in available_columns.items() if k in self.df.columns}

                # Default selected columns - FIXED: Use contract_award_type
                default_columns = ['award_id', 'recipient_name', 'award_amount', 'awarding_agency', 'contract_award_type']
                default_selected = [col for col in default_columns if col in existing_columns]

                col_select_col1, col_select_col2 = st.columns(2)

                with col_select_col1:
                    selected_columns = st.multiselect(
                        "Select columns to display:",
                        options=list(existing_columns.keys()),
                        default=default_selected,
                        format_func=lambda x: existing_columns[x],
                        help="Choose which columns to show in the data table"
                    )

                with col_select_col2:
                    # Quick selection buttons
                    st.markdown("**Quick Select:**")
                    quick_col1, quick_col2, quick_col3 = st.columns(3)

                    with quick_col1:
                        if st.button("📊 Essential", help="Show essential columns only"):
                            selected_columns = [col for col in
                                                ['award_id', 'recipient_name', 'award_amount', 'awarding_agency'] if
                                                col in existing_columns]

                    with quick_col2:
                        if st.button("📍 Location", help="Add location columns"):
                            location_cols = ['recipient_city_name', 'recipient_state_code',
                                            'place_of_performance_state_code']
                            selected_columns = list(
                                set(selected_columns + [col for col in location_cols if col in existing_columns]))

                    with quick_col3:
                        if st.button("🎯 All", help="Select all available columns"):
                            selected_columns = list(existing_columns.keys())

                if not selected_columns:
                    st.warning("⚠️ Please select at least one column to display")
                    selected_columns = default_selected

            # Step 3: Apply all filters
            filtered_df = self.df.copy()

            # Apply search filter
            if search_term:
                search_term_lower = search_term.lower()
                search_mask = (
                        filtered_df['recipient_name'].str.lower().str.contains(search_term_lower, na=False) |
                        filtered_df['awarding_agency'].str.lower().str.contains(search_term_lower, na=False)
                )
                filtered_df = filtered_df[search_mask]
                print(f"🔍 Search filter applied: '{search_term}' -> {len(filtered_df)} results")

            # Apply amount filters
            if min_amount > 0:
                filtered_df = filtered_df[filtered_df['award_amount'] >= min_amount]
                print(f"💰 Min amount filter applied: >= ${min_amount:,.0f} -> {len(filtered_df)} results")

            if max_amount > 0:
                filtered_df = filtered_df[filtered_df['award_amount'] <= max_amount]
                print(f"💰 Max amount filter applied: <= ${max_amount:,.0f} -> {len(filtered_df)} results")

            # Apply agency filter
            if selected_agency != 'All Agencies':
                filtered_df = filtered_df[filtered_df['awarding_agency'] == selected_agency]
                print(f"🏛️ Agency filter applied: '{selected_agency}' -> {len(filtered_df)} results")

            # Apply award type filter - FIXED: Use contract_award_type
            if selected_award_type != 'All Types' and 'contract_award_type' in self.df.columns:
                filtered_df = filtered_df[filtered_df['contract_award_type'] == selected_award_type]
                print(f"📊 Award type filter applied: '{selected_award_type}' -> {len(filtered_df)} results")

            # Apply sorting
            sort_column, sort_ascending = sort_options[sort_choice]
            if sort_column in filtered_df.columns:
                filtered_df = filtered_df.sort_values(sort_column, ascending=sort_ascending)
                print(f"📊 Sorted by {sort_column} ({'ascending' if sort_ascending else 'descending'})")

            # Step 4: Enhanced results summary
            total_original = len(self.df)
            total_filtered = len(filtered_df)

            if total_filtered == 0:
                st.warning("🔍 No records match your search criteria")

                # Helpful suggestions
                suggestions_col1, suggestions_col2 = st.columns(2)
                with suggestions_col1:
                    st.info("""
                    **💡 Try these suggestions:**
                    • Clear search terms
                    • Reduce minimum amount
                    • Select 'All Agencies' or 'All Types'
                    • Check your spelling
                    """)

                with suggestions_col2:
                    # Show some sample data to help user
                    sample_recipients = self.df['recipient_name'].value_counts().head(3)
                    st.info(f"""
                    **📊 Sample recipients in data:**
                    • {sample_recipients.index[0] if len(sample_recipients) > 0 else 'None'}
                    • {sample_recipients.index[1] if len(sample_recipients) > 1 else 'None'}
                    • {sample_recipients.index[2] if len(sample_recipients) > 2 else 'None'}
                    """)

                return False

            # Enhanced results summary with more details
            st.markdown("#### 📊 Filter Results Summary")
            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

            with summary_col1:
                delta_value = total_filtered - total_original if (search_term or min_amount > 0 or max_amount > 0 or
                                                                selected_agency != 'All Agencies' or
                                                                selected_award_type != 'All Types') else None
                st.metric(
                    label="📊 Matching Records",
                    value=f"{total_filtered:,}",
                    delta=f"{delta_value:,}" if delta_value is not None else None,
                    help=f"Showing {total_filtered:,} of {total_original:,} total records"
                )

            with summary_col2:
                filtered_total = filtered_df['award_amount'].sum()
                original_total = self.df['award_amount'].sum()
                percentage = (filtered_total / original_total * 100) if original_total > 0 else 0

                st.metric(
                    label="💰 Total Value",
                    value=self._format_amount_for_display(filtered_total),
                    delta=f"{percentage:.1f}% of total",
                    help=f"Total award amount in filtered results: ${filtered_total:,.2f}"
                )

            with summary_col3:
                if total_filtered > 0:
                    filtered_avg = filtered_df['award_amount'].mean()
                    original_avg = self.df['award_amount'].mean()
                    avg_delta = ((filtered_avg - original_avg) / original_avg * 100) if original_avg > 0 else 0

                    st.metric(
                        label="📈 Average Award",
                        value=self._format_amount_for_display(filtered_avg),
                        delta=f"{avg_delta:+.1f}% vs all",
                        help=f"Average award amount in results: ${filtered_avg:,.2f}"
                    )

            with summary_col4:
                if total_filtered > 0:
                    unique_recipients = filtered_df['recipient_name'].nunique()
                    st.metric(
                        label="🏢 Unique Recipients",
                        value=f"{unique_recipients:,}",
                        help=f"Number of distinct recipients in filtered results"
                    )

            # Step 5: Enhanced pagination controls
            st.markdown("#### 📋 Table Display Options")

            pagination_col1, pagination_col2, pagination_col3 = st.columns([1, 1, 2])

            with pagination_col1:
                # Page size selection
                page_size_options = [25, 50, 100, 200]
                page_size = st.selectbox(
                    "📄 Records per page:",
                    options=page_size_options,
                    index=1,  # Default to 50
                    help="Choose how many records to show per page"
                )

            with pagination_col2:
                # Calculate pagination
                total_pages = (len(filtered_df) - 1) // page_size + 1 if len(filtered_df) > 0 else 1

                if total_pages > 1:
                    current_page = st.selectbox(
                        f"📄 Page:",
                        options=range(1, total_pages + 1),
                        index=0,
                        format_func=lambda x: f"Page {x} of {total_pages}",
                        help=f"Navigate through {total_pages} pages of results"
                    )
                else:
                    current_page = 1
                    st.info(f"📄 Single page ({len(filtered_df)} records)")

            with pagination_col3:
                # Show pagination info
                start_idx = (current_page - 1) * page_size
                end_idx = min(start_idx + page_size, len(filtered_df))

                st.info(f"📊 **Showing records {start_idx + 1:,}-{end_idx:,} of {len(filtered_df):,}**")

            # Step 6: Prepare and display the enhanced table
            display_df = self._prepare_enhanced_table_for_display(filtered_df, selected_columns)
            page_df = display_df.iloc[start_idx:end_idx]

            # Configure enhanced dataframe display
            column_config = self._get_enhanced_column_config(selected_columns)

            st.dataframe(
                page_df,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                height=min(600, len(page_df) * 35 + 50)  # Dynamic height
            )

            # Step 7: Enhanced export functionality
            if len(filtered_df) > 0:
                st.markdown("---")
                st.markdown("#### 📥 Export Options")

                export_col1, export_col2, export_col3, export_col4 = st.columns(4)

                with export_col1:
                    # CSV export with selected columns
                    export_df = filtered_df[selected_columns] if selected_columns else filtered_df
                    csv_data = export_df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv_data,
                        file_name=f"federal_spending_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help=f"Download {len(filtered_df):,} filtered records as CSV"
                    )

                with export_col2:
                    # JSON export
                    json_data = export_df.to_json(orient='records', indent=2)
                    st.download_button(
                        label="🔗 Download JSON",
                        data=json_data,
                        file_name=f"federal_spending_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        help=f"Download {len(filtered_df):,} filtered records as JSON"
                    )

                with export_col3:
                    # Excel export (if possible)
                    try:
                        from io import BytesIO
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            export_df.to_excel(writer, sheet_name='Federal_Spending', index=False)

                        st.download_button(
                            label="📈 Download Excel",
                            data=excel_buffer.getvalue(),
                            file_name=f"federal_spending_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Download as Excel file (if supported)"
                        )
                    except ImportError:
                        st.info("📈 Excel export not available (install openpyxl)")

                with export_col4:
                    # Summary export
                    summary_data = self._create_export_summary(filtered_df)
                    st.download_button(
                        label="📋 Download Summary",
                        data=summary_data,
                        file_name=f"federal_spending_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        help="Download summary statistics as text file"
                    )

            print(f"✅ Enhanced data table displayed successfully: {len(page_df)} records on page {current_page}")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error creating enhanced data table: {error_msg}")
            st.error(f"❌ **Error creating enhanced data table**: {error_msg}")

            # Show basic fallback
            try:
                st.info(f"📊 Dataset contains {len(self.df):,} records, but enhanced table display failed")
            except:
                st.info("📊 Unable to display enhanced data table due to issues")

            return False
    def _prepare_enhanced_table_for_display(self, df, selected_columns):
        """Prepare DataFrame for enhanced table display with selected columns"""
        try:
            if not selected_columns:
                return df.head(0)

            # Select only the requested columns that exist
            available_columns = [col for col in selected_columns if col in df.columns]
            if not available_columns:
                return df.head(0)

            display_df = df[available_columns].copy()

            # Clean up data for better display
            for col in display_df.columns:
                if display_df[col].dtype == 'object':
                    # Clean text columns
                    display_df[col] = display_df[col].astype(str)
                    display_df[col] = display_df[col].replace(['nan', 'None', ''], 'N/A')

                    # Truncate very long text
                    if col in ['description']:
                        display_df[col] = display_df[col].apply(lambda x:
                                                                x[:150] + "..." if len(str(x)) > 150 else str(x)
                                                                )
                    else:
                        display_df[col] = display_df[col].apply(lambda x:
                                                                x[:50] + "..." if len(str(x)) > 50 else str(x)
                                                                )

            return display_df

        except Exception as e:
            print(f"❌ Error preparing enhanced table: {str(e)}")
            return df

    def _get_enhanced_column_config(self, selected_columns):
        """Get enhanced column configuration for better display"""
        config = {}

       # In your _get_enhanced_column_config() method, update this:

        column_configs = {
            'award_amount': st.column_config.NumberColumn(
                "Award Amount",
                format="$%.2f",
                help="Total award amount"
            ),
            'recipient_name': st.column_config.TextColumn(
                "Recipient Name",
                help="Organization receiving the award",
                width="medium"
            ),
            'awarding_agency': st.column_config.TextColumn(
                "Awarding Agency",
                help="Government agency providing the award",
                width="medium"
            ),
            'contract_award_type': st.column_config.TextColumn(  # Changed from 'award_type'
                "Award Type",
                help="Type of contract or award",
                width="small"
            ),
            'description': st.column_config.TextColumn(
                "Description",
                help="Award description",
                width="large"
            ),
            'award_id': st.column_config.TextColumn(
                "Award ID",
                help="Unique award identifier",
                width="small"
            )
        }

        for col in selected_columns:
            if col in column_configs:
                config[col] = column_configs[col]

        return config

    def _create_export_summary(self, df):
        """Create a text summary for export"""
        try:
            summary = f"""Federal Spending Data Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 50}

OVERVIEW:
- Total Records: {len(df):,}
- Total Award Amount: ${df['award_amount'].sum():,.2f}
- Average Award: ${df['award_amount'].mean():,.2f}
- Largest Award: ${df['award_amount'].max():,.2f}
- Smallest Award: ${df['award_amount'].min():,.2f}

TOP RECIPIENTS:
"""

            top_recipients = df.groupby('recipient_name')['award_amount'].sum().sort_values(ascending=False).head(10)
            for i, (recipient, amount) in enumerate(top_recipients.items(), 1):
                summary += f"{i:2d}. {recipient}: ${amount:,.2f}\n"

            summary += f"""
TOP AGENCIES:
"""

            top_agencies = df.groupby('awarding_agency')['award_amount'].sum().sort_values(ascending=False).head(10)
            for i, (agency, amount) in enumerate(top_agencies.items(), 1):
                summary += f"{i:2d}. {agency}: ${amount:,.2f}\n"

            return summary

        except Exception as e:
            return f"Error creating summary: {str(e)}"

    def run(self):
        """Main method to run the dashboard with organized layout"""
        # Set up the page with custom styling
        self.setup_page_config()

        # Create the styled header
        self.create_styled_header()

        # Load data if not already loaded
        if not self.data_loaded:
            self.load_data()

        # Create enhanced sidebar
        self.create_enhanced_sidebar()
        # NEW: Create filter UI (saves to session state)
        print("🎛️ Creating persistent filter system...")
        self.create_dynamic_filter_system()
        
        # NEW: Apply filters with persistence and conflict detection
        filtered_data = self.apply_filters_with_persistence()
        
            
         # Use filtered data for all subsequent operations
        if filtered_data is not None and not filtered_data.empty:
            original_df = self.df
            self.df = filtered_data
            print(f"✅ Using persistently filtered data: {len(filtered_data):,} records")
    
        # Show debug info if enabled
        self.display_debug_info()

        # Enhanced data status check with better user guidance
        if not self.add_loading_states_and_feedback():
            # Show enhanced getting started guide
            st.markdown("## 🚀 Getting Started with Federal Spending Analytics")
            
            # Progress indicator
            progress_col1, progress_col2 = st.columns([3, 1])
            
            with progress_col1:
                st.markdown("""
                ### 📋 Step-by-Step Setup Guide
                
                **Step 1: Collect Federal Spending Data** ⏱️ *~2 minutes*
                ```bash
                python data_collector.py
                ```
                This fetches real data from USAspending.gov and saves it locally.

                **Step 2: Refresh This Dashboard** ⏱️ *~5 seconds*
                Click the "🔄 Refresh Data" button in the sidebar to load the collected data.

                **Step 3: Explore Visualizations** ⏱️ *Unlimited!*
                Navigate through interactive charts, maps, and data tables.
                """)
            
            with progress_col2:
                st.info("""
                **⚡ System Requirements**
                
                ✅ Python 3.7+
                ✅ Internet connection
                ✅ 50MB free space
                ✅ Modern web browser
                
                **📁 Files Created**
                
                • CSV data files
                • JSON backups  
                • Operation logs
                """)
            
            # Add encouraging call-to-action
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; padding: 2rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 1rem; color: white; margin: 1rem 0;'>
                <h3>🚀 Ready to Explore Federal Spending?</h3>
                <p>Run the data collector and refresh this page to see amazing visualizations of real government spending data!</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add footer even when no data
            self.add_page_footer()
            return

        # Validate data structure
        if not self.validate_data_structure():
            return

        # =====================================
        # MAIN DASHBOARD CONTENT STARTS HERE
        # =====================================
        
        # 1. DASHBOARD OVERVIEW SECTION
        st.markdown("## 📊 Dashboard Overview")
        st.markdown("*Key metrics and summary of federal spending data*")
        
        # Add refresh button in a prominent location
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if st.button("🔄 Refresh Data", help="Reload data from files", key="main_refresh"):
                with st.spinner("Refreshing data..."):
                    self.load_data()
                st.rerun()
        
        # Show our key metrics
        self.show_metrics()

        

        # =====================================
        # 2. INTERACTIVE VISUALIZATIONS SECTION
        # =====================================
        st.markdown("---")
        st.markdown("## 📈 Interactive Visualizations")
        st.markdown("*Explore federal spending through different perspectives*")

        # Create tabs for different chart types (organized and user-friendly)
        chart_tab1, chart_tab2, chart_tab3, chart_tab4, chart_tab5, chart_tab6 = st.tabs([
            "🏆 Top Recipients",
            "🏛️ Agencies", 
            "📊 Award Types",
            "🌊 Agency Flow",
            "🗺️ Geographic Map",
            "⏰ Time Series"
        ])

        with chart_tab1:
            st.markdown("### Top Recipients by Total Award Amount")
            st.markdown("*Organizations that received the most federal spending*")
            
            # Add controls for the chart
            col1, col2 = st.columns([3, 1])
            with col2:
                top_n = st.selectbox(
                    "Number to show:",
                    options=[5, 10, 15, 20],
                    index=1,  # Default to 10
                    help="Select how many top recipients to display",
                    key="recipients_top_n"
                )
            
            # Show the chart
            self.show_top_recipients(top_n=top_n)

        with chart_tab2:
            st.markdown("### Federal Spending by Government Agency")
            st.markdown("*Distribution of spending across different government agencies*")
            
            # Add controls for the chart
            col1, col2 = st.columns([3, 1])
            with col2:
                agency_top_n = st.selectbox(
                    "Top agencies to show:",
                    options=[5, 6, 7, 8, 10],
                    index=3,  # Default to 8
                    help="Number of top agencies to show individually (others grouped)",
                    key="agency_top_n"
                )
            
            # Show the pie chart
            self.show_agency_pie(top_n=agency_top_n)

        with chart_tab3:
            st.markdown("### Federal Spending by Award Type")
            st.markdown("*Distribution across contracts, grants, loans, and other award types*")
            
            # Show the award types chart
            self.show_award_types()

        with chart_tab4:
            st.markdown("### Federal Funding Flow: Agencies → Sub-Agencies")
            st.markdown("*Interactive flow diagram showing funding relationships*")
            
            # Add controls for the diagram
            col1, col2 = st.columns([3, 1])
            with col2:
                min_flow_options = {
                    "All flows ($0+)": 0,
                    "Small flows ($100K+)": 100000,
                    "Medium flows ($1M+)": 1000000,
                    "Large flows ($10M+)": 10000000,
                    "Major flows ($100M+)": 100000000
                }
                
                selected_flow = st.selectbox(
                    "Minimum flow amount:",
                    options=list(min_flow_options.keys()),
                    index=2,  # Default to $1M+
                    help="Filter to show only flows above this amount",
                    key="sankey_flow"
                )
                
                min_flow_amount = min_flow_options[selected_flow]
            
            # Show the Sankey diagram
            self.show_agency_sankey(min_flow_amount=min_flow_amount)

        with chart_tab5:
            st.markdown("### Federal Spending by State")
            st.markdown("*Geographic distribution of federal spending across states*")
            
            # Add controls for the map
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown("**Customize your map visualization:**")
            
            with col2:
                map_type_options = {
                    "Choropleth Map": "choropleth", 
                    "Bubble Map": "scatter"
                }
                
                selected_map_type = st.selectbox(
                    "Map style:",
                    options=list(map_type_options.keys()),
                    index=0,
                    help="Choose visualization style",
                    key="map_type"
                )
                
                map_type = map_type_options[selected_map_type]
            
            with col3:
                color_scheme_options = {
                    "Professional Blue": "blue",
                    "Money Green": "green",
                    "Government Orange": "orange", 
                    "Executive Purple": "purple"
                }
                
                selected_color_scheme = st.selectbox(
                    "Color scheme:",
                    options=list(color_scheme_options.keys()),
                    index=0,
                    help="Choose color palette",
                    key="color_scheme"
                )
                
                color_scheme = color_scheme_options[selected_color_scheme]
            
            # Show the enhanced map
            self.show_enhanced_state_spending_map(map_type=map_type, color_scheme=color_scheme)


        with chart_tab6:
            st.markdown("### Time Series Analysis")
            st.markdown("*Analyze spending patterns and trends over time*")
            
            # Show the time series analysis directly (no subtabs)
            self.show_time_series_analysis()
        # =====================================
        # 3. DATA EXPLORER SECTION  
        # =====================================
        st.markdown("---")
        st.markdown("## 🔍 Data Explorer")
        st.markdown("*Search, filter, and explore individual spending records*")
        
        # Show the data table
        self.show_data_table()
        # Call the existing footer method
        self.add_page_footer()
def main():
    """Main function to run the Federal Spending Dashboard"""
    dashboard = FederalSpendingDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
