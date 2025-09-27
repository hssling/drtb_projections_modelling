#!/usr/bin/env python3
"""
TB-AMR Dashboard Auto-Refresh System

Automatically fetches latest WHO/ICMR data, updates forecasts,
and provides dashboard refresh status with timestamps.
"""

import sys
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import json
import hashlib
import logging
from typing import Dict, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_refresh.log'),
        logging.StreamHandler()
    ]
)

class TBAMRDataRefresher:
    """Manages automatic data extraction and dashboard refresh."""

    def __init__(self, base_dir: str = "tb_amr_project"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.plots_dir = self.base_dir / "plots"
        self.refresh_status_file = self.data_dir / "refresh_status.json"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)

    def load_refresh_status(self) -> Dict:
        """Load last refresh status from JSON file."""
        if self.refresh_status_file.exists():
            try:
                with open(self.refresh_status_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load refresh status: {e}")

        # Default status
        return {
            "last_refresh": None,
            "data_last_updated": None,
            "forecasts_last_updated": None,
            "sensitivity_last_updated": None,
            "meta_analysis_last_updated": None,
            "status": "never_run",
            "data_hashes": {},
            "error_log": []
        }

    def save_refresh_status(self, status: Dict):
        """Save current refresh status to JSON file."""
        try:
            with open(self.refresh_status_file, 'w') as f:
                json.dump(status, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save refresh status: {e}")

    def get_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA256 hash of a file."""
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            return None

    def has_data_changed(self, file_path: Path, component: str) -> bool:
        """Check if data file has changed since last refresh."""
        status = self.load_refresh_status()
        current_hash = self.get_file_hash(file_path)

        if component not in status.get('data_hashes', {}):
            return True

        previous_hash = status['data_hashes'][component]
        return current_hash != previous_hash

    def update_data_hashes(self, status: Dict):
        """Update file hashes in status."""
        key_files = {
            'tb_merged': self.data_dir / 'tb_merged.csv',
            'who_tb_india': self.data_dir / 'tb_raw' / 'who_tb_india.csv',
            'meta_analysis': self.data_dir / 'meta_analysis_tb_amr_results.json'
        }

        for component, file_path in key_files.items():
            status['data_hashes'][component] = self.get_file_hash(file_path)

    def refresh_who_data(self, force_refresh: bool = False) -> Tuple[bool, str]:
        """Refresh WHO TB surveillance data."""
        try:
            from extract_tb_data import extract_who_tb, unify_tb_data

            data_file = self.data_dir / 'tb_raw' / 'who_tb_india.csv'

            # Check if refresh needed
            if not force_refresh and data_file.exists():
                days_since_update = (datetime.now() - datetime.fromtimestamp(data_file.stat().st_mtime)).days
                if days_since_update < 7:  # Refresh weekly
                    return True, f"Data is recent ({days_since_update} days old), skipping WHO refresh"

            # Refresh WHO data
            logging.info("Refreshing WHO TB surveillance data...")
            who_data = extract_who_tb()
            merged_data = unify_tb_data()

            if who_data.empty or merged_data.empty:
                return False, "WHO data extraction failed - empty dataset"

            return True, f"Successfully refreshed WHO data ({len(who_data)} records)"

        except Exception as e:
            error_msg = f"WHO data refresh failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def refresh_icmr_data(self, force_refresh: bool = False) -> Tuple[bool, str]:
        """Refresh ICMR state-level data."""
        try:
            from icmr_connector import integrate_icmr_who_data

            merged_file = self.data_dir / 'tb_merged_icmr_who.csv'

            # Check if refresh needed
            if not force_refresh and merged_file.exists():
                days_since_update = (datetime.now() - datetime.fromtimestamp(merged_file.stat().st_mtime)).days
                if days_since_update < 30:  # Refresh monthly for ICMR data
                    return True, f"ICMR data is recent ({days_since_update} days old), skipping refresh"

            # Refresh ICMR data
            logging.info("Refreshing ICMR state-level data...")
            integrated_data = integrate_icmr_who_data()

            if integrated_data.empty:
                return False, "ICMR data integration failed - empty dataset"

            return True, f"Successfully refreshed ICMR data ({len(integrated_data)} records)"

        except Exception as e:
            error_msg = f"ICMR data refresh failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def refresh_forecasts(self, force_refresh: bool = False) -> Tuple[bool, str]:
        """Refresh forecasting models for new data."""
        try:
            from tb_forecast import TBForecastGenerator

            # Check if forecasts need update
            merged_file = self.data_dir / 'tb_merged.csv'
            if not merged_file.exists():
                return False, "No base data available for forecasting"

            if not force_refresh and self.has_data_changed(merged_file, 'tb_merged'):
                status = self.load_refresh_status()
                data_updated = status.get('data_last_updated')
                forecasts_updated = status.get('forecasts_last_updated')

                if data_updated and forecasts_updated:
                    if pd.to_datetime(forecasts_updated) >= pd.to_datetime(data_updated):
                        return True, "Forecasts are up-to-date with current data"

            # Generate forecasts for both case types
            case_types = ['new', 'retreated']
            success_count = 0

            for case_type in case_types:
                try:
                    generator = TBForecastGenerator()
                    success = generator.generate_forecasts(case_type=case_type)
                    if success:
                        success_count += 1
                        logging.info(f"Generated forecasts for {case_type} cases")
                    else:
                        logging.warning(f"Failed to generate forecasts for {case_type} cases")
                except Exception as e:
                    logging.error(f"Forecast generation error for {case_type}: {e}")

            if success_count > 0:
                return True, f"Successfully refreshed forecasts ({success_count}/{len(case_types)} case types)"
            else:
                return False, "All forecast refresh attempts failed"

        except Exception as e:
            error_msg = f"Forecast refresh failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def refresh_sensitivity_analysis(self, force_refresh: bool = False) -> Tuple[bool, str]:
        """Refresh policy sensitivity scenarios."""
        try:
            from tb_sensitivity import TBSensitivityAnalyzer

            # Check if sensitivity analysis needs update
            forecast_files = list(self.data_dir.glob("forecast_tb_India_*.csv"))
            if not forecast_files:
                return False, "No forecast data available for sensitivity analysis"

            # Perform sensitivity analysis for both case types
            case_types = ['new', 'retreated']
            success_count = 0

            for case_type in case_types:
                try:
                    analyzer = TBSensitivityAnalyzer()
                    success = analyzer.run_sensitivity_analysis(case_type=case_type)
                    if success:
                        success_count += 1
                        logging.info(f"Generated sensitivity analysis for {case_type} cases")
                except Exception as e:
                    logging.error(f"Sensitivity analysis error for {case_type}: {e}")

            if success_count > 0:
                return True, f"Successfully refreshed sensitivity analysis ({success_count}/{len(case_types)} scenarios)"
            else:
                return False, "All sensitivity analysis attempts failed"

        except Exception as e:
            error_msg = f"Sensitivity analysis refresh failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def refresh_meta_analysis(self, force_refresh: bool = False) -> Tuple[bool, str]:
        """Refresh literature meta-analysis."""
        try:
            from tb_meta_analysis import TBAMRMetaAnalyzer

            # Daily refresh for literature (check for new publications)
            if not force_refresh:
                status = self.load_refresh_status()
                meta_updated = status.get('meta_analysis_last_updated')

                if meta_updated:
                    days_since_meta = (datetime.now() - pd.to_datetime(meta_updated)).days
                    if days_since_meta < 1:  # Daily updates
                        return True, f"Meta-analysis is recent ({days_since_meta} days old)"

            # Refresh literature analysis
            analyzer = TBAMRMetaAnalyzer()
            success = analyzer.analyze_tb_amr_literature()

            if success:
                return True, "Successfully refreshed literature meta-analysis"
            else:
                return False, "Meta-analysis refresh failed"

        except Exception as e:
            error_msg = f"Meta-analysis refresh failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def run_complete_refresh(self, force_refresh: bool = False) -> Dict:
        """Run complete data refresh cycle and update status."""

        status = self.load_refresh_status()
        status['last_refresh'] = datetime.now()
        status['status'] = 'in_progress'

        refresh_steps = [
            ('WHO Data', self.refresh_who_data, 'data_last_updated'),
            ('ICMR Data', self.refresh_icmr_data, 'data_last_updated'),
            ('Forecasts', self.refresh_forecasts, 'forecasts_last_updated'),
            ('Sensitivity', self.refresh_sensitivity_analysis, 'sensitivity_last_updated'),
            ('Meta-Analysis', self.refresh_meta_analysis, 'meta_analysis_last_updated')
        ]

        results = []
        success_count = 0

        for step_name, refresh_func, timestamp_field in refresh_steps:
            logging.info(f"Starting {step_name} refresh...")

            success, message = refresh_func(force_refresh)

            if success:
                status[timestamp_field] = datetime.now()
                success_count += 1
                logging.info(f"✅ {step_name}: {message}")
            else:
                status['error_log'].append(f"{datetime.now()}: {step_name} - {message}")
                logging.warning(f"❌ {step_name}: {message}")

            results.append({
                'step': step_name,
                'success': success,
                'message': message
            })

        # Update final status
        status['status'] = 'completed' if success_count == len(refresh_steps) else 'partial'
        self.update_data_hashes(status)
        self.save_refresh_status(status)

        return {
            'overall_success': success_count > 0,
            'success_count': success_count,
            'total_steps': len(refresh_steps),
            'results': results,
            'timestamp': datetime.now(),
            'status': status
        }

    def get_refresh_display_info(self) -> Dict:
        """Get formatted information for dashboard display."""

        status = self.load_refresh_status()

        # Calculate time since last refresh
        last_refresh = status.get('last_refresh')
        if last_refresh:
            try:
                last_refresh_dt = pd.to_datetime(last_refresh)
                time_since = datetime.now() - last_refresh_dt

                if time_since < timedelta(hours=1):
                    time_display = f"{int(time_since.seconds // 60)} minutes ago"
                elif time_since < timedelta(days=1):
                    time_display = f"{int(time_since.seconds // 3600)} hours ago"
                elif time_since < timedelta(days=30):
                    time_display = f"{time_since.days} days ago"
                else:
                    time_display = f"{time_since.days // 30} months ago"

                status_indicator = "🟢 Fresh" if time_since < timedelta(days=7) else "🟡 Stale" if time_since < timedelta(days=30) else "🔴 Outdated"

            except:
                time_display = "Unknown"
                status_indicator = "⚪ Unknown"
        else:
            time_display = "Never"
            status_indicator = "⚪ Never Refreshed"

        # Get data freshness for each component
        components = []
        component_statuses = {
            'WHO/ICMR Data': status.get('data_last_updated'),
            'Forecasting Models': status.get('forecasts_last_updated'),
            'Policy Scenarios': status.get('sensitivity_last_updated'),
            'Meta-Analysis': status.get('meta_analysis_last_updated')
        }

        for component, last_update in component_statuses.items():
            if last_update:
                try:
                    update_dt = pd.to_datetime(last_update)
                    age_days = (datetime.now() - update_dt).days
                    freshness = "Fresh" if age_days < 7 else "Recent" if age_days < 30 else "Outdated"

                    if age_days < 1:
                        age_display = "Today"
                    elif age_days < 7:
                        age_display = f"{age_days} days ago"
                    else:
                        age_display = f"{age_days // 7} weeks ago"

                except:
                    freshness = "Unknown"
                    age_display = "Unknown"
            else:
                freshness = "No Data"
                age_display = "Never"

            components.append({
                'component': component,
                'last_updated': age_display,
                'freshness': freshness
            })

        return {
            'overall_status': status_indicator,
            'last_refresh': time_display,
            'components': components,
            'error_count': len(status.get('error_log', [])),
            'status_details': status.get('status', 'unknown')
        }

# Dashboard integration functions
def display_refresh_status_sidebar():
    """Display refresh status in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Data Refresh Status")

    refresher = TBAMRDataRefresher()
    refresh_info = refresher.get_refresh_display_info()

    # Overall status
    st.sidebar.metric("Data Status", refresh_info['overall_status'])

    # Last refresh
    st.sidebar.write(f"**Last Refresh:** {refresh_info['last_refresh']}")

    # Component status
    with st.sidebar.expander("📊 Component Details"):
        for comp in refresh_info['components']:
            status_icon = "✅" if comp['freshness'] == "Fresh" else "⚠️" if comp['freshness'] == "Recent" else "❌"
            st.write(f"{status_icon} **{comp['component']}**")
            st.write(f"   _{comp['last_updated']}_")

    # Error count
    if refresh_info['error_count'] > 0:
        st.sidebar.metric("Errors", refresh_info['error_count'])

def add_refresh_button(container, refresh_type: str = "quick"):
    """Add refresh button to dashboard."""

    refresher = TBAMRDataRefresher()

    if refresh_type == "quick":
        if container.button("🔄 Quick Refresh", help="Update with latest available data"):
            with st.spinner("Refreshing data..."):
                result = refresher.run_complete_refresh(force_refresh=False)

                if result['overall_success']:
                    success_rate = result['success_count'] / result['total_steps']
                    if success_rate == 1.0:
                        container.success(f"✅ Complete refresh successful! All {result['total_steps']} components updated.")
                    else:
                        container.warning(f"⚠️ Partial refresh: {result['success_count']}/{result['total_steps']} components updated.")

                    # Clear cache to force reload
                    st.cache_data.clear()
                else:
                    container.error("❌ Refresh failed. Check logs for details.")

                # Show details
                with container.expander("Refresh Details"):
                    for res in result['results']:
                        status_icon = "✅" if res['success'] else "❌"
                        st.write(f"{status_icon} **{res['step']}**: {res['message']}")

                st.rerun()

    elif refresh_type == "full":
        if container.button("🔄 Full Data Refresh", help="Force complete refresh from all sources"):
            confirm = st.warning("⚠️ This will re-download all WHO/ICMR data and regenerate all models. May take several minutes.")
            if st.button("Confirm Full Refresh"):
                with st.spinner("Performing full data refresh..."):
                    result = refresher.run_complete_refresh(force_refresh=True)

                    if result['overall_success']:
                        container.success(f"✅ Full refresh completed! All {result['total_steps']} components refreshed from source.")
                    else:
                        container.error("❌ Full refresh encountered errors.")

                    st.rerun()

if __name__ == "__main__":
    # Command line usage
    refresher = TBAMRDataRefresher()

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Auto-refresh mode
        logging.info("Starting automatic data refresh...")
        result = refresher.run_complete_refresh(force_refresh=False)

        if result['overall_success']:
            logging.info(f"Auto-refresh completed: {result['success_count']}/{result['total_steps']} components updated")
        else:
            logging.error("Auto-refresh failed")

        sys.exit(0 if result['overall_success'] else 1)

    # Interactive mode
    result = refresher.run_complete_refresh(force_refresh=False)

    print("="*50)
    print("TB-AMR DASHBOARD REFRESH RESULTS")
    print("="*50)
    print(f"Overall: {'SUCCESS' if result['overall_success'] else 'FAILED'}")
    print(f"Components: {result['success_count']}/{result['total_steps']} successful")
    print(f"Timestamp: {result['timestamp']}")
    print()

    for res in result['results']:
        status = "✅" if res['success'] else "❌"
        print(f"{status} {res['step']}: {res['message']}")

    print()
    print("Refresh status saved to:", refresher.refresh_status_file)
