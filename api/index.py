from flask import Flask, request, jsonify
import os
import uuid
from supabase import create_client
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Securely connect using environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize client only if keys exist to prevent boot errors
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    if not supabase:
        return jsonify({"error": "Database credentials missing"}), 500

    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            image_url = None
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_bytes = file.read()
                    
                    supabase.storage.from_("images").upload(
                        path=unique_filename, 
                        file=file_bytes, 
                        file_options={"content-type": file.content_type}
                    )
                    image_url = supabase.storage.from_("images").get_public_url(unique_filename)
            
            supabase.table("posts").insert({
                "title": title, 
                "content": content, 
                "image_url": image_url
            }).execute()

            return jsonify({"status": "success"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'GET':
        try:
            response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
            return jsonify(response.data), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# This is the line Vercel actually looks for
app = app
