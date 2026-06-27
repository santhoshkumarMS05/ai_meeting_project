from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
import re

def generate_pdf(meeting_title, summary, task_assignments, dependencies, key_decisions, next_steps, meeting_name="Meeting", 
                 participants=None, duration=None):
    """
    Generate a professional PDF report from meeting analysis results.
    Returns the PDF file path and filename.
    
    Args:
        meeting_title: Title of the meeting
        summary: Meeting summary text
        task_assignments: Task assignments data
        dependencies: Dependencies data
        key_decisions: Key decisions data
        next_steps: Next steps data
        meeting_name: Name for the PDF file
        participants: List of participant names (optional)
        duration: Meeting duration in minutes (optional)
    """
    
    # Generate PDF filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"{meeting_name}_Summary_{timestamp}.pdf"
    pdf_folder = "generated_pdfs"
    os.makedirs(pdf_folder, exist_ok=True)
    pdf_path = os.path.join(pdf_folder, pdf_filename)
    
    # Create PDF document with frame for border
    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=A4,
        rightMargin=0.7*inch, 
        leftMargin=0.7*inch,
        topMargin=0.7*inch, 
        bottomMargin=0.9*inch  # Extra space for footer
    )
    
    # Container for PDF elements
    story = []
    
    # Define styles with better fonts
    styles = getSampleStyleSheet()
    
    # Custom styles with different colors for title and headings
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=28
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica',
        leading=18
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=12,
        spaceBefore=22,
        fontName='Helvetica-Bold',
        leading=20
    )
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    content_style = ParagraphStyle(
        'ContentStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=18,
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#334155'),
        fontName='Helvetica'
    )
    
    info_box_style = ParagraphStyle(
        'InfoBoxStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        fontName='Helvetica',
        alignment=TA_LEFT
    )
    
    # Add title
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(meeting_title, title_style))
    story.append(Paragraph("Meeting Summary Report", subtitle_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", date_style))
    
    # Removed the date info box as requested
    story.append(Spacer(1, 0.3*inch))
    
    # Add Meeting Summary section with Unicode symbol
    summary_section = []
    summary_section.append(Paragraph("■ Meeting Overview", heading_style))
    summary_section.append(Spacer(1, 0.1*inch))

    # Clean and format summary - remove all bullet points and asterisks
    clean_summary = summary.replace('*', '').replace('•', '').strip()
    
    # Split into paragraphs and remove any lines that look like bullet formatting
    summary_paragraphs = clean_summary.split('\n\n')
    for para in summary_paragraphs:
        if para.strip():
            # Remove any remaining bullet-like formatting
            lines = para.split('\n')
            combined_text = ' '.join(line.strip() for line in lines if line.strip())
            
            # Skip lines that are just headers or formatting
            if combined_text and len(combined_text) > 10:
                summary_section.append(Paragraph(combined_text, content_style))
    
    # Add summary section to story
    story.extend(summary_section)
    story.append(Spacer(1, 0.3*inch))
    
    # Add Task Assignments section with Unicode symbol
    task_section = []
    task_section.append(Paragraph("▶ Task Assignments", heading_style))
    task_section.append(Spacer(1, 0.1*inch))
    
    task_table = parse_and_create_task_table(task_assignments)
    if task_table:
        task_section.append(task_table)
    else:
        task_section.append(Paragraph("No task assignments found in the transcript.", content_style))
    
    # Keep heading and table together
    story.append(KeepTogether(task_section))
    story.append(Spacer(1, 0.3*inch))
    
    # Add Dependencies section with Unicode symbol
    dependency_section = []
    dependency_section.append(Paragraph("◆ Task Dependencies", heading_style))
    dependency_section.append(Spacer(1, 0.1*inch))
    
    dependency_table = parse_and_create_dependency_table(dependencies)
    if dependency_table:
        dependency_section.append(dependency_table)
        dependency_section.append(Spacer(1, 0.12*inch))
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=content_style,
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_LEFT,
            fontName='Helvetica-Oblique'
        )
        dependency_section.append(Paragraph("Note: Only explicit or clearly logical dependencies are included in the table.", note_style))
    else:
        dependency_section.append(Paragraph("No task dependencies identified in this meeting.", content_style))
    
    # Keep heading and table together
    story.append(KeepTogether(dependency_section))
    story.append(Spacer(1, 0.3*inch))
    
    # Add Key Decisions section with Unicode symbol
    key_decisions_section = []
    key_decisions_section.append(Paragraph("★ Key Decisions", heading_style))
    key_decisions_section.append(Spacer(1, 0.1*inch))
    
    key_decisions_table = parse_and_create_key_decisions_table(key_decisions)
    if key_decisions_table:
        key_decisions_section.append(key_decisions_table)
    else:
        key_decisions_section.append(Paragraph("No key decisions were made in this meeting.", content_style))
    
    # Keep heading and table together
    story.append(KeepTogether(key_decisions_section))
    story.append(Spacer(1, 0.3*inch))
    
    # Add Next Steps section with Unicode symbol
    next_steps_section = []
    next_steps_section.append(Paragraph("→ Next Steps", heading_style))
    next_steps_section.append(Spacer(1, 0.1*inch))
    
    next_steps_table = parse_and_create_next_steps_table(next_steps)
    if next_steps_table:
        next_steps_section.append(next_steps_table)
    else:
        next_steps_section.append(Paragraph("No next steps were identified in this meeting.", content_style))
    
    # Keep heading and table together
    story.append(KeepTogether(next_steps_section))
    
    # Build PDF with border frame and footer
    doc.build(story, onFirstPage=add_page_number_and_footer, onLaterPages=add_page_number_and_footer)
    
    return pdf_path, pdf_filename


def add_page_number_and_footer(canvas, doc):
    """
    Add a border, page number, and footer to each page of the PDF
    """
    canvas.saveState()
    
    # Set border color and width
    canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
    canvas.setLineWidth(1)
    
    # Draw rectangle border with some margin from edges
    margin = 0.5 * inch
    canvas.rect(
        margin, 
        margin, 
        A4[0] - 2*margin, 
        A4[1] - 2*margin
    )
    
    # Add footer
    footer_y = 0.6 * inch
    
    # "Generated by Meeting AI Pro" - left aligned
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#64748b'))
    canvas.drawString(0.7 * inch, footer_y, "Generated by Meeting AI Pro")
    
    # Page number - right aligned
    page_num = canvas.getPageNumber()
    page_text = f"Page {page_num}"
    canvas.drawRightString(A4[0] - 0.7 * inch, footer_y, page_text)
    
    canvas.restoreState()


def parse_and_create_task_table(task_assignments):
    """
    Parse task assignments and create a formatted table.
    Only creates table if there are 2 or more data rows.
    """
    if not task_assignments or "No task" in task_assignments:
        return None
    
    lines = task_assignments.strip().split('\n')
    table_data = []
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=14
    )

    # Content styles
    cell_style_left = ParagraphStyle(
        'CellStyleLeft',
        fontSize=10,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=13
    ) 
    
    # Add header
    table_data.append([
        Paragraph('Assigned To', header_style),
        Paragraph('Task', header_style),
        Paragraph('Deadline', header_style)
    ])
    
    # Parse data rows
    for line in lines:
        line = line.strip()
        if ('|' in line and 
            not line.startswith('---') and 
            'Assigned To' not in line and
            'Task' not in line and
            '---' not in line):
            
            cells = [cell.strip() for cell in line.split('|')]
            cells = [cell for cell in cells if cell]
            
            if len(cells) >= 3:
                table_data.append([
                    Paragraph(cells[0], cell_style_left),
                    Paragraph(cells[1], cell_style_left),
                    Paragraph(cells[2], cell_style_left)
                ])
    
    # Check if we have at least 2 data rows (3 total including header)
    if len(table_data) < 3:
        return None
    
    # Create table
    table = Table(
        table_data, 
        colWidths=[1.3*inch, 3.5*inch, 1.8*inch],
        repeatRows=1
    )
    
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#312e81')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    return table


def parse_and_create_dependency_table(dependencies):
    """
    Parse dependencies and create a formatted table.
    Only creates table if there are 2 or more data rows.
    """
    if not dependencies or "No task" in dependencies or "No dependency" in dependencies.lower():
        return None
    
    lines = dependencies.strip().split('\n')
    table_data = []
    
    # Header style
    header_style = ParagraphStyle(
        'HeaderStyle',
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=12
    )
    
    # Content style
    cell_style_left = ParagraphStyle(
        'CellStyleLeft',
        fontSize=10,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=12
    )
    
    # Add header
    table_data.append([
        Paragraph('Person', header_style),
        Paragraph('Dependent Task', header_style),
        Paragraph('Depends On', header_style),
        Paragraph('Required Task', header_style),
        Paragraph('Reason', header_style)
    ])
    
    # Parse data rows
    for line in lines:
        line = line.strip()
        if ('|' in line and 
            not line.startswith('---') and 
            'Dependent Person' not in line and
            'Person' not in line and
            '---' not in line):
            
            cells = [cell.strip() for cell in line.split('|')]
            cells = [cell for cell in cells if cell]
            
            if len(cells) >= 5:
                table_data.append([
                    Paragraph(cells[0], cell_style_left),
                    Paragraph(cells[1], cell_style_left),
                    Paragraph(cells[2], cell_style_left),
                    Paragraph(cells[3], cell_style_left),
                    Paragraph(cells[4], cell_style_left)
                ])
    
    # Check if we have at least 2 data rows (3 total including header)
    if len(table_data) < 3:
        return None
    
    # Create table
    table = Table(
        table_data, 
        colWidths=[0.85*inch, 1.5*inch, 0.85*inch, 1.4*inch, 1.9*inch],
        repeatRows=1
    )
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#312e81')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    return table


def parse_and_create_key_decisions_table(key_decisions):
    """
    Parse key decisions and create a formatted table.
    Only creates table if there are 2 or more data rows.
    """
    if not key_decisions or "No key decision" in key_decisions.lower():
        return None
    
    lines = key_decisions.strip().split('\n')
    table_data = []
    
    # Header style
    header_style = ParagraphStyle(
        'HeaderStyle',
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=12
    )
    
    # Content style
    cell_style_left = ParagraphStyle(
        'CellStyleLeft',
        fontSize=10,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=12
    )
    
    # Add header
    table_data.append([
        Paragraph('Decision', header_style),
        Paragraph('Made By', header_style),
        Paragraph('Impact', header_style)
    ])
    
    # Parse data rows
    for line in lines:
        line = line.strip()
        if ('|' in line and 
            not line.startswith('---') and 
            'Decision' not in line and
            'Made By' not in line and
            '---' not in line):
            
            cells = [cell.strip() for cell in line.split('|')]
            cells = [cell for cell in cells if cell]
            
            if len(cells) >= 3:
                table_data.append([
                    Paragraph(cells[0], cell_style_left),
                    Paragraph(cells[1], cell_style_left),
                    Paragraph(cells[2], cell_style_left)
                ])
    
    # Check if we have at least 2 data rows (3 total including header)
    if len(table_data) < 3:
        return None
    
    # Create table
    table = Table(
        table_data, 
        colWidths=[3.0*inch, 1.5*inch, 2.0*inch],
        repeatRows=1
    )
    
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#312e81')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    return table


def parse_and_create_next_steps_table(next_steps):
    """
    Parse next steps and create a formatted table.
    Only creates table if there are 2 or more data rows.
    """
    if not next_steps or "No next step" in next_steps.lower():
        return None
    
    lines = next_steps.strip().split('\n')
    table_data = []
    
    # Header style
    header_style = ParagraphStyle(
        'HeaderStyle',
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=12
    )
    
    # Content style
    cell_style_left = ParagraphStyle(
        'CellStyleLeft',
        fontSize=10,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=12
    )
    
    # Add header
    table_data.append([
        Paragraph('Action', header_style),
        Paragraph('Owner', header_style),
        Paragraph('Timeline', header_style)
    ])
    
    # Parse data rows
    for line in lines:
        line = line.strip()
        if ('|' in line and 
            not line.startswith('---') and 
            'Action' not in line and
            'Owner' not in line and
            '---' not in line):
            
            cells = [cell.strip() for cell in line.split('|')]
            cells = [cell for cell in cells if cell]
            
            if len(cells) >= 3:
                table_data.append([
                    Paragraph(cells[0], cell_style_left),
                    Paragraph(cells[1], cell_style_left),
                    Paragraph(cells[2], cell_style_left)
                ])
    
    # Check if we have at least 2 data rows (3 total including header)
    if len(table_data) < 3:
        return None
    
    # Create table
    table = Table(
        table_data, 
        colWidths=[3.2*inch, 1.5*inch, 1.8*inch],
        repeatRows=1
    )
    
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#312e81')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    return table