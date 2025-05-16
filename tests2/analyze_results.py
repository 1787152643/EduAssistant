# tests2/analyze_results.py
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

def analyze_test_results(results_dir="test_results"):
    """
    Analyze Locust test results and generate a report
    """
    print(f"Analyzing test results in {results_dir}...")
    
    # Find all stats files
    stats_files = glob.glob(f"{results_dir}/*_stats.csv")
    
    if not stats_files:
        print("No test results found.")
        return
    
    # Process each stats file
    all_results = []
    
    for stats_file in stats_files:
        component = os.path.basename(stats_file).replace("_stats.csv", "")
        
        try:
            # Read stats file
            stats_df = pd.read_csv(stats_file)
            
            # Skip empty files
            if stats_df.empty:
                continue
            
            # Calculate summary metrics for each request type
            for _, row in stats_df.iterrows():
                result = {
                    "component": component,
                    "request": row.get("Name", "Unknown"),
                    "requests": row.get("Request Count", 0),
                    "failures": row.get("Failure Count", 0),
                    "median_response_time": row.get("Median Response Time", 0),
                    "avg_response_time": row.get("Average Response Time", 0),
                    "min_response_time": row.get("Min Response Time", 0),
                    "max_response_time": row.get("Max Response Time", 0),
                    "p95_response_time": row.get("95%ile Response Time", row.get("95%", 0)),
                    "requests_per_sec": row.get("Requests/s", 0)
                }
                
                # Calculate success rate
                if result["requests"] > 0:
                    result["success_rate"] = 100 * (1 - result["failures"] / result["requests"])
                else:
                    result["success_rate"] = 0
                    
                all_results.append(result)
                
        except Exception as e:
            print(f"Error processing {stats_file}: {e}")
    
    if not all_results:
        print("No valid data found in results.")
        return
    
    # Convert to DataFrame
    results_df = pd.DataFrame(all_results)
    
    # Save complete results
    results_df.to_csv(os.path.join(results_dir, "analysis_results.csv"), index=False)
    
    # Generate visualizations and report
    generate_report(results_df, results_dir)
    
def generate_report(df, output_dir):
    """Generate report with visualizations"""
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create report directory
    report_dir = os.path.join(output_dir, "report")
    os.makedirs(report_dir, exist_ok=True)
    
    # 1. Response Time by Component
    plt.figure(figsize=(12, 8))
    component_avg = df.groupby("component")["avg_response_time"].mean().reset_index()
    component_p95 = df.groupby("component")["p95_response_time"].mean().reset_index()
    
    plt.barh(component_avg["component"], component_avg["avg_response_time"], 
             color="blue", alpha=0.6, label="Average")
    plt.barh(component_p95["component"], component_p95["p95_response_time"], 
             color="red", alpha=0.6, label="95th Percentile")
    
    plt.title("Response Time by Component")
    plt.xlabel("Response Time (ms)")
    plt.ylabel("Component")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "response_time_by_component.png"))
    
    # 2. Success Rate by Component
    plt.figure(figsize=(12, 8))
    success_rate = df.groupby("component")["success_rate"].mean().reset_index()
    
    plt.bar(success_rate["component"], success_rate["success_rate"], color="green")
    plt.title("Success Rate by Component")
    plt.xlabel("Component")
    plt.ylabel("Success Rate (%)")
    plt.ylim([min(90, success_rate["success_rate"].min() - 5), 100.5])
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "success_rate_by_component.png"))
    
    # 3. Throughput Analysis
    plt.figure(figsize=(12, 8))
    throughput = df.groupby("component")["requests_per_sec"].sum().reset_index()
    
    plt.bar(throughput["component"], throughput["requests_per_sec"], color="purple")
    plt.title("Total Throughput by Component (Requests per Second)")
    plt.xlabel("Component")
    plt.ylabel("Requests/sec")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "throughput_by_component.png"))
    
    # Generate HTML report
    generate_html_report(df, report_dir, report_time)
    
    print(f"Report generated in {report_dir}")

def generate_html_report(df, report_dir, report_time):
    """Generate HTML report with metrics and visualizations"""
    # Calculate summary statistics
    total_requests = df["requests"].sum()
    avg_success_rate = df["success_rate"].mean()
    avg_response_time = df["avg_response_time"].mean()
    
    # Component summaries
    component_summary = df.groupby("component").agg({
        "requests": "sum",
        "failures": "sum",
        "avg_response_time": "mean",
        "p95_response_time": "mean",
        "requests_per_sec": "sum"
    }).reset_index()
    
    component_summary["success_rate"] = 100 * (1 - component_summary["failures"] / component_summary["requests"])
    
    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EduAssistant Performance Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .success {{ color: green; }}
            .warning {{ color: orange; }}
            .danger {{ color: red; }}
            .summary {{ background-color: #eef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            img {{ max-width: 100%; height: auto; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>EduAssistant Performance Test Report</h1>
        <p>Report generated at: {report_time}</p>
        
        <div class="summary">
            <h2>Test Summary</h2>
            <p><strong>Total Requests:</strong> {total_requests:,}</p>
            <p><strong>Overall Success Rate:</strong> 
                <span class="{'success' if avg_success_rate >= 99 else 'warning' if avg_success_rate >= 95 else 'danger'}">{avg_success_rate:.2f}%</span>
            </p>
            <p><strong>Average Response Time:</strong> {avg_response_time:.2f} ms</p>
        </div>
        
        <h2>Component Performance</h2>
        <img src="response_time_by_component.png" alt="Response Time by Component">
        <img src="success_rate_by_component.png" alt="Success Rate by Component">
        <img src="throughput_by_component.png" alt="Throughput by Component">
        
        <h2>Component Summary</h2>
        <table>
            <tr>
                <th>Component</th>
                <th>Requests</th>
                <th>Success Rate</th>
                <th>Avg Response Time (ms)</th>
                <th>P95 Response Time (ms)</th>
                <th>Throughput (req/s)</th>
            </tr>
    """
    
    # Add component summary rows
    for _, row in component_summary.iterrows():
        success_class = 'success' if row['success_rate'] >= 99 else 'warning' if row['success_rate'] >= 95 else 'danger'
        html += f"""
            <tr>
                <td>{row['component']}</td>
                <td>{row['requests']:,}</td>
                <td class="{success_class}">{row['success_rate']:.2f}%</td>
                <td>{row['avg_response_time']:.2f}</td>
                <td>{row['p95_response_time']:.2f}</td>
                <td>{row['requests_per_sec']:.2f}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>System Recommendations</h2>
        <ul>
            <li>For components with high response times, consider optimization or caching strategies</li>
            <li>For components with low success rates, investigate error causes and improve error handling</li>
            <li>Monitor database connection pool during high load periods</li>
        </ul>
    </body>
    </html>
    """
    
    # Write HTML report
    with open(os.path.join(report_dir, "report.html"), "w") as f:
        f.write(html)

if __name__ == "__main__":
    analyze_test_results()