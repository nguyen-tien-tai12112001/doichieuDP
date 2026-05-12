"""
Interest rate fetcher module for market benchmark data.
"""
import requests
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta


def fetch_vietnam_interest_rates() -> Optional[Dict[str, float]]:
    """
    Fetch current interest rates for Vietnam from public API.
    
    Returns:
        Dict with term -> rate mappings, or None if failed
    """
    try:
        # Note: This is a placeholder. Replace with actual API endpoint
        # Example: Vietnam Bank interest rates API or public source
        
        # For demo, using mock data. Replace with real API call:
        # response = requests.get('https://api.example.com/vietnam-interest-rates', timeout=10)
        # if response.status_code == 200:
        #     data = response.json()
        #     return {
        #         '1_month': data.get('1M', 4.5),
        #         '3_month': data.get('3M', 5.0),
        #         '6_month': data.get('6M', 5.5),
        #         '12_month': data.get('12M', 6.0),
        #         '24_month': data.get('24M', 6.5),
        #         '36_month': data.get('36M', 7.0),
        #     }
        
        # Mock data for demonstration (based on typical Vietnam rates as of 2024)
        return {
            '1_month': 4.2,
            '3_month': 4.8,
            '6_month': 5.3,
            '12_month': 6.1,
            '24_month': 6.8,
            '36_month': 7.2,
        }
    except Exception as e:
        print(f"Failed to fetch interest rates: {e}")
        return None


def get_market_benchmark_rates() -> Dict[str, float]:
    """
    Get market benchmark interest rates with fallback to defaults.
    
    Returns:
        Dict of term -> rate
    """
    rates = fetch_vietnam_interest_rates()
    if rates:
        return rates
    
    # Fallback defaults if API fails
    return {
        '1_month': 4.0,
        '3_month': 4.5,
        '6_month': 5.0,
        '12_month': 5.5,
        '24_month': 6.0,
        '36_month': 6.5,
    }


def compare_internal_vs_market(internal_rate: float, term: str = '12_month') -> Dict[str, any]:
    """
    Compare internal deposit rate vs market benchmark.
    
    Args:
        internal_rate: Internal rate (percentage)
        term: Term to compare (default 12 months)
        
    Returns:
        Dict with comparison data
    """
    market_rates = get_market_benchmark_rates()
    market_rate = market_rates.get(term, 5.5)
    
    difference = internal_rate - market_rate
    competitive = 'THUẬN LỢI' if difference >= 0 else 'BẤT LỢI'
    
    return {
        'internal_rate': internal_rate,
        'market_rate': market_rate,
        'difference': difference,
        'competitive': competitive,
        'term': term,
    }


def get_interest_rate_insights(internal_avg_rate: float = 5.5) -> list[str]:
    """
    Generate insights about interest rate competitiveness.
    
    Args:
        internal_avg_rate: Average internal deposit rate
        
    Returns:
        List of insight strings
    """
    comparison = compare_internal_vs_market(internal_avg_rate)
    
    insights = [
        f"Lãi suất tiết kiệm trung bình nội bộ: {comparison['internal_rate']:.2f}%",
        f"Lãi suất thị trường tham chiếu (12 tháng): {comparison['market_rate']:.2f}%",
        f"Chênh lệch: {comparison['difference']:+.2f}% ({comparison['competitive']})",
    ]
    
    if comparison['difference'] < -0.5:
        insights.append("⚠️ Lãi suất nội bộ thấp hơn thị trường, có nguy cơ mất khách hàng sang đối thủ.")
        insights.append("💡 Khuyến nghị tăng lãi suất hoặc bổ sung ưu đãi phi lãi suất để cạnh tranh.")
    elif comparison['difference'] > 0.5:
        insights.append("✅ Lãi suất nội bộ cao hơn thị trường, lợi thế cạnh tranh tốt.")
    else:
        insights.append("📊 Lãi suất nội bộ tương đương thị trường, cần theo dõi biến động.")
    
    return insights