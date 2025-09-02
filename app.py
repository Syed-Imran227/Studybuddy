from flask import Flask, request, render_template, jsonify, session, redirect, url_for, flash
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import os
import ollama
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import uuid
import time
from werkzeug.utils import secure_filename
import threading
import queue
import math
import hashlib
import re
from pymongo import MongoClient
import bcrypt
from functools import wraps

# Try to import pytesseract, but don't fail if it's not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
except Exception:
    TESSERACT_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

UPLOAD_FOLDER = "uploads"
IMAGE_FOLDER = "static/images"
SUMMARY_FOLDER = "summaries"
ALLOWED_EXTENSIONS = {'pdf'}
MAX_WORKERS = min(8, os.cpu_count() or 4)  # Optimize worker count
BATCH_SIZE = 20  # Number of pages to process in one batch
MAX_IMAGES_PER_BATCH = 5  # Maximum images to extract per batch
CHUNK_SIZE = 12000  # Increased chunk size for faster processing
SUMMARY_CACHE_DIR = "cache/summaries"
MAX_CONCURRENT_LLM_CALLS = 2  # Limit concurrent LLM calls to reduce errors
USE_QUICK_EXTRACT = True  # Use quick text extraction for very large PDFs

# Create necessary directories
for folder in [UPLOAD_FOLDER, IMAGE_FOLDER, SUMMARY_FOLDER, SUMMARY_CACHE_DIR]:
    os.makedirs(folder, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["IMAGE_FOLDER"] = IMAGE_FOLDER
app.config["SUMMARY_FOLDER"] = SUMMARY_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Global progress tracking
processing_status = {}

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['pdf_chatbot']
users = db['users']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_processing_status(session_id, status):
    processing_status[session_id] = status

def get_processing_status(session_id):
    return processing_status.get(session_id, {})

def clean_old_files(folder, max_age_hours=24):
    """Clean up old files from the specified folder."""
    current_time = time.time()
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            if current_time - os.path.getmtime(filepath) > max_age_hours * 3600:
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error removing old file {filepath}: {e}")

def process_page_batch(args):
    """Process a batch of PDF pages."""
    doc, start_page, end_page, session_id = args
    batch_text = []
    batch_images = []
    images_in_batch = 0

    for page_num in range(start_page, min(end_page, doc.page_count)):
        try:
            page = doc[page_num]
            # Extract text
            text = page.get_text("text")
            batch_text.append(text)

            # Extract images (limited per batch)
            if images_in_batch < MAX_IMAGES_PER_BATCH:
                for img_index, img in enumerate(page.get_images(full=True)):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        img_bytes = base_image["image"]
                        
                        # Generate unique filename
                        image_filename = f"{session_id}_page_{page_num + 1}_img_{img_index + 1}.png"
                        image_path = os.path.join(IMAGE_FOLDER, image_filename)
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(img_bytes)
                        
                        batch_images.append(image_path)
                        images_in_batch += 1
                        
                        if images_in_batch >= MAX_IMAGES_PER_BATCH:
                            break
                    except Exception as e:
                        print(f"Error processing image {img_index} on page {page_num}: {e}")

        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue

    return "\n".join(batch_text), batch_images

def quick_extract_pdf(pdf_path, session_id):
    """Extract only text and a few images from very large PDFs for faster processing."""
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    all_text = []
    sample_images = []
    
    # Get text from pages with interval sampling for large PDFs
    sampling_interval = max(1, total_pages // 100)  # Sample at most 100 pages
    
    for page_num in range(0, total_pages, sampling_interval):
        try:
            page = doc[page_num]
            all_text.append(page.get_text("text"))
            
            # Extract a few images for context
            if len(sample_images) < 3:
                for img_index, img in enumerate(page.get_images(full=True)):
                    if len(sample_images) >= 3:
                        break
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        img_bytes = base_image["image"]
                        
                        image_filename = f"{session_id}_sample_img_{len(sample_images) + 1}.png"
                        image_path = os.path.join(IMAGE_FOLDER, image_filename)
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(img_bytes)
                        
                        sample_images.append(image_path)
                    except:
                        continue
        except:
            continue
    
    doc.close()
    return "\n".join(all_text), sample_images

def extract_key_content(text):
    """Extract key content from text to make summarization faster."""
    # Skip very short chunks
    if len(text) < 100:
        return text
        
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Extract key paragraphs (non-empty lines with reasonable length)
    paragraphs = [p for p in text.split('\n') if len(p.strip()) > 50]
    if not paragraphs:
        return text
        
    # Return filtered content
    return '\n\n'.join(paragraphs)

def get_cache_key(text):
    """Generate a cache key for the text."""
    # Use first 2K chars + last 2K chars to create a hash
    text_sample = text[:2000] + text[-2000:] if len(text) > 4000 else text
    return hashlib.md5(text_sample.encode()).hexdigest()

def get_cached_summary(cache_key):
    """Get cached summary if it exists."""
    cache_file = os.path.join(SUMMARY_CACHE_DIR, f"{cache_key}.txt")
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def save_to_cache(cache_key, summary):
    """Save summary to cache."""
    cache_file = os.path.join(SUMMARY_CACHE_DIR, f"{cache_key}.txt")
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(summary)

def summarize_chunk(args):
    """Summarize a single chunk of text."""
    chunk, chunk_index, total_chunks, images = args
    
    # Skip empty chunks
    if not chunk.strip():
        return chunk_index, "No content found in this section."
    
    # Extract key content for faster processing
    filtered_chunk = extract_key_content(chunk)
    
    # Generate cache key
    cache_key = get_cache_key(filtered_chunk)
    cached_summary = get_cached_summary(cache_key)
    
    if cached_summary:
        return chunk_index, cached_summary

    try:
        # Use a short/direct prompt for faster processing
        summary_prompt = f"TLDR; Summarize this text (Part {chunk_index + 1}/{total_chunks}). Be concise:\n\n{filtered_chunk}"
        
        summary_response = ollama.chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": summary_prompt,
                "images": images if chunk_index == 0 else []  # Only send images with first chunk
            }]
        )
        summary = summary_response["message"]["content"]
        
        # Cache the summary
        save_to_cache(cache_key, summary)
        return chunk_index, summary
    except Exception as e:
        print(f"Error summarizing chunk {chunk_index}: {e}")
        
        # Fallback to basic extraction if LLM fails
        lines = filtered_chunk.split('\n')
        top_lines = lines[:min(10, len(lines))]
        return chunk_index, f"Error with AI summary. Key content:\n{' '.join(top_lines)}"

def process_large_pdf(pdf_path, session_id):
    """Process a large PDF file in batches."""
    try:
        # Get document info first to determine strategy
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()  # Close to free memory
        
        # For very large PDFs, use quick extraction
        if total_pages > 200 and USE_QUICK_EXTRACT:
            update_processing_status(session_id, {
                'status': 'quick_extract',
                'progress': 0,
                'total_pages': total_pages
            })
            all_text, all_images = quick_extract_pdf(pdf_path, session_id)
        else:
            # Normal batch processing for smaller PDFs
            doc = fitz.open(pdf_path)
            batches = math.ceil(total_pages / BATCH_SIZE)
            all_text = []
            all_images = []
            
            update_processing_status(session_id, {
                'status': 'processing',
                'progress': 0,
                'total_batches': batches,
                'current_batch': 0
            })

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Process PDF in batches
                batch_jobs = []
                for batch in range(batches):
                    start_page = batch * BATCH_SIZE
                    end_page = min((batch + 1) * BATCH_SIZE, total_pages)
                    batch_jobs.append(executor.submit(process_page_batch, (doc, start_page, end_page, session_id)))

                # Collect results from batches
                for i, future in enumerate(as_completed(batch_jobs)):
                    try:
                        batch_text, batch_images = future.result()
                        all_text.append(batch_text)
                        all_images.extend(batch_images)
                        
                        # Update progress
                        update_processing_status(session_id, {
                            'status': 'processing',
                            'progress': ((i + 1) / batches) * 100,
                            'total_batches': batches,
                            'current_batch': i + 1
                        })
                    except Exception as e:
                        print(f"Error processing batch {i}: {e}")
                
                # Close the PDF
                doc.close()
                
                # Join all text
                all_text = "\n".join(all_text)
                
        # Process the extracted text in larger chunks
        update_processing_status(session_id, {
            'status': 'preparing_summary',
            'progress': 80
        })
        
        # Divide text into chunks
        text_chunks = []
        combined_text = all_text if isinstance(all_text, str) else "\n".join(all_text)
        
        # Skip summarization for very small texts
        if len(combined_text) < CHUNK_SIZE/2:
            if len(combined_text) < 100:
                final_summary = "The document appears to have very little text content to summarize."
            else:
                # For small documents, just use a single LLM call
                summary_prompt = f"Summarize this document concisely:\n\n{combined_text}"
                summary_response = ollama.chat(
                    model="llava",
                    messages=[{
                        "role": "user",
                        "content": summary_prompt,
                        "images": all_images[:3]
                    }]
                )
                final_summary = summary_response["message"]["content"]
                
            # Save the summary
            summary_path = os.path.join(SUMMARY_FOLDER, f"{session_id}_summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(final_summary)
                
            update_processing_status(session_id, {
                'status': 'completed',
                'progress': 100
            })
            
            # Convert image paths to URLs
            image_urls = [f"/{path}" for path in all_images]
            return final_summary, image_urls
            
        # For larger documents, use chunked processing    
        for i in range(0, len(combined_text), CHUNK_SIZE):
            text_chunks.append(combined_text[i:i + CHUNK_SIZE])
        
        total_chunks = len(text_chunks)
        
        # Process just a subset of chunks for very large documents (first, middle, last sections)
        if total_chunks > 6:
            sampled_chunks = []
            # First chunk
            sampled_chunks.append((0, text_chunks[0]))
            # Middle chunks (sample)
            mid_interval = max(1, total_chunks // 3)
            for i in range(mid_interval, total_chunks - mid_interval, mid_interval):
                sampled_chunks.append((i, text_chunks[i]))
            # Last chunk
            sampled_chunks.append((total_chunks-1, text_chunks[-1]))
            
            update_processing_status(session_id, {
                'status': 'summarizing',
                'progress': 0,
                'using_sampling': True,
                'total_chunks': len(sampled_chunks)
            })
            
            # Prepare arguments for summarization
            summarize_args = [
                (chunk, idx, len(sampled_chunks), all_images if i == 0 else []) 
                for i, (idx, chunk) in enumerate(sampled_chunks)
            ]
            
            # Collect summaries by index
            summaries = {}
            
        else:
            # Process all chunks for smaller documents
            update_processing_status(session_id, {
                'status': 'summarizing',
                'progress': 0, 
                'total_chunks': total_chunks
            })
            
            # Prepare arguments for summarization
            summarize_args = [
                (chunk, i, total_chunks, all_images) 
                for i, chunk in enumerate(text_chunks)
            ]
            
            # Pre-allocate list
            summaries = [""] * total_chunks

        # Process summaries with limited concurrency
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_LLM_CALLS) as executor:
            future_to_chunk = {
                executor.submit(summarize_chunk, args): args[1]  # args[1] is chunk_index
                for args in summarize_args
            }

            completed = 0
            for future in as_completed(future_to_chunk):
                try:
                    chunk_index, summary = future.result()
                    
                    if isinstance(summaries, dict):
                        summaries[chunk_index] = summary
                    else:
                        summaries[chunk_index] = summary
                        
                    completed += 1
                    
                    # Update progress
                    update_processing_status(session_id, {
                        'status': 'summarizing',
                        'progress': (completed / len(summarize_args)) * 100,
                        'current_chunk': completed,
                        'total_chunks': len(summarize_args)
                    })
                except Exception as e:
                    print(f"Error processing summary result: {e}")
        
        # Combine summaries with better formatting
        if isinstance(summaries, dict):
            summary_texts = []
            for i in sorted(summaries.keys()):
                if i == 0:
                    section = "Beginning"
                elif i == total_chunks - 1:
                    section = "End"
                else:
                    section = f"Middle (part {i+1}/{total_chunks})"
                summary_texts.append(f"{section}:\n{summaries[i]}")
            
            final_summary = "Document Summary (sampled sections):\n\n" + "\n\n".join(summary_texts)
        elif len(summaries) == 1:
            final_summary = summaries[0]
        else:
            final_summary = "Document Summary:\n\n" + "\n\n".join([
                f"Part {i+1}:\n{summary}" 
                for i, summary in enumerate(summaries)
                if summary  # Skip empty summaries
            ])

        # Save the summary
        summary_path = os.path.join(SUMMARY_FOLDER, f"{session_id}_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(final_summary)

        # Convert image paths to URLs
        image_urls = [f"/{path}" for path in all_images]

        update_processing_status(session_id, {
            'status': 'completed',
            'progress': 100
        })

        return final_summary, image_urls

    except Exception as e:
        update_processing_status(session_id, {
            'status': 'error',
            'error': str(e)
        })
        raise

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users.find_one({'username': username})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if users.find_one({'username': username}):
            return render_template('register.html', error='Username already exists')
        
        if users.find_one({'email': email}):
            return render_template('register.html', error='Email already exists')
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_id = users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        }).inserted_id
        
        session['user_id'] = str(user_id)
        session['username'] = username
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Update the index route to require login
@app.route('/')
@login_required
def index():
    # Clean up old files
    for folder in [UPLOAD_FOLDER, IMAGE_FOLDER, SUMMARY_FOLDER]:
        clean_old_files(folder)
    return render_template("index.html", username=session.get('username'))

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if "pdf_file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["pdf_file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{session_id}_{filename}")
        file.save(pdf_path)

        # Start processing in a separate thread
        def process_async():
            try:
                summary, image_urls = process_large_pdf(pdf_path, session_id)
                # Clean up the uploaded PDF
                try:
                    os.remove(pdf_path)
                except Exception as e:
                    print(f"Error removing temporary PDF: {e}")
            except Exception as e:
                update_processing_status(session_id, {
                    'status': 'error',
                    'error': str(e)
                })

        threading.Thread(target=process_async).start()

        return jsonify({
            "session_id": session_id,
            "message": "PDF processing started"
        })

    except Exception as e:
        return jsonify({"error": f"Error processing PDF: {str(e)}"}), 500

@app.route("/status/<session_id>")
def get_status(session_id):
    """Get the current processing status."""
    status = get_processing_status(session_id)
    return jsonify(status)

@app.route("/result/<session_id>")
def get_result(session_id):
    """Get the processing result."""
    status = get_processing_status(session_id)
    
    if status.get('status') != 'completed':
        return jsonify({"error": "Processing not completed"}), 400

    try:
        # Read the summary
        summary_path = os.path.join(SUMMARY_FOLDER, f"{session_id}_summary.txt")
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = f.read()

        # Get image URLs
        image_urls = []
        for filename in os.listdir(IMAGE_FOLDER):
            if filename.startswith(session_id):
                image_urls.append(f"/static/images/{filename}")

        return jsonify({
            "reply": summary,
            "images": image_urls,
            "ocr_available": TESSERACT_AVAILABLE
        })

    except Exception as e:
        return jsonify({"error": f"Error retrieving results: {str(e)}"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form.get("user_input")
    if not user_input:
        return jsonify({"reply": "Please enter a valid message."})
    
    try:
        response = ollama.chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": user_input
            }]
        )
        return jsonify({"reply": response["message"]["content"]})
    
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == "__main__":
    if not TESSERACT_AVAILABLE:
        print("Warning: Tesseract OCR is not available. OCR functionality will be disabled.")
    app.run(debug=True, threaded=True)
