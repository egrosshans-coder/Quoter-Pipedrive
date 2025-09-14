#!/usr/bin/env python3
"""
Cover Letter Editor - Friendly Front-end for Sales Reps
A web-based interface to modify cover letters for all templates
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
from template_mapping_enhanced import TEMPLATE_BUNDLES, get_template_cover_letter, get_template_appended_content

app = Flask(__name__)

# HTML Template for the editor
EDITOR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TLC Creative - Cover Letter Editor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            padding: 30px;
            display: flex;
            gap: 30px;
        }
        
        .sidebar {
            width: 300px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            height: fit-content;
            position: sticky;
            top: 20px;
        }
        
        .content-area {
            flex: 1;
        }
        
        .template-selector {
            margin-bottom: 30px;
        }
        
        .template-selector h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        
        .template-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .template-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .template-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        
        .template-card.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .template-card h3 {
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        
        .template-card p {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .editor-section {
            display: none;
        }
        
        .editor-section.active {
            display: block;
        }
        
        .editor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .editor-header h2 {
            color: #2c3e50;
            font-size: 1.8em;
        }
        
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            background: #5a6fd8;
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .btn-success {
            background: #28a745;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .form-group textarea {
            width: 100%;
            min-height: 300px;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            resize: vertical;
        }
        
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .preview-section {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .preview-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        
        .preview-content {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            min-height: 200px;
            line-height: 2.0;
        }
        
        .preview-content p {
            margin-bottom: 1em;
            line-height: 2.0;
        }
        
        .preview-content h1, .preview-content h2, .preview-content h3 {
            margin-bottom: 0.5em;
            line-height: 1.5;
        }
        
        .field-help {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 5px 5px 0;
        }
        
        .field-help h4 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        
        .field-help ul {
            list-style: none;
            padding-left: 0;
        }
        
        .field-help li {
            margin-bottom: 5px;
            font-family: 'Courier New', monospace;
            background: white;
            padding: 5px 10px;
            border-radius: 3px;
            display: inline-block;
            margin-right: 10px;
        }
        
        .status-message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .status-message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Cover Letter Editor</h1>
            <p>Customize cover letters for all TLC Creative templates</p>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <h3 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.3em;">📋 Quoter Merge Fields</h3>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #495057; margin-bottom: 10px;">🏢 Business Fields</h4>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##BusinessName##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##BusinessAddress##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##BusinessCity##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##BusinessPostalCode##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##BusinessPhone##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##BusinessEmail##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##BusinessWebsite##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##BusinessLogo##</code>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #495057; margin-bottom: 10px;">👤 Customer Fields</h4>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerOrganization##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerTitle##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerFirstName##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerLastName##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerStreetAddress##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerCity##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerPostalCode##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerCountry##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerWorkPhone##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerEmail##</code>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #495057; margin-bottom: 10px;">🚚 Shipping Fields</h4>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerShippingFirstName##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerShippingLastName##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerShippingStreetAddress##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerShippingCity##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##CustomerShippingPostalCode##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##CustomerShippingCountry##</code>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #495057; margin-bottom: 10px;">📄 Quote Fields</h4>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##QuoteNumber##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##QuoteLink##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##QuoteWebViewURL##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##QuotePDFURL##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##QuoteTotal##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##QuoteUpfrontTotal##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##QuoteRecurringTotal##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##QuoteCreatedDate##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##QuoteExpiryDate##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##QuoteFormName##</code>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #495057; margin-bottom: 10px;">👤 User Fields</h4>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##UserFirstName##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##UserLastName##</code>
                    </div>
                    <div style="background: white; padding: 8px; border-radius: 5px; margin-bottom: 8px; font-size: 0.85em;">
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">##UserEmail##</code>
                        <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px; margin-left: 5px;">##Signature##</code>
                    </div>
                </div>
                
                <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; border-radius: 0 5px 5px 0;">
                    <h4 style="color: #1976d2; margin-bottom: 10px;">🎯 Dynamic Roles</h4>
                    <div style="font-size: 0.9em; color: #1976d2;">
                        <div style="margin-bottom: 5px;"><strong>Maurice Capillaire</strong> → Sales and Logistics</div>
                        <div style="margin-bottom: 5px;"><strong>Jeff Ward</strong> → Sales and Logistics</div>
                        <div style="margin-bottom: 5px;"><strong>Eric Grosshans</strong> → Technical Director</div>
                        <div><strong>Others</strong> → Sales Team</div>
                    </div>
                </div>
            </div>
            
            <div class="content-area">
                <div class="template-selector">
                    <h2>Select Template to Edit</h2>
                    <div class="template-grid">
                        {% for template_key, template_data in templates.items() %}
                        <div class="template-card" onclick="selectTemplate('{{ template_key }}')">
                            <h3>{{ template_data.name }}</h3>
                            <p>{{ template_key }}</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            
            <div class="status-message" id="statusMessage"></div>
            
            <div class="editor-section" id="editorSection">
                <div class="editor-header">
                    <h2 id="editorTitle">Select a template above</h2>
                    <div>
                        <button class="btn btn-secondary" onclick="resetTemplate()">Reset</button>
                        <button class="btn btn-success" onclick="saveTemplate()">Save Changes</button>
                    </div>
                </div>
                
                
                <div class="form-group">
                    <label for="coverLetterEditor">Cover Letter Content:</label>
                    <textarea id="coverLetterEditor" placeholder="Enter your cover letter content here..."></textarea>
                </div>
                
                <div class="preview-section">
                    <h3>Live Preview</h3>
                    <div class="preview-content" id="previewContent">
                        <p style="color: #6c757d; font-style: italic;">Preview will appear here as you type...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentTemplate = null;
        let originalContent = null;
        
        const templates = {{ templates | tojson }};
        
        function selectTemplate(templateKey) {
            // Remove active class from all cards
            document.querySelectorAll('.template-card').forEach(card => {
                card.classList.remove('active');
            });
            
            // Add active class to selected card
            event.target.closest('.template-card').classList.add('active');
            
            currentTemplate = templateKey;
            const templateData = templates[templateKey];
            
            // Update editor title
            document.getElementById('editorTitle').textContent = `Editing: ${templateData.name}`;
            
            // Load cover letter content
            const coverLetterEditor = document.getElementById('coverLetterEditor');
            coverLetterEditor.value = templateData.cover_letter;
            originalContent = templateData.cover_letter;
            
            // Show editor section
            document.getElementById('editorSection').classList.add('active');
            
            // Update preview
            updatePreview();
        }
        
        function updatePreview() {
            const content = document.getElementById('coverLetterEditor').value;
            const preview = document.getElementById('previewContent');
            
            // Replace field codes with example values using correct ##FieldName## syntax
            let previewContent = content
                // Business Fields
                .replace(/##BusinessName##/g, 'TLC Creative')
                .replace(/##BusinessAddress##/g, '123 Main Street')
                .replace(/##BusinessCity##/g, 'Toronto')
                .replace(/##BusinessPostalCode##/g, 'M5V 3A8')
                .replace(/##BusinessPhone##/g, '(416) 555-0123')
                .replace(/##BusinessEmail##/g, 'info@tlciscreative.com')
                .replace(/##BusinessWebsite##/g, 'www.tlciscreative.com')
                
                // Customer Fields
                .replace(/##CustomerOrganization##/g, 'ZZ19-Org')
                .replace(/##CustomerTitle##/g, 'Mr.')
                .replace(/##CustomerFirstName##/g, 'John')
                .replace(/##CustomerLastName##/g, 'Smith')
                .replace(/##CustomerStreetAddress##/g, '456 Oak Avenue')
                .replace(/##CustomerCity##/g, 'Vancouver')
                .replace(/##CustomerPostalCode##/g, 'V6B 1A1')
                .replace(/##CustomerCountry##/g, 'Canada')
                .replace(/##CustomerWorkPhone##/g, '(604) 555-0456')
                .replace(/##CustomerEmail##/g, 'john.smith@example.com')
                
                // Shipping Fields
                .replace(/##CustomerShippingFirstName##/g, 'John')
                .replace(/##CustomerShippingLastName##/g, 'Smith')
                .replace(/##CustomerShippingStreetAddress##/g, '456 Oak Avenue')
                .replace(/##CustomerShippingCity##/g, 'Vancouver')
                .replace(/##CustomerShippingPostalCode##/g, 'V6B 1A1')
                .replace(/##CustomerShippingCountry##/g, 'Canada')
                
                // Quote Fields
                .replace(/##QuoteNumber##/g, 'Q-2025-001')
                .replace(/##QuoteLink##/g, 'https://tlciscreative.quoter.com/quote/webview/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
                .replace(/##QuoteWebViewURL##/g, 'https://tlciscreative.quoter.com/quote/webview/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
                .replace(/##QuotePDFURL##/g, 'https://tlciscreative.quoter.com/quote/download/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
                .replace(/##QuoteTotal##/g, '$2,500.00')
                .replace(/##QuoteUpfrontTotal##/g, '$1,000.00')
                .replace(/##QuoteRecurringTotal##/g, '$1,500.00')
                .replace(/##QuoteCreatedDate##/g, '2025/09/14')
                .replace(/##QuoteExpiryDate##/g, '2025/10/14')
                .replace(/##QuoteFormName##/g, 'Wedding Photography Package')
                
                // User Fields
                .replace(/##UserFirstName##/g, 'Maurice')
                .replace(/##UserLastName##/g, 'Capillaire')
                .replace(/##UserEmail##/g, 'maurice@tlciscreative.com')
                .replace(/##Signature##/g, 'Maurice Capillaire<br>Sales and Logistics');
            
            preview.innerHTML = previewContent;
        }
        
        function resetTemplate() {
            if (currentTemplate && originalContent) {
                document.getElementById('coverLetterEditor').value = originalContent;
                updatePreview();
                showMessage('Template reset to original content', 'success');
            }
        }
        
        function saveTemplate() {
            if (!currentTemplate) {
                showMessage('Please select a template first', 'error');
                return;
            }
            
            const newContent = document.getElementById('coverLetterEditor').value;
            
            // Send update to server
            fetch('/update_template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    template: currentTemplate,
                    cover_letter: newContent
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    originalContent = newContent;
                    showMessage('Cover letter updated successfully!', 'success');
                } else {
                    showMessage('Error updating template: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('Error saving changes: ' + error, 'error');
            });
        }
        
        function showMessage(message, type) {
            const statusMessage = document.getElementById('statusMessage');
            statusMessage.textContent = message;
            statusMessage.className = `status-message ${type}`;
            statusMessage.style.display = 'block';
            
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 3000);
        }
        
        // Update preview as user types
        document.getElementById('coverLetterEditor').addEventListener('input', updatePreview);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main editor page"""
    return render_template_string(EDITOR_TEMPLATE, templates=TEMPLATE_BUNDLES)

@app.route('/update_template', methods=['POST'])
def update_template():
    """Update a template's cover letter"""
    try:
        data = request.get_json()
        template_key = data.get('template')
        new_cover_letter = data.get('cover_letter')
        
        if not template_key or not new_cover_letter:
            return jsonify({'success': False, 'error': 'Missing template or cover letter data'})
        
        if template_key not in TEMPLATE_BUNDLES:
            return jsonify({'success': False, 'error': 'Template not found'})
        
        # Update the template
        TEMPLATE_BUNDLES[template_key]['cover_letter'] = new_cover_letter
        
        return jsonify({'success': True, 'message': 'Template updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_template/<template_key>')
def get_template(template_key):
    """Get a specific template's data"""
    if template_key in TEMPLATE_BUNDLES:
        return jsonify(TEMPLATE_BUNDLES[template_key])
    else:
        return jsonify({'error': 'Template not found'}), 404

@app.route('/preview/<template_key>')
def preview_template(template_key):
    """Preview a template with sample data"""
    if template_key not in TEMPLATE_BUNDLES:
        return "Template not found", 404
    
    cover_letter = TEMPLATE_BUNDLES[template_key]['cover_letter']
    
    # Replace field codes with sample data using correct ##FieldName## syntax
    preview = cover_letter
    # Business Fields
    preview = preview.replace('##BusinessName##', 'TLC Creative')
    preview = preview.replace('##BusinessAddress##', '123 Main Street')
    preview = preview.replace('##BusinessCity##', 'Toronto')
    preview = preview.replace('##BusinessPostalCode##', 'M5V 3A8')
    preview = preview.replace('##BusinessPhone##', '(416) 555-0123')
    preview = preview.replace('##BusinessEmail##', 'info@tlciscreative.com')
    preview = preview.replace('##BusinessWebsite##', 'www.tlciscreative.com')
    
    # Customer Fields
    preview = preview.replace('##CustomerOrganization##', 'ZZ19-Org')
    preview = preview.replace('##CustomerTitle##', 'Mr.')
    preview = preview.replace('##CustomerFirstName##', 'John')
    preview = preview.replace('##CustomerLastName##', 'Smith')
    preview = preview.replace('##CustomerStreetAddress##', '456 Oak Avenue')
    preview = preview.replace('##CustomerCity##', 'Vancouver')
    preview = preview.replace('##CustomerPostalCode##', 'V6B 1A1')
    preview = preview.replace('##CustomerCountry##', 'Canada')
    preview = preview.replace('##CustomerWorkPhone##', '(604) 555-0456')
    preview = preview.replace('##CustomerEmail##', 'john.smith@example.com')
    
    # Shipping Fields
    preview = preview.replace('##CustomerShippingFirstName##', 'John')
    preview = preview.replace('##CustomerShippingLastName##', 'Smith')
    preview = preview.replace('##CustomerShippingStreetAddress##', '456 Oak Avenue')
    preview = preview.replace('##CustomerShippingCity##', 'Vancouver')
    preview = preview.replace('##CustomerShippingPostalCode##', 'V6B 1A1')
    preview = preview.replace('##CustomerShippingCountry##', 'Canada')
    
    # Quote Fields
    preview = preview.replace('##QuoteNumber##', 'Q-2025-001')
    preview = preview.replace('##QuoteLink##', 'https://tlciscreative.quoter.com/quote/webview/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
    preview = preview.replace('##QuoteWebViewURL##', 'https://tlciscreative.quoter.com/quote/webview/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
    preview = preview.replace('##QuotePDFURL##', 'https://tlciscreative.quoter.com/quote/download/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
    preview = preview.replace('##QuoteTotal##', '$2,500.00')
    preview = preview.replace('##QuoteUpfrontTotal##', '$1,000.00')
    preview = preview.replace('##QuoteRecurringTotal##', '$1,500.00')
    preview = preview.replace('##QuoteCreatedDate##', '2025/09/14')
    preview = preview.replace('##QuoteExpiryDate##', '2025/10/14')
    preview = preview.replace('##QuoteFormName##', 'Wedding Photography Package')
    
    # User Fields
    preview = preview.replace('##UserFirstName##', 'Maurice')
    preview = preview.replace('##UserLastName##', 'Capillaire')
    preview = preview.replace('##UserEmail##', 'maurice@tlciscreative.com')
    preview = preview.replace('##Signature##', 'Maurice Capillaire<br>Sales and Logistics')
    
    return f"""
    <html>
    <head><title>Preview - {TEMPLATE_BUNDLES[template_key]['name']}</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>Preview: {TEMPLATE_BUNDLES[template_key]['name']}</h1>
        <div style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;">
            {preview}
        </div>
        <a href="/" style="color: #667eea;">← Back to Editor</a>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🚀 Starting Cover Letter Editor...")
    print("📝 Access the editor at: http://localhost:5001")
    print("🎨 Features:")
    print("   • Select any of 11 templates")
    print("   • Live preview with sample data")
    print("   • Field code help")
    print("   • Save changes instantly")
    print("   • Reset to original content")
    
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
