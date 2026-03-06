"""
Sample data generator for testing the system.
Generate sample CSV files for T1 and T2 input testing.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import os


def generate_sample_data(output_dir='sample_data', num_branches=3, num_customers=50):
    """
    Generate sample CSV files for testing.
    
    Args:
        output_dir: Directory to save sample files
        num_branches: Number of branch CSV files to generate
        num_customers: Number of customers per branch
    """
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Branch codes
    branch_codes = ['2600', '2602', '2604'][:num_branches]
    
    # Sample customer types
    customer_types = ['Cá Nhân', 'Doanh Nghiệp']
    
    # Sample DP_TYPE_CODEs (deposit types)
    dp_types = ['010', '011', '012', '020', '021', '022', '030', '031', '032', '040', '050']
    
    # Some DP_TYPE_CODEs to exclude in validation
    exclude_types = ['101', '401']
    
    # T1 date: 2025-12-31
    t1_date = '20251231'
    # T2 date: 2026-02-28
    t2_date = '20260228'
    
    print("📊 Generating sample data...")
    
    for branch in branch_codes:
        # ============ Generate T1 data ============
        t1_data = []
        
        for i in range(num_customers):
            customer_id = f"KH{branch}{i:04d}"
            customer_name = f"Khách hàng {i+1} - {branch}"
            customer_type = np.random.choice(customer_types)
            dp_type_code = np.random.choice(dp_types + exclude_types)
            balance = np.random.uniform(100000, 50000000)
            
            t1_data.append({
                'MA_KH': customer_id,
                'TEN_KH': customer_name,
                'DP_TYPE_CODE': dp_type_code,
                'CURRENT_BALANCE': balance,
                'CUST_TYPE_NAME': customer_type
            })
        
        df_t1 = pd.DataFrame(t1_data)
        t1_filename = f"{branch}_dp01_{t1_date}.csv"
        df_t1.to_csv(os.path.join(output_dir, t1_filename), index=False)
        print(f"✅ Created: {t1_filename} ({len(df_t1)} records)")
        
        # ============ Generate T2 data ============
        # Copy T1 structure but with modifications
        t2_data = []
        
        for i, row in df_t1.iterrows():
            # 70% of customers: modify balance (increase/decrease)
            if np.random.random() < 0.7:
                # Modify balance (±30%)
                change_rate = np.random.uniform(-0.3, 0.3)
                new_balance = row['CURRENT_BALANCE'] * (1 + change_rate)
                
                # Ensure positive
                new_balance = max(0, new_balance)
            else:
                # 30% no change
                new_balance = row['CURRENT_BALANCE']
            
            t2_data.append({
                'MA_KH': row['MA_KH'],
                'TEN_KH': row['TEN_KH'],
                'DP_TYPE_CODE': row['DP_TYPE_CODE'],
                'CURRENT_BALANCE': new_balance,
                'CUST_TYPE_NAME': row['CUST_TYPE_NAME']
            })
        
        # 5% new customers
        new_customers = int(num_customers * 0.05)
        for i in range(new_customers):
            customer_id = f"KH{branch}NEW{i:03d}"
            customer_name = f"Khách mới {branch} {i+1}"
            customer_type = np.random.choice(customer_types)
            dp_type_code = np.random.choice(dp_types)
            balance = np.random.uniform(100000, 50000000)
            
            t2_data.append({
                'MA_KH': customer_id,
                'TEN_KH': customer_name,
                'DP_TYPE_CODE': dp_type_code,
                'CURRENT_BALANCE': balance,
                'CUST_TYPE_NAME': customer_type
            })
        
        df_t2 = pd.DataFrame(t2_data)
        t2_filename = f"{branch}_dp01_{t2_date}.csv"
        df_t2.to_csv(os.path.join(output_dir, t2_filename), index=False)
        print(f"✅ Created: {t2_filename} ({len(df_t2)} records)")
    
    print(f"\n✅ Sample data generated in '{output_dir}/' directory")
    print(f"\n📝 File naming: {{MACN}}_dp01_yyyymmdd.csv")
    print(f"📅 T1 Date: {t1_date}")
    print(f"📅 T2 Date: {t2_date}")
    print(f"\n💡 To test the app:")
    print(f"1. Upload files from T1 directory (2600_dp01_20251231.csv, etc.)")
    print(f"2. Upload files from T2 directory (2600_dp01_20260228.csv, etc.)")
    print(f"3. Click 'Xử Lý Đối Chiếu' button")


if __name__ == "__main__":
    generate_sample_data(output_dir='sample_data', num_branches=3, num_customers=100)
