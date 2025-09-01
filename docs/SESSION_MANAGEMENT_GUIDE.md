# Session Management Guide

## 🎯 **Overview**

This guide explains how to use the automated session management system for the Quoter-Pipedrive integration project. The system consists of three main components:

1. **Session Manager** (`session_manager.py`) - Main automation script
2. **Cross-System Sync** (`cross_system_sync.py`) - Sync between computers
3. **Usage Guide** (this file) - How to use the system

## 🚀 **Quick Start**

### **End of Session (Laptop/Desktop):**
```bash
# Run the complete session workflow
python3 session_manager.py

# Or run specific actions
python3 session_manager.py --action summary    # Generate summary only
python3 session_manager.py --action sync      # Sync to GitHub only
python3 session_manager.py --action all       # Complete workflow (default)
```

### **Start of Session (Other Computer):**
```bash
# Pull latest changes from GitHub
python3 cross_system_sync.py
```

## 📋 **Detailed Usage**

### **1. Session Manager (`session_manager.py`)**

#### **What It Does:**
- ✅ **Generates session summary** with auto-populated sections
- ✅ **Commits all changes** to git
- ✅ **Pushes to GitHub** automatically
- ✅ **Creates timestamped files** for easy tracking

#### **Usage Options:**
```bash
# Complete workflow (recommended for end of session)
python3 session_manager.py --action all

# Generate summary only
python3 session_manager.py --action summary

# Sync to GitHub only
python3 session_manager.py --action sync

# Pull from GitHub only
python3 session_manager.py --action pull
```

#### **Output Files:**
- `SESSION_SUMMARY_YYYYMMDD_HHMM.md` - Timestamped session summary
- Git commit with session timestamp
- All changes pushed to GitHub

### **2. Cross-System Sync (`cross_system_sync.py`)**

#### **What It Does:**
- ✅ **Checks for local changes** that might conflict
- ✅ **Stashes changes** if needed (with your permission)
- ✅ **Pulls latest changes** from GitHub
- ✅ **Restores stashed changes** if any
- ✅ **Shows what's new** from other systems

#### **Usage:**
```bash
python3 cross_system_sync.py
```

#### **Safety Features:**
- Asks before stashing local changes
- Shows conflicts before proceeding
- Restores stashed changes after sync

## 🔄 **Workflow Examples**

### **End of Session (Laptop):**
```bash
# 1. Finish your work
# 2. Run session manager
python3 session_manager.py

# 3. Review the generated summary
# 4. Edit summary to add key accomplishments, issues, next steps
# 5. All changes are automatically committed and pushed
```

### **Start of Session (Desktop):**
```bash
# 1. Navigate to project directory
cd /path/to/quoter_sync

# 2. Pull latest changes
python3 cross_system_sync.py

# 3. Review recent session summaries
ls SESSION_SUMMARY_*.md

# 4. Start working with latest code
```

## 📁 **File Structure**

```
quoter_sync/
├── session_manager.py           # Main automation script
├── cross_system_sync.py         # Cross-system sync script
├── SESSION_MANAGEMENT_GUIDE.md # This guide
├── SESSION_SUMMARY_*.md        # Generated session summaries
├── .git/                       # Git repository
└── ... (other project files)
```

## ⚠️ **Important Notes**

### **Before Running Session Manager:**
1. **Save all your work** in your editor
2. **Close any files** you're editing
3. **Ensure you're in the project directory**

### **After Running Session Manager:**
1. **Review the generated summary**
2. **Edit the summary** to add:
   - Key accomplishments
   - Technical updates
   - Issues encountered
   - Next steps
   - Insights and patterns
3. **Commit the updated summary** if you made changes

### **Cross-System Sync Safety:**
1. **Always check for conflicts** before pulling
2. **Stash local changes** if you're unsure
3. **Review what's new** before proceeding

## 🎯 **Best Practices**

### **End of Each Session:**
1. **Run session manager** before closing
2. **Review and edit** the generated summary
3. **Ensure all changes** are committed and pushed

### **Start of Each Session:**
1. **Run cross-system sync** to get latest changes
2. **Review recent summaries** to understand context
3. **Check for any conflicts** or issues

### **Between Sessions:**
1. **Keep GitHub updated** with your latest work
2. **Use descriptive commit messages** (auto-generated)
3. **Review session summaries** for continuity

## 🚨 **Troubleshooting**

### **Session Manager Issues:**
```bash
# Check git status
git status

# Check if you're in the right directory
pwd

# Check if git is configured
git config --list
```

### **Cross-System Sync Issues:**
```bash
# Check git remote
git remote -v

# Check branch status
git branch -vv

# Force pull if needed (use with caution)
git fetch origin
git reset --hard origin/main
```

### **Common Problems:**
1. **Not in project directory** - Navigate to quoter_sync folder
2. **Git not configured** - Set up user.name and user.email
3. **No internet connection** - Check network before syncing
4. **Merge conflicts** - Resolve conflicts before proceeding

## 📞 **Support**

If you encounter issues:
1. **Check this guide** for common solutions
2. **Review git status** for clues
3. **Check error messages** for specific issues
4. **Use git commands** manually if needed

## 🎉 **Benefits**

### **Automation:**
- ✅ **No more manual commits** - everything is automatic
- ✅ **Consistent session summaries** - standardized format
- ✅ **Automatic GitHub sync** - never lose work again

### **Collaboration:**
- ✅ **Easy cross-system sync** - work on any computer
- ✅ **Session continuity** - pick up where you left off
- ✅ **Change tracking** - see what's new from other systems

### **Documentation:**
- ✅ **Session history** - track progress over time
- ✅ **Key insights** - capture important discoveries
- ✅ **Next steps** - maintain momentum between sessions

---

**Remember:** Always run the session manager at the end of each session to keep everything synchronized! 🚀
