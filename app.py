from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import shutil

# ==============================
# Configuration
# ==============================
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
ORGANIZED_FOLDER = BASE_DIR / 'organized'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB limit

# Ensure folders exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
ORGANIZED_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['ORGANIZED_FOLDER'] = str(ORGANIZED_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = 'change-this-secret-key'


# ==============================
# Helper Functions
# ==============================
def human_size(nbytes):
    """Convert bytes to human-readable file size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


def categorize_by_extension(path: Path):
    """Categorize files based on their extension."""
    ext = path.suffix.lower().lstrip('.')
    if not ext:
        return 'no_extension'

    categories = {
        'images': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'},
        'pdfs': {'pdf'},
        'documents': {'doc', 'docx', 'txt', 'rtf', 'odt'},
        'spreadsheets': {'xls', 'xlsx', 'csv', 'ods'},
        'presentations': {'ppt', 'pptx', 'odp'},
        'archives': {'zip', 'rar', '7z', 'tar', 'gz'},
        'videos': {'mp4', 'mkv', 'mov', 'avi'},
        'code': {'py', 'js', 'html', 'css', 'java', 'cpp', 'json'}
    }

    for category, extensions in categories.items():
        if ext in extensions:
            return category

    return ext  # fallback


# ==============================
# Routes
# ==============================
@app.route('/')
def index():
    """Display uploaded files."""
    files = []
    for f in UPLOAD_FOLDER.iterdir():
        if f.is_file():
            files.append({
                'name': f.name,
                'size': human_size(f.stat().st_size),
                'ext': f.suffix.lstrip('.') or '—'
            })
    return render_template('index.html', files=files)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    dest = UPLOAD_FOLDER / filename

    # Avoid overwriting by adding (1), (2), etc.
    counter = 1
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    while dest.exists():
        dest = UPLOAD_FOLDER / f"{stem}({counter}){suffix}"
        counter += 1

    file.save(dest)
    flash(f'File "{filename}" uploaded successfully!')
    return redirect(url_for('index'))


@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """Delete a specific uploaded file."""
    file_path = UPLOAD_FOLDER / filename
    if file_path.exists():
        file_path.unlink()
        flash(f'File "{filename}" deleted.')
    else:
        flash('File not found.')
    return redirect(url_for('index'))


@app.route('/download/<filename>')
def download(filename):
    """Download a file from uploads."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/organize', methods=['POST'])
def organize_files():
    """Organize all files into categorized folders."""
    moved_count = 0

    for file in UPLOAD_FOLDER.iterdir():
        if file.is_file():
            category = categorize_by_extension(file)
            category_dir = ORGANIZED_FOLDER / category
            category_dir.mkdir(parents=True, exist_ok=True)

            dest = category_dir / file.name
            counter = 1
            stem = file.stem
            suffix = file.suffix
            while dest.exists():
                dest = category_dir / f"{stem}({counter}){suffix}"
                counter += 1

            shutil.move(str(file), str(dest))
            moved_count += 1

    if moved_count:
        flash(f"Organized {moved_count} file(s) successfully!")
    else:
        flash("No files to organize.")

    return redirect(url_for('index'))


# ==============================
# Main Entry
# ==============================
if __name__ == '__main__':
    app.run(debug=True)
