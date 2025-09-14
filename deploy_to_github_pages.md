# Deploy Cover Letter Editor to GitHub Pages

## Steps to Deploy:

1. **Push to GitHub:**
   ```bash
   git add cover_letter_editor.py
   git commit -m "Add cover letter editor"
   git push origin main
   ```

2. **Enable GitHub Pages:**
   - Go to your repo settings
   - Scroll to "Pages" section
   - Select "Deploy from a branch"
   - Choose "main" branch
   - Select "/docs" folder

3. **Your team will access it at:**
   ```
   https://your-username.github.io/quoter_sync/
   ```

## Alternative: Use GitHub Codespaces
- Go to your GitHub repo
- Click "Code" → "Codespaces" → "Create codespace"
- Run: `python cover_letter_editor.py`
- Share the codespace URL with your team
