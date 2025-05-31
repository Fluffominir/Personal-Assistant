
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

# Ensure data directory exists
os.makedirs("data/raw", exist_ok=True)

# Create the PDF
doc = SimpleDocTemplate("data/raw/michael_personal_info.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Title
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Title'],
    fontSize=24,
    spaceAfter=30,
)
story.append(Paragraph("Michael Slusher - Personal Information", title_style))
story.append(Spacer(1, 12))

# Personal info
content = [
    ("About Michael Slusher", [
        "Michael Slusher is the founder and creative director of Rocket Launch Studio.",
        "He specializes in video production, content creation, and creative marketing solutions.",
        "Michael has ADHD and is passionate about helping other neurodivergent entrepreneurs succeed.",
        "He is known for his innovative approach to storytelling and brand development."
    ]),
    
    ("Family Information", [
        "Michael has a twin sister named Sarah Slusher.",
        "His parents are Robert Slusher (father) and Jennifer Slusher (mother).",
        "He has one brother named David Slusher.",
        "His family is very close and supportive of his entrepreneurial ventures."
    ]),
    
    ("Professional Background", [
        "Founder of Rocket Launch Studio - a creative agency specializing in video production",
        "Expert in content strategy and brand storytelling",
        "Experienced in working with clients across various industries",
        "Passionate about helping businesses tell their stories through compelling video content"
    ]),
    
    ("Personal Interests", [
        "Technology and innovation",
        "Creative arts and filmmaking",
        "Entrepreneurship and business development",
        "Helping other ADHD entrepreneurs",
        "Continuous learning and personal growth"
    ]),
    
    ("Goals and Values", [
        "Building authentic connections through storytelling",
        "Creating impactful content that drives results",
        "Supporting the neurodivergent community",
        "Maintaining work-life balance while pursuing excellence",
        "Fostering creativity and innovation in all projects"
    ])
]

for section_title, items in content:
    # Section header
    story.append(Paragraph(section_title, styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Section content
    for item in items:
        story.append(Paragraph(f"• {item}", styles['Normal']))
        story.append(Spacer(1, 6))
    
    story.append(Spacer(1, 20))

# Build PDF
doc.build(story)
print("✓ Created test PDF: data/raw/michael_personal_info.pdf")
