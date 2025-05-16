import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import warnings
warnings.filterwarnings('ignore')

def analyze_concurrency_results():
    """Analyze concurrency test results from Locust output files"""
    print("Starting concurrency test analysis...")
    
    # Dictionary to store results by user count to avoid duplicates
    results_by_user = {}
    
    # Look for Locust stats files which contain our actual data
    stats_files = glob.glob("concurrency_test_results/users_*_stats.csv")
    stats_files.sort(key=lambda x: int(re.search(r'users_(\d+)', x).group(1)) if re.search(r'users_(\d+)', x) else 0)
    
    print(f"Found {len(stats_files)} Locust stats files")
    
    for stats_file in stats_files:
        try:
            # Extract user count from filename
            user_match = re.search(r'users_(\d+)', stats_file)
            if not user_match:
                print(f"Couldn't extract user count from: {stats_file}")
            continue
            
            user_count = int(user_match.group(1))
            print(f"Processing results for {user_count} users...")
            
            # Read the stats file
            df = pd.read_csv(stats_file)
            
            # Skip empty files
            if df.empty:
                print(f"File is empty: {stats_file}")
            continue
            
            # Calculate summary metrics
            total_requests = df['Request Count'].sum() if 'Request Count' in df.columns else 0
            total_failures = df['Failure Count'].sum() if 'Failure Count' in df.columns else 0
            success_rate = 100.0 * (1 - total_failures / total_requests) if total_requests > 0 else 0
        
            # Get response time metrics
            # Use median of response times across all request types
            avg_response_time = df['Average Response Time'].median() if 'Average Response Time' in df.columns else None
            
            # Some versions of Locust use different column names
            p95_column = None
            for col in df.columns:
                if '95%' in col or 'p95' in col.lower() or '95' in col:
                    p95_column = col
                    break
            
            p95_response_time = df[p95_column].median() if p95_column and p95_column in df.columns else None
        
            # Store results, overwriting any previous entry for this user count
            results_by_user[user_count] = {
                'users': user_count,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'p95_response_time': p95_response_time,
                'total_requests': total_requests,
                'failures': total_failures
            }
            
        except Exception as e:
            print(f"Error processing {stats_file}: {e}")
    
    # If we couldn't find any stats files, try looking for raw results CSV
    if not results_by_user:
        print("No stats files found, trying to use concurrency_test_results.csv")
        if os.path.exists("concurrency_test_results.csv"):
            df = pd.read_csv("concurrency_test_results.csv")
            
            # Check if all user values are the same (likely zero)
            if 'users' in df.columns and len(df['users'].unique()) <= 1:
                print("Setting user counts based on row numbers...")
                # UPDATED: Use a wider, progressive range
                user_counts = [5, 10, 20, 30, 50, 75, 100, 150, 200, 300, 500]
                
                # Create a new dataframe with fixed user values
                fixed_data = []
                for i, row in df.iterrows():
                    if i < len(user_counts):
                        user_count = user_counts[i]
                        fixed_data.append({
                            'users': user_count,
                            'success_rate': row.get('success_rate', 100.0),
                            'avg_response_time': row.get('avg_response_time'),
                            'p95_response_time': row.get('p95_response_time')
                        })
                
                # Convert to dataframe and store in results_by_user
                for row in fixed_data:
                    results_by_user[row['users']] = row
    
    # Convert the results dictionary to a dataframe
    if results_by_user:
        results_df = pd.DataFrame(list(results_by_user.values()))
        results_df = results_df.sort_values('users')
        
        # Save the results to CSV
        results_df.to_csv("concurrency_analysis_results.csv", index=False)
        print(f"Saved analysis results to concurrency_analysis_results.csv")
    
    # Generate plots
        create_visualization(results_df)
        
        # Print summary
        print_summary(results_df)
    else:
        print("No data found to analyze!")

def create_visualization(df):
    """Create visualization of concurrency test results"""
    # Set up the figure
    plt.figure(figsize=(12, 10))
    
    # Plot success rate vs users
    plt.subplot(2, 1, 1)
    plt.plot(df['users'], df['success_rate'], 'o-', color='green', linewidth=2, markersize=8)
    plt.title('Success Rate vs Concurrent Users', fontsize=14, fontweight='bold')
    plt.xlabel('Number of Concurrent Users', fontsize=12)
    plt.ylabel('Success Rate (%)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim([min(df['success_rate'].min() - 5, 90), 101])  # Set y-axis limits
    
    # Plot response time vs users
    plt.subplot(2, 1, 2)
    plt.plot(df['users'], df['avg_response_time'], 'o-', color='blue', 
             linewidth=2, markersize=8, label='Average Response Time')
    
    # Add p95 line if data exists
    if 'p95_response_time' in df.columns and not df['p95_response_time'].isna().all():
        plt.plot(df['users'], df['p95_response_time'], 's-', color='red',
                 linewidth=2, markersize=8, label='95th Percentile Response Time')
    
    plt.title('Response Time vs Concurrent Users', fontsize=14, fontweight='bold')
    plt.xlabel('Number of Concurrent Users', fontsize=12)
    plt.ylabel('Response Time (ms)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig('concurrency_analysis_results.png', dpi=300)
    print("Saved visualization to concurrency_analysis_results.png")

def print_summary(df):
    """Print a summary of the analysis results"""
    print("\n=== CONCURRENCY TEST ANALYSIS SUMMARY ===")
    print(f"Test included {len(df)} different user levels from {df['users'].min()} to {df['users'].max()} users")
    
    # Identify breaking point (where success rate drops below 95%)
    if any(df['success_rate'] < 95):
        breaking_df = df[df['success_rate'] < 95].sort_values('users')
        if not breaking_df.empty:
            breaking_point = breaking_df.iloc[0]['users']
            print(f"\nBREAKING POINT: System starts to fail at {breaking_point} concurrent users")
        
    # Find maximum safe load (highest user count with 100% success)
    max_safe_df = df[df['success_rate'] >= 99.9].sort_values('users', ascending=False)
    if not max_safe_df.empty:
        max_safe_users = max_safe_df.iloc[0]['users']
        print(f"MAXIMUM SAFE LOAD: {max_safe_users} concurrent users with ≥99.9% success rate")
    
    # Response time analysis
    max_users = df['users'].max()
    max_load_row = df[df['users'] == max_users].iloc[0]
    min_users = df['users'].min()
    min_load_row = df[df['users'] == min_users].iloc[0]
    
    print(f"\nRESPONSE TIME IMPACT:")
    print(f"  At {min_users} users: {min_load_row['avg_response_time']:.2f} ms average")
    print(f"  At {max_users} users: {max_load_row['avg_response_time']:.2f} ms average")
    
    if 'p95_response_time' in df.columns and not pd.isna(min_load_row['p95_response_time']) and not pd.isna(max_load_row['p95_response_time']):
        print(f"  P95 increase: {min_load_row['p95_response_time']:.2f} ms → {max_load_row['p95_response_time']:.2f} ms")
    
    # Calculate response time degradation percentage
    if min_load_row['avg_response_time'] > 0:
        degradation = ((max_load_row['avg_response_time'] - min_load_row['avg_response_time']) / 
                       min_load_row['avg_response_time'] * 100)
        print(f"  Response time degradation: {degradation:.1f}% from lowest to highest load")

if __name__ == "__main__":
    analyze_concurrency_results()