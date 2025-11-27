param(
    [Parameter(Mandatory=$true)]
    [string]$EC2Host,
    
    [Parameter(Mandatory=$true)]
    [string]$KeyFile,
    
    [int]$TrainingEpisodes = 500,
    
    [int]$TestEpisodes = 100,
    
    [string]$ExperimentName = "DeceptiCloud_Research"
)

$ErrorActionPreference = "Stop"

Write-Host "🧠 DeceptiCloud Research Experiment" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host "EC2 Host: $EC2Host" -ForegroundColor Cyan
Write-Host "Training Episodes: $TrainingEpisodes" -ForegroundColor Cyan
Write-Host "Test Episodes: $TestEpisodes" -ForegroundColor Cyan
Write-Host "Experiment: $ExperimentName" -ForegroundColor Cyan

# Create experiment directory
$experimentDir = "experiments\$ExperimentName`_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $experimentDir -Force | Out-Null
Write-Host "📁 Experiment directory: $experimentDir" -ForegroundColor Yellow

# Setup monitoring
Write-Host "`n🔧 Setting up monitoring..." -ForegroundColor Yellow
.\scripts\setup_cloudwatch.ps1

# Initialize monitoring
python -c "from src.monitoring import monitor; monitor.setup_cloudwatch_logging()"

# Run comprehensive research experiment
Write-Host "`n🚀 Starting Research Experiment..." -ForegroundColor Green

$pythonScript = @"
import sys
import os
sys.path.append(os.getcwd())

from src.research_framework import DeceptiCloudResearchFramework
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

# Initialize research framework
print("🔬 Initializing DeceptiCloud Research Framework...")
framework = DeceptiCloudResearchFramework(
    ec2_host='$EC2Host',
    ec2_user='ubuntu', 
    ec2_key='$KeyFile'
)

# Phase 1: Train Autonomous System
print("\n" + "="*50)
print("PHASE 1: TRAINING AUTONOMOUS SYSTEM")
print("="*50)

training_results = framework.train_autonomous_system(
    episodes=$TrainingEpisodes,
    save_interval=50
)

print(f"✅ Training completed!")
print(f"Final epsilon: {training_results['final_epsilon']:.3f}")
print(f"Average reward (last 50): {np.mean(training_results['episode_rewards'][-50:]):.2f}")
print(f"Average detection rate (last 50): {np.mean(training_results['attack_detection_rates'][-50:]):.2f}")

# Phase 2: Comparative Evaluation
print("\n" + "="*50)
print("PHASE 2: AUTONOMOUS vs STATIC COMPARISON")
print("="*50)

evaluation_results = framework.evaluate_autonomous_vs_static(test_episodes=$TestEpisodes)

# Phase 3: Generate Research Report
print("\n" + "="*50)
print("PHASE 3: GENERATING RESEARCH REPORT")
print("="*50)

report = framework.generate_research_report(evaluation_results)
print("📊 Research report generated!")

# Phase 4: Create Visualizations
print("\n" + "="*50)
print("PHASE 4: CREATING VISUALIZATIONS")
print("="*50)

# Training progress plot
plt.figure(figsize=(15, 10))

# Subplot 1: Episode Rewards
plt.subplot(2, 3, 1)
rewards = training_results['episode_rewards']
plt.plot(rewards, alpha=0.6, color='blue')
plt.plot(np.convolve(rewards, np.ones(50)/50, mode='valid'), color='red', linewidth=2)
plt.title('Training Progress: Episode Rewards')
plt.xlabel('Episode')
plt.ylabel('Reward')
plt.grid(True, alpha=0.3)

# Subplot 2: Detection Rates
plt.subplot(2, 3, 2)
detection_rates = training_results['attack_detection_rates']
plt.plot(detection_rates, alpha=0.6, color='green')
plt.plot(np.convolve(detection_rates, np.ones(50)/50, mode='valid'), color='darkgreen', linewidth=2)
plt.title('Attack Detection Rates')
plt.xlabel('Episode')
plt.ylabel('Detection Rate')
plt.grid(True, alpha=0.3)

# Subplot 3: Honeypot Effectiveness
plt.subplot(2, 3, 3)
effectiveness = training_results['honeypot_effectiveness']
plt.plot(effectiveness, alpha=0.6, color='orange')
plt.plot(np.convolve(effectiveness, np.ones(50)/50, mode='valid'), color='darkorange', linewidth=2)
plt.title('Honeypot Effectiveness')
plt.xlabel('Episode')
plt.ylabel('Effectiveness Score')
plt.grid(True, alpha=0.3)

# Subplot 4: System Comparison - Rewards
plt.subplot(2, 3, 4)
systems = ['Autonomous', 'Static SSH', 'Static Web']
rewards = [
    evaluation_results['autonomous']['avg_reward'],
    evaluation_results['static_ssh']['avg_reward'],
    evaluation_results['static_web']['avg_reward']
]
colors = ['green', 'blue', 'red']
bars = plt.bar(systems, rewards, color=colors, alpha=0.7)
plt.title('Average Rewards Comparison')
plt.ylabel('Average Reward')
plt.grid(True, alpha=0.3)

# Add value labels on bars
for bar, reward in zip(bars, rewards):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
             f'{reward:.1f}', ha='center', va='bottom')

# Subplot 5: Detection Rate Comparison
plt.subplot(2, 3, 5)
detection_rates = [
    evaluation_results['autonomous']['avg_detection_rate'],
    evaluation_results['static_ssh']['avg_detection_rate'],
    evaluation_results['static_web']['avg_detection_rate']
]
bars = plt.bar(systems, detection_rates, color=colors, alpha=0.7)
plt.title('Detection Rate Comparison')
plt.ylabel('Detection Rate')
plt.grid(True, alpha=0.3)

# Add value labels
for bar, rate in zip(bars, detection_rates):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
             f'{rate:.2f}', ha='center', va='bottom')

# Subplot 6: Cost Efficiency Comparison
plt.subplot(2, 3, 6)
efficiency = [
    evaluation_results['autonomous']['avg_cost_efficiency'],
    evaluation_results['static_ssh']['avg_cost_efficiency'],
    evaluation_results['static_web']['avg_cost_efficiency']
]
bars = plt.bar(systems, efficiency, color=colors, alpha=0.7)
plt.title('Cost Efficiency Comparison')
plt.ylabel('Efficiency Score')
plt.grid(True, alpha=0.3)

# Add value labels
for bar, eff in zip(bars, efficiency):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
             f'{eff:.2f}', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('$experimentDir/research_results.png', dpi=300, bbox_inches='tight')
plt.show()

# Save detailed results
results_data = {
    'experiment_name': '$ExperimentName',
    'timestamp': datetime.now().isoformat(),
    'training_episodes': $TrainingEpisodes,
    'test_episodes': $TestEpisodes,
    'training_results': training_results,
    'evaluation_results': evaluation_results,
    'ec2_host': '$EC2Host'
}

with open('$experimentDir/detailed_results.json', 'w') as f:
    json.dump(results_data, f, indent=2, default=str)

# Print summary
print("\n" + "="*60)
print("🎯 EXPERIMENT SUMMARY")
print("="*60)
print(f"Autonomous vs Static SSH:")
print(f"  Reward Improvement: {evaluation_results['comparison']['reward_improvement']['vs_ssh']:.1f}%")
print(f"  Detection Improvement: {evaluation_results['comparison']['detection_improvement']['vs_ssh']:.1f}%")
print(f"  Efficiency Improvement: {evaluation_results['comparison']['efficiency_improvement']['vs_ssh']:.1f}%")

print(f"\nAutonomous vs Static Web:")
print(f"  Reward Improvement: {evaluation_results['comparison']['reward_improvement']['vs_web']:.1f}%")
print(f"  Detection Improvement: {evaluation_results['comparison']['detection_improvement']['vs_web']:.1f}%")
print(f"  Efficiency Improvement: {evaluation_results['comparison']['efficiency_improvement']['vs_web']:.1f}%")

print(f"\n📊 Results saved to: $experimentDir")
print(f"📈 Visualizations: $experimentDir/research_results.png")
print(f"📄 Report: decepticloud_research_report_*.md")
print(f"📋 Data: $experimentDir/detailed_results.json")

print("\n✅ Research experiment completed successfully!")
"@

# Execute Python research script
$pythonScript | python

Write-Host "`n🎉 Research Experiment Completed!" -ForegroundColor Green
Write-Host "Results available in: $experimentDir" -ForegroundColor Cyan

# Open results directory
if (Test-Path $experimentDir) {
    Write-Host "📂 Opening results directory..." -ForegroundColor Yellow
    Invoke-Item $experimentDir
}

Write-Host "`n📊 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review the research report (*.md file)" -ForegroundColor White
Write-Host "2. Examine visualizations (research_results.png)" -ForegroundColor White
Write-Host "3. Analyze detailed data (detailed_results.json)" -ForegroundColor White
Write-Host "4. Monitor live system: .\scripts\monitor_system.ps1 -EC2Host $EC2Host -KeyFile $KeyFile -Action dashboard" -ForegroundColor White