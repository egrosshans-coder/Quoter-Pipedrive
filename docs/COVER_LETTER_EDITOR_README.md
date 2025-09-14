# 📝 Cover Letter Editor

A friendly, web-based interface for sales reps to customize cover letters for all TLC Creative templates.

## 🚀 Features

### **Beautiful, Modern Interface**
- Clean, responsive design
- Intuitive template selection grid
- Live preview as you type
- Professional color scheme

### **Template Management**
- **11 Templates Available:**
  - Floating Video
  - LED Wristbands
  - Balloons
  - CO2/Smoke/Upright Foggers
  - Confetti/Streamers
  - Fireworks/Pyro/Fire
  - LED Lanyards
  - Basic
  - Low Level Fog
  - Robotics
  - Tank Delivery

### **Smart Field Codes**
- **Available Fields:**
  - `{{person.first_name}}` - Contact's first name
  - `{{deal.title}}` - Deal title
  - `{{deal.id}}` - Deal ID
  - `{{deal.owner_name}}` - Deal owner name
  - `{{quote.owner.name}}` - Quote owner name
  - `{{quote.owner.email}}` - Quote owner email

### **Dynamic Role Logic**
- **Maurice Capillaire** → "Sales and Logistics"
- **Jeff Ward** → "Sales and Logistics"
- **Eric Grosshans** → "Technical Director"
- **Anyone else** → "Sales Team"

### **User-Friendly Features**
- ✅ **Live Preview** - See changes instantly with sample data
- ✅ **Field Code Help** - Built-in reference for available fields
- ✅ **Save Changes** - Updates templates instantly
- ✅ **Reset Function** - Restore original content anytime
- ✅ **Status Messages** - Clear feedback on actions

## 🎯 How to Use

### **1. Start the Editor**
```bash
# Activate virtual environment
source venv/bin/activate

# Run the editor
python cover_letter_editor.py
```

### **2. Access the Interface**
- Open your browser to: `http://localhost:5000`
- You'll see a beautiful grid of all 11 templates

### **3. Edit a Cover Letter**
1. **Click on any template** to select it
2. **Edit the content** in the text area
3. **See live preview** with sample data
4. **Click "Save Changes"** to update the template
5. **Use "Reset"** to restore original content

### **4. Field Code Examples**
```html
<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>
```

## 🎨 Interface Preview

### **Template Selection Grid**
- Clean cards showing template names
- Hover effects and active states
- Easy one-click selection

### **Editor Interface**
- Large text area with syntax highlighting
- Field code reference panel
- Live preview section
- Save/Reset buttons

### **Live Preview**
- Real-time updates as you type
- Sample data for field codes
- Professional formatting

## 🔧 Technical Details

### **Built With**
- **Flask** - Python web framework
- **HTML5/CSS3** - Modern styling
- **JavaScript** - Interactive features
- **Template Integration** - Direct access to `template_mapping_enhanced.py`

### **File Structure**
```
cover_letter_editor.py          # Main Flask application
COVER_LETTER_EDITOR_README.md   # This documentation
template_mapping_enhanced.py    # Template data source
```

### **API Endpoints**
- `GET /` - Main editor interface
- `POST /update_template` - Save template changes
- `GET /get_template/<key>` - Get specific template
- `GET /preview/<key>` - Preview template with sample data

## 🎯 Benefits for Sales Reps

### **No Technical Knowledge Required**
- Visual interface - no code editing
- Built-in help for field codes
- Instant feedback and preview

### **Professional Results**
- Consistent formatting across all templates
- Dynamic personalization with real data
- Professional appearance for clients

### **Easy Customization**
- Modify any template in minutes
- Test changes with live preview
- Revert changes if needed

### **Time Saving**
- No need to manually edit Python files
- Batch updates across templates
- Instant deployment of changes

## 🚀 Getting Started

1. **Ensure you're in the project directory**
2. **Activate the virtual environment**
3. **Run the editor**
4. **Open your browser to localhost:5000**
5. **Start customizing cover letters!**

The editor is now ready for your sales team to use! 🎉
