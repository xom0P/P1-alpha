from flask import Flask, request, jsonify
import os
import uuid
from supabase import create_client
from werkzeug.utils import secure_filename

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# THE SECRET PASSWORD
ADMIN_PASS = "bsdk"

@app.route('/api/posts', methods=['GET', 'POST', 'PUT'])
def handle_posts():
    if not supabase:
        return jsonify({"error": "Database credentials missing"}), 500

    # SECURITY CHECK: Block unauthorized POST and PUT requests
    if request.method in ['POST', 'PUT']:
        provided_pass = request.headers.get('X-Admin-Password')
        if provided_pass != ADMIN_PASS:
            return jsonify({"error": "ACCESS DENIED: Unauthorized Hacker Detected."}), 403

    # CREATE NEW POST
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

    # UPDATE EXISTING POST
    if request.method == 'PUT':
        try:
            post_id = request.form.get('id')
            title = request.form.get('title')
            content = request.form.get('content')
            
            update_data = {
                "title": title,
                "content": content
            }

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
                    update_data["image_url"] = supabase.storage.from_("images").get_public_url(unique_filename)
            
            supabase.table("posts").update(update_data).eq("id", post_id).execute()

            return jsonify({"status": "updated"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # FETCH ALL POSTS (Publicly accessible so index.html works)
    if request.method == 'GET':
        try:
            response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
            return jsonify(response.data), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

app = app
