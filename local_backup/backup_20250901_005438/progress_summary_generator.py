#!/usr/bin/env python3
"""
Generate Progress Summary from Chat Files
This script reads through chat files and automatically generates a progress summary
to transfer progress between different chat sessions.
"""

import os
import re
from datetime import datetime
from pathlib import Path

def extract_progress_from_chat(chat_content):
    """Extract progress information from a chat file."""
    progress = {
        'status': 'Unknown',
        'completed_tasks': [],
        'current_files': [],
        'next_steps': [],
        'known_issues': [],
        'key_insights': []
    }
    
    # Look for status indicators
    status_patterns = [
        r'✅\s*(.*?)(?:\n|$)',
        r'Status.*?:\s*(.*?)(?:\n|$)',
        r'COMPLETE|READY|DONE|FIXED|RESOLVED',
        r'100%\s*Complete',
        r'production-ready|ready to go'
    ]
    
    for pattern in status_patterns:
        matches = re.findall(pattern, chat_content, re.IGNORECASE)
        if matches:
            progress['status'] = matches[0] if matches[0] else 'In Progress'
            break
    
    # Look for completed tasks
    completed_patterns = [
        r'✅\s*(.*?)(?:\n|$)',
        r'Fixed.*?:\s*(.*?)(?:\n|$)',
        r'Resolved.*?:\s*(.*?)(?:\n|$)',
        r'Completed.*?:\s*(.*?)(?:\n|$)'
    ]
    
    for pattern in completed_patterns:
        matches = re.findall(pattern, chat_content, re.IGNORECASE)
        progress['completed_tasks'].extend(matches)
    
    # Look for current files
    file_patterns = [
        r'Updated.*?:\s*(.*?\.py)',
        r'Modified.*?:\s*(.*?\.py)',
        r'File.*?:\s*(.*?\.py)',
        r'`(.*?\.py)`'
    ]
    
    for pattern in file_patterns:
        matches = re.findall(pattern, chat_content, re.IGNORECASE)
        progress['current_files'].extend(matches)
    
    # Look for next steps
    next_step_patterns = [
        r'Next.*?:\s*(.*?)(?:\n|$)',
        r'Next step.*?:\s*(.*?)(?:\n|$)',
        r'TODO.*?:\s*(.*?)(?:\n|$)',
        r'Need to.*?:\s*(.*?)(?:\n|$)'
    ]
    
    for pattern in next_step_patterns:
        matches = re.findall(pattern, chat_content, re.IGNORECASE)
        progress['next_steps'].extend(matches)
    
    # Look for known issues
    issue_patterns = [
        r'❌\s*(.*?)(?:\n|$)',
        r'Issue.*?:\s*(.*?)(?:\n|$)',
        r'Problem.*?:\s*(.*?)(?:\n|$)',
        r'Error.*?:\s*(.*?)(?:\n|$)'
    ]
    
    for pattern in issue_patterns:
        matches = re.findall(pattern, chat_content, re.IGNORECASE)
        progress['known_issues'].extend(matches)
    
    # Look for key insights
    insight_patterns = [
        r'Key.*?:\s*(.*?)(?:\n|$)',
        r'Important.*?:\s*(.*?)(?:\n|$)',
        r'Critical.*?:\s*(.*?)(?:\n|$)',
        r'Remember.*?:\s*(.*?)(?:\n|$)'
    ]
    
    for pattern in insight_patterns:
        matches = re.findall(pattern, chat_content, re.IGNORECASE)
        progress['key_insights'].extend(matches)
    
    return progress

def analyze_chat_files():
    """Analyze all chat files in the current directory."""
    chat_files = []
    progress_data = []
    
    # Find all chat files
    for file in os.listdir('.'):
        if file.endswith('.md') and ('chat' in file.lower() or 'cursor' in file.lower()):
            chat_files.append(file)
    
    print(f"Found {len(chat_files)} chat files:")
    for file in chat_files:
        print(f"  - {file}")
    
    # Analyze each chat file
    for chat_file in chat_files:
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            progress = extract_progress_from_chat(content)
            progress['source_file'] = chat_file
            progress['file_size'] = len(content)
            progress_data.append(progress)
            
            print(f"\nAnalyzed {chat_file}:")
            print(f"  Status: {progress['status']}")
            print(f"  Completed tasks: {len(progress['completed_tasks'])}")
            print(f"  Current files: {len(progress['current_files'])}")
            
        except Exception as e:
            print(f"Error reading {chat_file}: {e}")
    
    return progress_data

def generate_progress_summary(progress_data):
    """Generate a comprehensive progress summary."""
    summary = f"""# PROGRESS SUMMARY - Auto-Generated

## Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
## Source: {len(progress_data)} chat files analyzed

## OVERALL STATUS
"""
    
    # Determine overall status
    statuses = [p['status'] for p in progress_data if p['status'] != 'Unknown']
    if statuses:
        overall_status = max(set(statuses), key=statuses.count)
        summary += f"- **Overall Status**: {overall_status}\n"
    else:
        summary += "- **Overall Status**: Unknown\n"
    
    summary += "\n## COMPLETED TASKS\n"
    
    # Collect all completed tasks
    all_completed = []
    for progress in progress_data:
        all_completed.extend(progress['completed_tasks'])
    
    if all_completed:
        unique_completed = list(set(all_completed))
        for task in unique_completed[:10]:  # Limit to first 10
            summary += f"- ✅ {task}\n"
        if len(unique_completed) > 10:
            summary += f"- ... and {len(unique_completed) - 10} more\n"
    else:
        summary += "- No completed tasks identified\n"
    
    summary += "\n## CURRENT FILES\n"
    
    # Collect all current files
    all_files = []
    for progress in progress_data:
        all_files.extend(progress['current_files'])
    
    if all_files:
        unique_files = list(set(all_files))
        for file in unique_files:
            summary += f"- `{file}`\n"
    else:
        summary += "- No current files identified\n"
    
    summary += "\n## NEXT STEPS\n"
    
    # Collect all next steps
    all_next_steps = []
    for progress in progress_data:
        all_next_steps.extend(progress['next_steps'])
    
    if all_next_steps:
        unique_next_steps = list(set(all_next_steps))
        for step in unique_next_steps[:5]:  # Limit to first 5
            summary += f"- {step}\n"
        if len(unique_next_steps) > 5:
            summary += f"- ... and {len(unique_next_steps) - 5} more\n"
    else:
        summary += "- No next steps identified\n"
    
    summary += "\n## KNOWN ISSUES\n"
    
    # Collect all known issues
    all_issues = []
    for progress in progress_data:
        all_issues.extend(progress['known_issues'])
    
    if all_issues:
        unique_issues = list(set(all_issues))
        for issue in unique_issues[:5]:  # Limit to first 5
            summary += f"- ❌ {issue}\n"
        if len(unique_issues) > 5:
            summary += f"- ... and {len(unique_issues) - 5} more\n"
    else:
        summary += "- No known issues identified\n"
    
    summary += "\n## KEY INSIGHTS\n"
    
    # Collect all key insights
    all_insights = []
    for progress in progress_data:
        all_insights.extend(progress['key_insights'])
    
    if all_insights:
        unique_insights = list(set(all_insights))
        for insight in unique_insights[:5]:  # Limit to first 5
            summary += f"- 💡 {insight}\n"
        if len(unique_insights) > 5:
            summary += f"- ... and {len(unique_insights) - 5} more\n"
    else:
        summary += "- No key insights identified\n"
    
    summary += f"""
## CHAT FILES ANALYZED
"""
    
    for progress in progress_data:
        summary += f"- `{progress['source_file']}` ({progress['file_size']:,} chars)\n"
    
    summary += f"""
## USAGE
This file is auto-generated. To update it:
1. Run: `python generate_progress_summary.py`
2. Review and edit the generated summary
3. Use this file to transfer progress between chat sessions

## NOTES
- This is an automated summary - manual review recommended
- Focus on the most recent chat files for current status
- Update manually with specific details not captured automatically
"""
    
    return summary

def main():
    """Main function to generate progress summary."""
    print("🔍 Analyzing chat files for progress...")
    print("=" * 50)
    
    # Analyze chat files
    progress_data = analyze_chat_files()
    
    if not progress_data:
        print("❌ No chat files found to analyze")
        return
    
    # Generate summary
    summary = generate_progress_summary(progress_data)
    
    # Write to file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"PROGRESS_SUMMARY_{timestamp}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\n✅ Progress summary generated: {output_file}")
    print(f"📊 Summary includes:")
    print(f"  - Overall status assessment")
    print(f"  - Completed tasks")
    print(f"  - Current files")
    print(f"  - Next steps")
    print(f"  - Known issues")
    print(f"  - Key insights")
    
    print(f"\n💡 Use this file to transfer progress between chat sessions!")
    print(f"🔄 Run this script again after each chat to keep it updated.")

if __name__ == "__main__":
    main()
