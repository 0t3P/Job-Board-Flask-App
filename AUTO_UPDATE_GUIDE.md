# 🤖 Auto-Update Setup Guide

This guide will help you automatically update your job board daily (or on any schedule you choose).

---

## 📋 What I Created For You:

1. **`auto_update_jobs.bat`** - Manual update script (with output)
2. **`auto_update_silent.bat`** - Silent version for scheduled tasks
3. **`update_log.txt`** - Will be created to track updates

---

## 🧪 Test It First

Before scheduling, test the manual version:

1. **Double-click** `auto_update_jobs.bat`
2. Watch it:
   - Run all scrapers
   - Commit changes
   - Push to GitHub
   - Update Render automatically
3. If it works, proceed to scheduling!

---

## ⏰ Schedule Automatic Daily Updates

### Step 1: Open Task Scheduler

1. Press **Windows Key + R**
2. Type: `taskschd.msc`
3. Press **Enter**

### Step 2: Create a New Task

1. Click **"Create Basic Task"** (right sidebar)
2. **Name**: `Auto Update Job Board`
3. **Description**: `Automatically scrape jobs and update website daily`
4. Click **Next**

### Step 3: Set the Trigger (When to Run)

1. Select: **Daily**
2. Click **Next**
3. **Start date**: Today
4. **Time**: Choose when (e.g., `2:00 AM` for overnight updates)
5. **Recur every**: `1 days`
6. Click **Next**

### Step 4: Set the Action (What to Run)

1. Select: **Start a program**
2. Click **Next**
3. **Program/script**: Browse and select:
   ```
   c:\Python\desktop_python_files\other_script\mobile\jobs_flask\auto_update_silent.bat
   ```
4. **Start in (optional)**: Add the folder path:
   ```
   c:\Python\desktop_python_files\other_script\mobile\jobs_flask
   ```
5. Click **Next**

### Step 5: Finish

1. ✅ Check **"Open the Properties dialog"**
2. Click **Finish**

### Step 6: Advanced Settings

In the Properties dialog that opens:

1. **General** tab:
   - ✅ Check **"Run whether user is logged on or not"**
   - ✅ Check **"Run with highest privileges"**

2. **Conditions** tab:
   - ❌ Uncheck **"Start the task only if the computer is on AC power"**
   - (So it runs even on battery)

3. **Settings** tab:
   - ✅ Check **"Run task as soon as possible after a scheduled start is missed"**
   - ✅ Check **"If the task fails, restart every: 10 minutes"**

4. Click **OK**

---

## 📊 Check If It's Working

### Method 1: Check Log File
Open `update_log.txt` to see update history:
```
2026-02-03 02:00:00 - Starting auto-update
Running scrapers...
Committing changes...
Pushing to GitHub...
2026-02-03 02:05:32 - Update complete
```

### Method 2: Check GitHub
Visit your repo to see auto-commits:
https://github.com/jleyco/Job-Board-Flask-Apps/commits

### Method 3: Check Render
Check Render dashboard for automatic deployments

---

## ⚙️ Customize Schedule

Want different timing? Edit the task:

| Schedule | Settings |
|----------|----------|
| **Every 6 hours** | Trigger: Daily, Repeat every 6 hours |
| **Twice daily** | Create 2 tasks (e.g., 6 AM and 6 PM) |
| **Weekdays only** | Trigger: Weekly, select Mon-Fri |
| **Every hour** | Trigger: Daily, Repeat every 1 hour |

To edit:
1. Open Task Scheduler
2. Find your task in **Task Scheduler Library**
3. Right-click → **Properties**
4. Modify settings

---

## 🐛 Troubleshooting

### Task doesn't run?
- Check `update_log.txt` for errors
- Make sure your PC is on at the scheduled time
- Verify paths are correct in Task Scheduler

### Git asks for credentials?
- GitHub Desktop handles this automatically
- Or set up credential caching:
  ```bash
  git config --global credential.helper wincred
  ```

### Scrapers fail?
- Check internet connection
- Some websites may block frequent scraping
- Consider longer intervals (daily instead of hourly)

---

## 🎯 Best Practices

1. **Run overnight** (2-3 AM) when websites have less traffic
2. **Check logs weekly** to catch any issues
3. **Don't over-scrape** - Daily is usually enough
4. **Keep PC on** during scheduled times (or use Wake-on-LAN)

---

## 🔄 Alternative: Cloud Automation (Advanced)

If you don't want to keep your PC on:

### Option 1: GitHub Actions (Free)
- Runs in the cloud
- Free for public repos
- Some websites may block cloud IPs

### Option 2: Render Cron Jobs
- Runs on Render servers
- Requires paid plan ($7/month)

Want me to help set up cloud automation instead?

---

## 📝 Summary

✅ **What happens automatically:**
1. Task Scheduler runs `auto_update_silent.bat` daily
2. Scrapers collect fresh jobs
3. Changes committed to Git
4. Pushed to GitHub
5. Render auto-deploys updated site

**Your job board stays fresh with zero manual work!** 🎉

---

**Questions?** Check the log file or ask for help!
