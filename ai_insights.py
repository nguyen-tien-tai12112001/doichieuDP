"""AI-powered insights module for deposit data analysis."""

import pandas as pd
import numpy as np
from typing import Dict


def prepare_features_for_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare numerical features for clustering analysis."""
    # Select numerical columns for clustering
    numerical_cols = ['CURRENT_BALANCE']

    # Add derived features
    features = df[numerical_cols].copy()

    # Handle missing values
    features = features.fillna(features.mean())

    return features


def perform_customer_segmentation(df: pd.DataFrame, n_clusters: int = 4) -> Dict:
    """Perform customer segmentation using simple binning instead of ML clustering."""
    features = prepare_features_for_clustering(df)

    if features.empty:
        return {"error": "Insufficient data for segmentation"}

    # Simple segmentation based on balance quantiles
    balance_col = 'CURRENT_BALANCE'
    try:
        # Create bins based on quantiles
        bins = pd.qcut(df[balance_col], q=n_clusters, duplicates='drop')
        clusters = bins.cat.codes

        # Add cluster labels to dataframe
        df_with_clusters = df.copy()
        df_with_clusters['cluster'] = clusters

        # Analyze cluster characteristics
        cluster_analysis = {}
        for cluster_id in range(len(bins.cat.categories)):
            cluster_data = df_with_clusters[df_with_clusters['cluster'] == cluster_id]
            cluster_analysis[f'Cluster_{cluster_id}'] = {
                'size': len(cluster_data),
                'avg_balance': cluster_data[balance_col].mean(),
                'min_balance': cluster_data[balance_col].min(),
                'max_balance': cluster_data[balance_col].max(),
                'balance_range': f"{cluster_data[balance_col].min():.2f} - {cluster_data[balance_col].max():.2f}",
                'customer_types': cluster_data['CUST_TYPE_NAME'].value_counts().to_dict() if 'CUST_TYPE_NAME' in cluster_data.columns else {}
            }

        return {
            'segmented_data': df_with_clusters,
            'cluster_analysis': cluster_analysis,
            'method': 'quantile_binning'
        }

    except Exception as e:
        return {"error": f"Segmentation failed: {str(e)}"}


def generate_clustering_insights(cluster_analysis: Dict) -> str:
    """Generate human-readable insights from clustering results."""
    insights = ["🤖 AI Customer Segmentation Insights:\n"]

    for cluster_name, data in cluster_analysis.items():
        insights.append(f"• {cluster_name}: {data['size']} customers")
        insights.append(f"  - Average Balance: ${data['avg_balance']:.2f}")
        insights.append(f"  - Balance Range: {data['balance_range']}")

        # Add customer type breakdown
        if data['customer_types']:
            top_type = max(data['customer_types'], key=data['customer_types'].get)
            insights.append(f"  - Primary Customer Type: {top_type}")
        insights.append("")

    return "\n".join(insights)


def predict_churn_risk(df: pd.DataFrame) -> Dict:
    """Predict customer churn risk using simple rules (no ML required)."""
    # Simplified churn prediction based on balance thresholds
    # In a real scenario, you'd use historical churn data with ML

    if df.empty:
        return {"error": "No data for churn prediction"}

    # Simple rule-based prediction
    # Low balance = higher churn risk
    balance_col = 'CURRENT_BALANCE'
    median_balance = df[balance_col].median()

    def calculate_risk_score(row):
        balance = row[balance_col]
        # Risk increases as balance decreases
        if balance < median_balance * 0.5:
            return 0.8  # High risk
        elif balance < median_balance:
            return 0.5  # Medium risk
        else:
            return 0.2  # Low risk

    df_with_risk = df.copy()
    df_with_risk['churn_risk_score'] = df.apply(calculate_risk_score, axis=1)
    df_with_risk['churn_risk_level'] = pd.cut(
        df_with_risk['churn_risk_score'],
        bins=[0, 0.4, 0.7, 1.0],
        labels=['Low', 'Medium', 'High']
    )

    # Mock accuracy for demonstration
    mock_accuracy = 0.75

    return {
        'model_accuracy': mock_accuracy,
        'churn_predictions': df_with_risk[['MA_KH', 'TEN_KH', 'churn_risk_score', 'churn_risk_level']].to_dict('records'),
        'insights': generate_churn_insights(df_with_risk)
    }


def generate_churn_insights(df_with_risk: pd.DataFrame) -> str:
    """Generate insights from churn prediction results."""
    insights = ["🔮 AI Churn Risk Analysis:\n"]

    risk_counts = df_with_risk['churn_risk_level'].value_counts()
    total_customers = len(df_with_risk)

    for level in ['Low', 'Medium', 'High']:
        count = risk_counts.get(level, 0)
        percentage = (count / total_customers) * 100
        insights.append(f"• {level} Risk: {count} customers ({percentage:.1f}%)")

    # Identify high-risk customers
    high_risk = df_with_risk[df_with_risk['churn_risk_level'] == 'High']
    if not high_risk.empty:
        insights.append(f"\n⚠️  High-risk customers to monitor:")
        for _, customer in high_risk.head(5).iterrows():
            insights.append(f"  - {customer['TEN_KH']} (ID: {customer['MA_KH']})")

    return "\n".join(insights)


def generate_ai_recommendations(df: pd.DataFrame) -> str:
    """Generate AI-powered recommendations for deposit strategies."""
    recommendations = ["💡 AI Recommendations:\n"]

    # Analyze balance distribution
    balance_stats = df['CURRENT_BALANCE'].describe()

    if balance_stats['mean'] > balance_stats['50%'] * 1.5:
        recommendations.append("• Consider targeted promotions for high-balance customers")
    else:
        recommendations.append("• Focus on customer acquisition and balance growth")

    # Customer type analysis
    type_counts = df['CUST_TYPE_NAME'].value_counts()
    if len(type_counts) > 1:
        dominant_type = type_counts.index[0]
        recommendations.append(f"• Strengthen relationships with {dominant_type} customers")

    # Balance concentration
    top_10_percent = df.nlargest(int(len(df) * 0.1), 'CURRENT_BALANCE')
    concentration_ratio = top_10_percent['CURRENT_BALANCE'].sum() / df['CURRENT_BALANCE'].sum()

    if concentration_ratio > 0.5:
        recommendations.append("• High balance concentration detected - diversify customer base")
    else:
        recommendations.append("• Balanced customer portfolio - maintain current strategies")

    return "\n".join(recommendations)