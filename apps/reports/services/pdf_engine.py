"""
Enhanced PDF generation engine using FPDF2.
Generates professional PDF reports with cover page, rich content, and page numbers.
Supports Unicode via DejaVu fonts (when available), with graceful Helvetica fallback.
"""
import os
import re
import logging
import tempfile
import urllib.request
from urllib.parse import urlparse
from datetime import datetime
from fpdf import FPDF
from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Font configuration - searches multiple locations automatically
# ---------------------------------------------------------------------------

def _get_font_search_paths():
    """Build a list of directories to search for font files."""
    paths = []

    # 1. Project-level fonts directory (RECOMMENDED)
    paths.append(os.path.join(settings.BASE_DIR, "fonts"))

    # 2. Settings override
    if hasattr(settings, "PDF_FONT_DIR"):
        paths.append(settings.PDF_FONT_DIR)

    # 3. Same directory as this file (for backward compat with auto-download)
    paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"))

    # 4. Windows system fonts
    paths.append(r"C:\Windows\Fonts")

    # 5. Common Linux font directories
    paths.extend([
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype",
        "/usr/local/share/fonts",
        os.path.expanduser("~/.fonts"),
    ])

    # 6. macOS
    paths.extend([
        "/Library/Fonts",
        "/System/Library/Fonts",
        os.path.expanduser("~/Library/Fonts"),
    ])

    return [p for p in paths if os.path.isdir(p)]


def _find_font_file(filename):
    """Search for a font file in all known locations."""
    for directory in _get_font_search_paths():
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return path
    return None


class ResearchPDF(FPDF):
    """
    Custom FPDF subclass with automatic footer (page numbers) 
    and header support. Excludes page number on cover page (page 1).
    """

    def __init__(self, accent_rgb=(37, 99, 235), **kwargs):
        super().__init__(**kwargs)
        self.accent_rgb = accent_rgb

    def footer(self):
        """Auto-called on every page. Skip cover page (page 1)."""
        if self.page_no() == 1:
            return

        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(150, 150, 150)
        # Content page number: current page - 1 (since page 1 is cover)
        page_num = self.page_no() - 1
        self.cell(0, 10, text=f"Page {page_num}", align="C")


class PDFExporter:
    """
    Export research reports to professional PDFs.

    Features:
    - Branded cover page with logo and accent color
    - Unicode support via DejaVu fonts (auto-detected)
    - Rich markdown parsing (headers, lists, tables, code blocks, blockquotes)
    - Clickable source links
    - Auto page numbering (excludes cover)
    - Professional typography with proper hierarchy
    """

    # Markdown parsing state
    STATE_NORMAL = "normal"
    STATE_CODE_BLOCK = "code_block"
    STATE_BLOCKQUOTE = "blockquote"

    def __init__(self):
        self.pdf = None
        self.accent_rgb = None
        self._code_block_buffer = []
        self._state = self.STATE_NORMAL
        self._blockquote_buffer = []
        self._has_unicode_fonts = False
        self._font_family = "DejaVu"
        self._font_mono = "DejaVuMono"

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _clean_text(self, text: str) -> str:
        """
        Clean text for PDF rendering.
        If using DejaVu fonts, only strip control characters.
        If using Helvetica fallback, strip ALL non-ASCII characters.
        """
        if not text:
            return ""

        # Always strip zero-width and control chars
        replacements = {
            "\u200b": "",   # zero-width space
            "\u200c": "",   # zero-width non-joiner
            "\u200d": "",   # zero-width joiner
            "\ufeff": "",   # BOM
            "\t": "    ",   # tabs to spaces
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)

        # If no Unicode fonts, aggressively strip to ASCII
        if not self._has_unicode_fonts:
            text = self._to_ascii(text)

        return text

    def _to_ascii(self, text: str) -> str:
        """Replace Unicode characters with ASCII equivalents for Helvetica."""
        replacements = {
            "\u2022": "-",      # bullet -> dash
            "\u00b7": "-",      # middle dot -> dash
            "\u2605": "*",      # black star -> asterisk
            "\u2606": "*",      # white star -> asterisk
            "\u2013": "-",      # en dash -> dash
            "\u2014": "-",      # em dash -> dash
            "\u201c": '"',      # left double quote -> "
            "\u201d": '"',      # right double quote -> "
            "\u2018": "'",      # left single quote -> '
            "\u2019": "'",      # right single quote -> '
            "\u2026": "...",    # ellipsis -> ...
            "\u00a9": "(c)",    # copyright
            "\u00ae": "(R)",    # registered
            "\u2122": "(TM)",   # trademark
            "\u20ac": "EUR",    # euro
            "\u00a3": "GBP",    # pound
            "\u00a5": "YEN",    # yen
            "\u20b9": "INR",    # rupee
            "\u2713": "[x]",    # check mark
            "\u2714": "[x]",    # heavy check mark
            "\u2717": "[ ]",    # ballot x
            "\u2718": "[ ]",    # heavy ballot x
            "\u2192": "->",     # right arrow
            "\u2190": "<-",     # left arrow
            "\u2011": "-",      # non-breaking hyphen
            "\u00a0": " ",      # non-breaking space
        }
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
        # Remove any remaining non-ASCII characters
        return "".join(c for c in text if ord(c) < 128)

    def _resolve_logo(self, logo_url: str) -> str:
        """Resolve a logo URL to a local file path."""
        if not logo_url:
            return None

        # Absolute local path
        if logo_url.startswith("/"):
            if logo_url.startswith(settings.MEDIA_URL):
                rel_path = logo_url[len(settings.MEDIA_URL):]
                local = os.path.join(settings.MEDIA_ROOT, rel_path)
                return local if os.path.exists(local) else None
            if logo_url.startswith(settings.STATIC_URL):
                rel_path = logo_url[len(settings.STATIC_URL):]
                for static_dir in settings.STATICFILES_DIRS:
                    local = os.path.join(static_dir, rel_path)
                    if os.path.exists(local):
                        return local
                return None
            return logo_url if os.path.exists(logo_url) else None

        # Remote URL
        if logo_url.startswith(("http://", "https://")):
            try:
                parsed = urlparse(logo_url)
                suffix = os.path.splitext(parsed.path)[1] or ".png"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    urllib.request.urlretrieve(logo_url, tmp.name)
                    return tmp.name
            except Exception as e:
                logger.warning(f"Failed to download logo: {e}")
                return None

        # Relative path
        local = os.path.join(settings.MEDIA_ROOT, logo_url)
        return local if os.path.exists(local) else None

    def _add_unicode_fonts(self):
        """Add DejaVu fonts for Unicode support. Search common locations."""
        font_files = {
            ("DejaVu", ""): "DejaVuSans.ttf",
            ("DejaVu", "B"): "DejaVuSans-Bold.ttf",
            ("DejaVu", "I"): "DejaVuSans-Oblique.ttf",
            ("DejaVu", "BI"): "DejaVuSans-BoldOblique.ttf",
            ("DejaVuMono", ""): "DejaVuSansMono.ttf",
            ("DejaVuMono", "B"): "DejaVuSansMono-Bold.ttf",
        }

        all_found = True
        found_paths = []
        missing = []

        for (family, style), filename in font_files.items():
            path = _find_font_file(filename)
            if path:
                try:
                    self.pdf.add_font(family, style, path, uni=True)
                    found_paths.append(path)
                except Exception as e:
                    logger.warning(f"Failed to add font {family}/{style} from {path}: {e}")
                    all_found = False
                    missing.append(filename)
            else:
                all_found = False
                missing.append(filename)

        self._has_unicode_fonts = all_found

        if all_found:
            logger.info(f"Loaded DejaVu fonts from: {os.path.dirname(found_paths[0])}")
        else:
            logger.warning(
                "DejaVu fonts not found. Missing: %s. "
                "Falling back to Helvetica (ASCII only). "
                "To enable Unicode support, download from "
                "https://dejavu-fonts.github.io/Download.html and place .ttf files in: %s",
                ", ".join(missing),
                os.path.join(settings.BASE_DIR, "fonts")
            )
            self._font_family = "Helvetica"
            self._font_mono = "Courier"

    def _set_font(self, family="DejaVu", style="", size=11):
        """Safe font setter with automatic fallback."""
        if not self._has_unicode_fonts:
            family = "Courier" if "Mono" in family else "Helvetica"
        try:
            self.pdf.set_font(family, style, size)
        except Exception as e:
            logger.debug(f"Font set failed for {family}, using Helvetica: {e}")
            fallback = "Courier" if "Mono" in family else "Helvetica"
            self.pdf.set_font(fallback, style, size)

    def export(
        self,
        markdown_content: str,
        research,
        accent_color: str = "#2563EB",
        logo_url: str = None,
        output_path: str = None
    ) -> str:
        """
        Generate the PDF.

        Args:
            markdown_content: Markdown text to render
            research: ResearchQuery model instance (for metadata)
            accent_color: Hex color for branding
            logo_url: URL/path to logo image
            output_path: Where to save the PDF

        Returns:
            Path to generated PDF file
        """
        self.accent_rgb = self._hex_to_rgb(accent_color)

        # Use custom FPDF subclass with automatic footer
        self.pdf = ResearchPDF(accent_rgb=self.accent_rgb)
        self.pdf.set_auto_page_break(auto=True, margin=25)

        # Add Unicode fonts (with fallback detection)
        self._add_unicode_fonts()

        # --- Cover page ---
        self._add_cover_page(research, logo_url, accent_color)

        # --- Content pages ---
        cleaned_content = self._clean_text(markdown_content)
        self._add_content(cleaned_content)

        # --- Save ---
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            self.pdf.output(output_path)
            return output_path
        return None

    def _add_cover_page(self, research, logo_url=None, accent_color="#2563EB"):
        """Professional cover page with branding."""
        self.pdf.add_page()

        # Accent bar at top
        self.pdf.set_fill_color(*self._hex_to_rgb(accent_color))
        self.pdf.rect(0, 0, 210, 12, "F")

        # Logo
        y_pos = 40
        if logo_url:
            logo_path = self._resolve_logo(logo_url)
            if logo_path:
                try:
                    self.pdf.image(logo_path, x=75, y=25, w=60)
                    y_pos = 100
                except Exception as e:
                    logger.warning(f"Could not load logo: {e}")

        # Main title
        self.pdf.set_y(y_pos)
        self._set_font("DejaVu", "B", 28)
        self.pdf.set_text_color(*self.accent_rgb)
        self.pdf.cell(0, 20, text="AI Research Report", align="C", new_x="LMARGIN", new_y="NEXT")

        # Decorative line
        self.pdf.ln(5)
        self.pdf.set_draw_color(*self.accent_rgb)
        self.pdf.set_line_width(0.5)
        line_y = self.pdf.get_y()
        self.pdf.line(60, line_y, 150, line_y)
        self.pdf.ln(15)

        # Report title
        title = f"Research Report: {research.query_text[:50]}"
        self._set_font("DejaVu", "B", 18)
        self.pdf.set_text_color(30, 30, 30)
        self.pdf.multi_cell(0, 12, text=self._clean_text(title), align="C")
        self.pdf.ln(10)

        # Query
        self._set_font("DejaVu", "", 11)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.multi_cell(0, 7, text=f"Query: {self._clean_text(research.query_text)}", align="C")
        self.pdf.ln(20)

        # Metadata box
        source_count = research.sources.count() if hasattr(research, "sources") else 0
        self._set_font("DejaVu", "", 10)
        self.pdf.set_text_color(100, 100, 100)
        self.pdf.set_fill_color(245, 245, 245)
        self.pdf.set_draw_color(200, 200, 200)
        box_y = self.pdf.get_y()
        self.pdf.rect(40, box_y, 130, 50, "FD")

        self.pdf.set_y(box_y + 8)
        self.pdf.set_x(50)
        self.pdf.cell(0, 6, text=f"Generated: {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_x(50)
        self.pdf.cell(0, 6, text=f"Source Count: {source_count}", new_x="LMARGIN", new_y="NEXT")

        search_depth = getattr(research, "search_depth", "standard")
        llm_model = getattr(research, "llm_model", "default")

        self.pdf.set_x(50)
        self.pdf.cell(0, 6, text=f"Search Depth: {search_depth.title() if isinstance(search_depth, str) else 'Standard'}", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_x(50)
        self.pdf.cell(0, 6, text=f"LLM Model: {llm_model.title() if isinstance(llm_model, str) else 'Default'}", new_x="LMARGIN", new_y="NEXT")

        # Footer
        self.pdf.set_y(270)
        self.pdf.set_draw_color(*self.accent_rgb)
        self.pdf.set_line_width(0.3)
        self.pdf.line(20, 270, 190, 270)
        self._set_font("DejaVu", "", 8)
        self.pdf.set_text_color(150, 150, 150)
        self.pdf.cell(0, 8, text="Generated by AI Research Agent", align="C")

    def _add_content(self, markdown_content: str):
        """Render the body content with full markdown support."""
        lines = markdown_content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Handle state transitions
            if self._state == self.STATE_CODE_BLOCK:
                if line.strip().startswith("```"):
                    self._flush_code_block()
                    self._state = self.STATE_NORMAL
                else:
                    self._code_block_buffer.append(line)
                i += 1
                continue

            if self._state == self.STATE_BLOCKQUOTE:
                if not line.strip().startswith(">"):
                    self._flush_blockquote()
                    self._state = self.STATE_NORMAL
                    continue  # Re-process this line in normal state
                else:
                    self._blockquote_buffer.append(line.lstrip(">").strip())
                    i += 1
                    continue

            # Normal state processing
            if not line:
                self.pdf.ln(4)
                i += 1
                continue

            # Code block start
            if line.strip().startswith("```"):
                self._state = self.STATE_CODE_BLOCK
                self._code_block_buffer = []
                i += 1
                continue

            # Blockquote start
            if line.strip().startswith(">"):
                self._state = self.STATE_BLOCKQUOTE
                self._blockquote_buffer = [line.lstrip(">").strip()]
                i += 1
                continue

            # H1 Header
            if line.startswith("# "):
                self.pdf.ln(6)
                self._set_font("DejaVu", "B", 20)
                self.pdf.set_text_color(*self.accent_rgb)
                self.pdf.multi_cell(0, 10, text=self._clean_text(line[2:]), new_x="LMARGIN", new_y="NEXT")
                self.pdf.set_draw_color(*self.accent_rgb)
                line_y = self.pdf.get_y()
                self.pdf.line(20, line_y, 190, line_y)
                self.pdf.ln(6)

            # H2 Header
            elif line.startswith("## "):
                self.pdf.ln(8)
                self._set_font("DejaVu", "B", 16)
                self.pdf.set_text_color(30, 30, 30)
                self.pdf.multi_cell(0, 9, text=self._clean_text(line[3:]), new_x="LMARGIN", new_y="NEXT")
                self.pdf.ln(4)

            # H3 Header
            elif line.startswith("### "):
                self.pdf.ln(4)
                self._set_font("DejaVu", "B", 13)
                self.pdf.set_text_color(50, 50, 50)
                self.pdf.multi_cell(0, 8, text=self._clean_text(line[4:]), new_x="LMARGIN", new_y="NEXT")
                self.pdf.ln(3)

            # Horizontal rule
            elif line.startswith("---") or line.startswith("==="):
                self.pdf.ln(6)
                self.pdf.set_draw_color(200, 200, 200)
                self.pdf.set_line_width(0.3)
                line_y = self.pdf.get_y()
                self.pdf.line(20, line_y, 190, line_y)
                self.pdf.ln(6)

            # Table row (not separator)
            elif "|" in line and "---" not in line and not line.replace("|", "").replace("-", "").replace(":", "").strip() == "":
                self._render_table_line(line)

            # Bullet list
            elif line.startswith("- ") or line.startswith("* "):
                self._set_font("DejaVu", "", 11)
                self.pdf.set_text_color(50, 50, 50)
                self.pdf.set_x(25)
                # Use ASCII-safe bullet when no Unicode fonts
                bullet_char = "-" if not self._has_unicode_fonts else "\u2022"
                self.pdf.cell(6, 7, text=bullet_char, new_x="RIGHT", new_y="TOP")
                self._render_rich_text(self._clean_text(line[2:]), x=31)
                self.pdf.ln(6)

            # Numbered list
            elif re.match(r"^\d+\.\s", line):
                self._set_font("DejaVu", "", 11)
                self.pdf.set_text_color(50, 50, 50)
                match = re.match(r"^(\d+)\.\s(.*)", line)
                if match:
                    num, text = match.groups()
                    self.pdf.set_x(25)
                    self.pdf.cell(10, 7, text=f"{num}.", new_x="RIGHT", new_y="TOP")
                    self._render_rich_text(self._clean_text(text), x=35)
                self.pdf.ln(6)

            # Regular paragraph
            else:
                self._set_font("DejaVu", "", 11)
                self.pdf.set_text_color(50, 50, 50)
                self._render_rich_text(self._clean_text(line), x=20)
                self.pdf.ln(5)

            i += 1

        # Flush any remaining states
        if self._state == self.STATE_CODE_BLOCK:
            self._flush_code_block()
        if self._state == self.STATE_BLOCKQUOTE:
            self._flush_blockquote()

    def _flush_code_block(self):
        """Render accumulated code block."""
        if not self._code_block_buffer:
            return
        self.pdf.ln(4)
        # Code block background
        code_text = "\n".join(self._code_block_buffer)
        line_count = len(self._code_block_buffer)
        block_height = max(line_count * 5 + 8, 20)

        self.pdf.set_fill_color(245, 245, 245)
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.rect(20, self.pdf.get_y(), 170, block_height, "FD")

        self.pdf.set_xy(24, self.pdf.get_y() + 4)
        self._set_font("DejaVuMono", "", 9)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.multi_cell(162, 5, text=code_text, new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(4)
        self._code_block_buffer = []

    def _flush_blockquote(self):
        """Render accumulated blockquote."""
        if not self._blockquote_buffer:
            return
        self.pdf.ln(4)
        quote_text = " ".join(self._blockquote_buffer)

        # Left accent bar
        self.pdf.set_fill_color(*self.accent_rgb)
        self.pdf.rect(20, self.pdf.get_y(), 3, 20, "F")

        self.pdf.set_x(28)
        self._set_font("DejaVu", "I", 11)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.multi_cell(162, 6, text=quote_text, new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(4)
        self._blockquote_buffer = []

    def _render_table_line(self, line: str):
        """Render a Markdown table row with proper styling."""
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells:
            return

        # Clean cells (remove markdown formatting for table display)
        clean_cells = []
        for cell in cells:
            cell = re.sub(r"\*\*", "", cell)
            cell = re.sub(r"\*(?!\*)", "", cell)
            clean_cells.append(self._clean_text(cell))

        # Determine if header row (simple heuristic: all caps or bold markers)
        is_header = any("**" in c or c.isupper() for c in cells) or self.pdf.get_y() < 50

        # Column widths - distribute evenly
        total_width = 170
        num_cols = len(clean_cells)
        if num_cols == 2:
            col_widths = [total_width * 0.4, total_width * 0.6]
        elif num_cols == 3:
            col_widths = [total_width * 0.3, total_width * 0.4, total_width * 0.3]
        else:
            col_widths = [total_width / num_cols] * num_cols

        x_start = 20
        y_before = self.pdf.get_y()

        # Determine row height based on content
        max_height = 8
        for cell in clean_cells:
            lines_count = max(1, len(cell) // 35 + 1)
            max_height = max(max_height, lines_count * 5.5)

        # Draw cells
        x_pos = x_start
        for i, cell in enumerate(clean_cells):
            self.pdf.set_y(y_before)
            self.pdf.set_x(x_pos)

            if is_header:
                self.pdf.set_fill_color(*self.accent_rgb)
                self.pdf.set_text_color(255, 255, 255)
                self._set_font("DejaVu", "B", 10)
            else:
                self.pdf.set_fill_color(248, 248, 248)
                self.pdf.set_text_color(50, 50, 50)
                self._set_font("DejaVu", "", 10)

            # Draw cell background/border
            self.pdf.cell(col_widths[i], max_height, text="", border=1, ln=0, fill=True)

            # Draw text
            self.pdf.set_y(y_before + 2)
            self.pdf.set_x(x_pos + 3)
            if is_header:
                self._set_font("DejaVu", "B", 9)
                self.pdf.set_text_color(255, 255, 255)
            else:
                self._set_font("DejaVu", "", 9)
                self.pdf.set_text_color(50, 50, 50)

            # Truncate very long cells
            display_cell = cell[:45] + "..." if len(cell) > 45 else cell
            self.pdf.multi_cell(col_widths[i] - 6, 5, text=display_cell, border=0, align="L")

            x_pos += col_widths[i]

        self.pdf.ln(max_height + 2)

    def _render_rich_text(self, text: str, x: float = 20):
        """Render inline formatting: bold, italic, code, links."""
        self.pdf.set_x(x)

        # Split by markdown patterns
        parts = re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\))", text)
        for part in parts:
            if not part:
                continue

            # Bold **text**
            if part.startswith("**") and part.endswith("**"):
                self._set_font("DejaVu", "B", 11)
                self.pdf.write(7, text=part[2:-2])

            # Italic *text* (but not **)
            elif part.startswith("*") and part.endswith("*") and not part.startswith("**"):
                self._set_font("DejaVu", "I", 11)
                self.pdf.write(7, text=part[1:-1])

            # Inline code `text`
            elif part.startswith("`") and part.endswith("`"):
                self._set_font("DejaVuMono", "", 10)
                self.pdf.set_text_color(100, 100, 200)
                self.pdf.write(7, text=part[1:-1])
                self.pdf.set_text_color(50, 50, 50)

            # Link [text](url)
            elif re.match(r"\[.*?\]\(.*?\)", part):
                match = re.match(r"\[(.*?)\]\((.*?)\)", part)
                if match:
                    link_text, url = match.groups()
                    if url and url != "#" and not url.startswith("javascript:"):
                        try:
                            self._set_font("DejaVu", "U", 11)
                            self.pdf.set_text_color(0, 0, 200)
                            self.pdf.write(7, text=link_text, link=url)
                            self.pdf.set_text_color(50, 50, 50)
                        except Exception:
                            self._set_font("DejaVu", "", 11)
                            self.pdf.write(7, text=link_text)
                    else:
                        self._set_font("DejaVu", "", 11)
                        self.pdf.write(7, text=link_text)

            # Plain text
            else:
                self._set_font("DejaVu", "", 11)
                self.pdf.write(7, text=part)